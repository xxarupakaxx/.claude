"""地図の「場」を見張り、前回から新しく出たものを一覧にする（Ellis の monitoring）。

検索ではなく RSS / Atom を引く。検索は結果が揺れて費用もかかるが、フィードは
「その場所に新しく出たもの」をそのまま返す。決まった Qiita・Zenn・X を毎回検索する代わりに、
掘って見つけた場所を見張るための道具。

新着には要約をつけない。代わりにフィードに入っている原文の冒頭を1行そのまま載せる
（エージェントの言葉を挟まずに、選ぶ手がかりだけ出す）。

使い方:
    watch.py add   <topic_dir> <url> [名前]   … 見張る先を足す（RSS の場所は自動で探す）
    watch.py list  <topic_dir>               … 見張る先の一覧
    watch.py check <topic_dir> [--days N] [--fresh]
                                             … 新着を出して watch/<日付-時刻>.md に残す
                                               初回のフィードは直近 N 日（既定14）だけ
                                               --fresh は見た記録を無視して窓だけで選び直す
                                               新着の無い場所も、最新の1件を窓に関係なく出す

置き場（<topic_dir> = ~/.local/share/imozuru/topics/<話題>/）:
    watch.tsv          種類・名前・フィードの URL・元の URL（タブ区切り）
    watch-state.json   フィードごとに見たことのある記事の URL
    watch/<日付>.md     check の結果
"""

import codecs

import datetime as dt

import email.utils

import html

import json

import os


import re

import sys

import urllib.parse
import unicodedata

import xml.etree.ElementTree as ET

from pathlib import Path


from xml.parsers import expat

UA = {"User-Agent": "Mozilla/5.0 imozuru-watch"}

ATOM = "{http://www.w3.org/2005/Atom}"

HEAD_CHARS = 120

SEEN_LIMIT = 500

MAX_BYTES = 5_000_000


def fetch(url: str) -> tuple[bytes, str]:
    body, ctype, _ = fetch_final(url)
    return body, ctype

def known_feed(url: str) -> tuple[str, str] | None:
    """URL の形だけでフィードが分かる場所。種類とフィードの URL を返す。"""
    rules = [
        (r"^https?://qiita\.com/tags/([^/?#]+)", "qiita-tag", "https://qiita.com/tags/{0}/feed"),
        (r"^https?://zenn\.dev/topics/([^/?#]+)", "zenn-topic", "https://zenn.dev/topics/{0}/feed"),
        (r"^https?://zenn\.dev/([^/?#]+)/?$", "zenn-user", "https://zenn.dev/{0}/feed"),
        (r"^https?://note\.com/([^/?#]+)/?$", "note-user", "https://note.com/{0}/rss"),
        (r"^https?://qiita\.com/([^/?#]+)/?$", "qiita-user", "https://qiita.com/{0}/feed"),
        (r"^https?://(?:www\.|old\.)?reddit\.com/r/([^/?#]+)", "reddit", "https://www.reddit.com/r/{0}/.rss"),
    ]
    for pat, kind, tmpl in rules:
        m = re.match(pat, url)
        if m:
            return kind, tmpl.format(*m.groups())
    if re.match(r"^https?://export\.arxiv\.org/api/query", url):
        return "arxiv", url
    return None

def discover(url: str) -> tuple[str, str]:
    """ページの <link rel="alternate" type="application/rss+xml"> からフィードを探す。

    個人ブログ・はてな・WordPress・YouTube のチャンネルページはこれを持っている。
    URL そのものがフィードなら、それをそのまま使う。
    """
    hit = known_feed(url)
    if hit:
        return hit
    body, ctype, final = fetch_final(url)
    if "xml" in ctype or body.removeprefix(codecs.BOM_UTF8).lstrip()[:5] in (b"<?xml", b"<rss ", b"<feed"):
        return "feed", url
    text = body.decode("utf-8", errors="replace")
    # [^<>] にするのは、「<link」が並んで「>」の無いページで、1つずつ末尾まで読み直して遅くなるのを防ぐため
    for m in re.finditer(r"<link\b[^<>]*>", text, re.I):
        tag = m.group(0)
        if re.search(r'type=["\']application/(rss|atom)\+xml', tag, re.I):
            href = re.search(r'href=["\']([^"\']+)', tag)
            if href:
                # 「feed.xml」「//feeds.example/rss」のような相対の書き方も、転送の後のページを基準に解く
                feed = urllib.parse.urljoin(final, html.unescape(href.group(1)).strip())
                kind = "youtube" if "youtube.com/feeds" in feed else "site"
                return kind, feed
    raise SystemExit(f"RSS が見つからない: {url}（ページに RSS の案内が無い。X・pixiv はそもそも出していない）")

def plain(s: str | None) -> str:
    s = html.unescape(re.sub(r"<[^<>]*>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()

def md_text(s: str) -> str:
    r"""フィードの題や冒頭を markdown に書く形にする。

    題は他人が書く。「&amp;lt;img onerror=…&amp;gt;」のように二重に符号化しておくと、
    plain() の後で生のタグになり、.md を HTML として表示する道具で動いてしまう（2026-10-20 のレビュー）。
    「\」は先に符号化する。後にすると、元からある「\]」が「\\]」になって「]」が効き直す。
    改行と制御文字は空白にする（1行のはずの見出しや箇条を割らない）。
    """
    s = clean(s).replace("\\", "\\\\").replace("<", "&lt;").replace(">", "&gt;")
    return s.replace("[", r"\[").replace("]", r"\]")

def clean(s: str) -> str:
    """制御文字（端末を操る ESC の並び）と改行の仲間を空白にする。fetch.py の clean と同じ。"""
    return re.sub(r"[\s\x00-\x1f\x7f-\x9f\u2028\u2029\u200b\u200e\u200f\u202a-\u202e\u2060-\u2069\ufeff]+", " ", s).strip()

def md_link(url: str) -> str:
    """記事の URL を markdown のリンク先に書く形にする。http(s) 以外（javascript: など）と壊れた URL は空にする。"""
    if any(unicodedata.category(c) in {'Cc', 'Cf', 'Zl', 'Zp'} for c in url):
        return ""
    try:
        scheme = urllib.parse.urlsplit(url).scheme.lower()
    except ValueError:  # 「http://[」のような URL で、check 全体を止めない
        return ""
    if scheme not in {"http", "https"}:
        return ""
    return re.sub(r"[()\s<>]", lambda m: f"%{ord(m.group(0)):02X}", url)

def parse_date(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)  # RSS 2.0 の形
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))  # Atom の形
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)

class _Doctype(Exception):
    pass

def _refuse_doctype(*_):
    raise _Doctype

def reject_doctype(feed_bytes: bytes) -> None:
    """DOCTYPE か ENTITY の宣言があれば ValueError にする。宣言を見つけた時点で読むのを止める。

    前は根の要素より前を正規表現で探していたが、2つの道で素通りした（2026-10-20 のレビュー）。
    「<!-- <rss -->」のコメントを前に置くとそこを根と取り違え、UTF-16 で書くとバイトの並びが合わない。
    expat 自身に読ませて宣言の場所で止めれば、コメントも文字コードも expat が正しく扱う。
    ElementTree は中で使う expat の手綱を外に出さないので、同じ本体を先に expat だけで読む。
    """
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse_doctype
    parser.EntityDeclHandler = _refuse_doctype
    try:
        parser.Parse(feed_bytes, True)
    except _Doctype:
        raise ValueError("DOCTYPE か ENTITY を含むフィードは読まない") from None
    except expat.ExpatError:
        pass  # 壊れた XML は、このあとの ET.fromstring が同じく ParseError にする

def items(feed_bytes: bytes) -> list[dict]:
    """RSS 2.0 と Atom の記事を、題・URL・日付・冒頭の形にそろえる。

    フィードは他人のサーバーから来る。DOCTYPE や ENTITY を含む XML は、外部の実体の
    読み込みや入れ子の展開（billion laughs）に使われうるので、読まずに弾く。
    defusedxml を使うのが定石だが、標準ライブラリだけで動かす決まりなので入れない。
    ふつうの RSS / Atom は DOCTYPE を使わないので、弾いて困ることはまず無い。
    """
    reject_doctype(feed_bytes)
    root = ET.fromstring(feed_bytes)
    out = []
    for it in root.iter("item"):
        out.append({
            "title": plain(it.findtext("title")),
            "link": (it.findtext("link") or "").strip(),
            "date": parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")),
            "head": plain(it.findtext("description")),
        })
    for en in root.iter(f"{ATOM}entry"):
        link = ""
        for ln in en.findall(f"{ATOM}link"):
            if ln.get("rel", "alternate") == "alternate":
                link = ln.get("href", "")
                break
        head = en.findtext(f"{ATOM}summary") or en.findtext(f"{ATOM}content") \
            or en.findtext("{http://search.yahoo.com/mrss/}group/{http://search.yahoo.com/mrss/}description")
        out.append({
            "title": plain(en.findtext(f"{ATOM}title")),
            "link": link,
            "date": parse_date(en.findtext(f"{ATOM}published") or en.findtext(f"{ATOM}updated")),
            "head": plain(head),
        })
    return out

def load_watch(topic: Path) -> list[list[str]]:
    """watch.tsv の行を返す。列が足りない行は、手で書き損じたものとして飛ばす。"""
    p = topic / "watch.tsv"
    if not p.exists():
        return []
    # splitlines() は U+2028 なども行の区切りにするので、書くときと同じ \n だけで分ける
    rows = [ln.rstrip("\r").split("\t") for ln in p.read_text(encoding="utf-8").split("\n")
            if ln and not ln.startswith("#")]
    return [r for r in rows if len(r) >= 3]

def atomic_write(path: Path, text: str) -> None:
    """一時ファイルに書いてから置き換える。途中で止まっても前のファイルが壊れずに残る。"""
    _safe_write(path, text)

def cmd_add(topic: Path, url: str, name: str | None) -> int:
    # 1つ足せなくても、続けて他を足せるように例外で落とさず1行で返す
    # （Reddit が 429 を返してトレースバックで止まった・2026-10-10 の試し）。
    try:
        kind, feed = discover(url)
        found = items(fetch(feed)[0])  # 引けないフィードは足さない
    except SystemExit as e:
        print(f"足せなかった: {clean(str(e))}")
        return 1
    except Exception as e:
        print(f"足せなかった: {clean(url)}（{type(e).__name__}: {clean(str(e))}）")
        return 1
    for row in load_watch(topic):
        if row[2] == feed:
            print(f"もう見張っている: {row[1]} {feed}")
            return 0
    if name:
        label = name
    elif kind == "arxiv":
        q = re.search(r"search_query=([^&]+)", url)
        label = "arxiv " + (urllib.parse.unquote(q.group(1)) if q else "query")
    elif kind == "feed" and found:
        label = found[0]["title"][:30]
    else:
        # 末尾だけだと「blog」「releases」ばかりになって見分けられないので、ドメインと道筋で名づける
        label = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")[:40]
    # フィードの URL はページを書いた他人が決める。&#9; や &#10; で列や行を足されないよう、制御文字を断る
    if any(clean(s) != s for s in (feed, url)):
        print(f"足せなかった: {clean(url)}（URL に空白・タブ・改行・制御文字が入っている）")
        return 1
    label = clean(label)
    topic.mkdir(parents=True, exist_ok=True)
    p = topic / "watch.tsv"
    previous = p.read_text(encoding="utf-8") if p.exists() else "# 種類\t名前\tフィード\t元の URL\n"
    atomic_write(p, previous + f"{kind}\t{label}\t{feed}\t{url}\n")
    print(f"足した: {kind}\t{label}\t{feed}（いま {len(found)} 件）")
    return 0

def cmd_check(topic: Path, days: int, fresh: bool) -> None:
    """新着を出す。fresh なら見たことの記録を無視して、窓（days）だけで選び直す。

    初回の窓の外の記事も「見た」と記録されるので、窓を広げて出し直したいときに
    記録が邪魔をする（14日で出したあと 30日で見直せなかった・2026-10-10 の試し）。
    """
    rows = load_watch(topic)
    if not rows:
        raise SystemExit(f"見張る先が無い: {topic}/watch.tsv（watch.py add で足す）")
    state_p = topic / "watch-state.json"
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=days)
    lines = [f"# 新着 {now.astimezone():%Y-%m-%d %H:%M}", ""]
    quiet: list[str] = []
    total = 0
    for kind, label, feed, *_ in rows:
        try:
            got = items(fetch(feed)[0])
        except Exception as e:  # 1つのフィードが落ちても他は見る
            lines += [f"## {md_text(label)}（{kind}）", f"- 取れなかった: {type(e).__name__}: {md_text(str(e))}", ""]
            continue
        seen = set() if fresh else set(state.get(feed, []))
        # 前回が空のフィード（記事0件）も初回と同じく窓で絞る。空の記録で全部を新着と取り違えない
        first = fresh or not state.get(feed)
        new = [i for i in got if i["link"] and i["link"] not in seen
               and (not first or (i["date"] and i["date"] >= cutoff))]
        new.sort(key=lambda i: i["date"] or now, reverse=True)
        state[feed] = ([i["link"] for i in got] + list(set(state.get(feed, [])) - {i["link"] for i in got}))[:SEEN_LIMIT]
        if not new:
            # 新着が無くても、窓に関係なくそのフィードの最新を1行出す。公式の最新が
            # 窓の外に落ちて見えなくなるのを防ぐ（React 19.3 が 31日前で漏れた）。
            dated = [i for i in got if i["date"]]
            if dated:
                last = max(dated, key=lambda i: i["date"])
                quiet.append(f"- {md_text(label)}（{kind}）最新 {last['date'].astimezone():%Y-%m-%d} "
                             f"[{md_text(last['title'])}]({md_link(last['link'])})")
            else:
                quiet.append(f"- {md_text(label)}（{kind}）記事なし")
            continue
        total += len(new)
        lines.append(f"## {md_text(label)}（{kind}）{'・直近' + str(days) + '日' if first else ''}")
        for i in new:
            day = i["date"].astimezone().strftime("%Y-%m-%d") if i["date"] else "日付なし"
            lines.append(f"- {day} [{md_text(i['title'])}]({md_link(i['link'])})")
            if i["head"]:
                lines.append(f"  > {md_text(i['head'][:HEAD_CHARS])}{'…' if len(i['head']) > HEAD_CHARS else ''}")
        lines.append("")
    if total == 0:
        lines += ["新着なし", ""]
    if quiet:
        lines += ["## 新着の無かった場所（窓に関係なく最新の1件）", *quiet, ""]
    # 秒まで入れる。日付だけだと同じ日の2回目が1回目を上書きして消した（2026-10-10 の試し）。
    out = topic / "watch" / f"{now.astimezone():%Y-%m-%d-%H%M%S}.md"
    n = 2
    while out.exists():  # 同じ秒にもう一度回したときも、前の結果を消さない
        out = out.with_name(f"{now.astimezone():%Y-%m-%d-%H%M%S}-{n}.md")
        n += 1
    out.parent.mkdir(exist_ok=True)
    # 結果を書けてから「見た」の記録を進める。逆だと、書けなかった新着が次から出なくなる
    atomic_write(out, "\n".join(lines) + "\n")
    atomic_write(state_p, json.dumps(state, ensure_ascii=False, indent=1))
    print("\n".join(lines))
    print(f"\n→ {out}（新着 {total} 件・見張る先 {len(rows)}）")

def main() -> int:
    args = sys.argv[1:]
    days = 14
    fresh = "--fresh" in args
    if fresh:
        args.remove("--fresh")
    if "--days" in args:
        i = args.index("--days")
        value = args[i + 1] if i + 1 < len(args) else ""
        # isdigit() は「²」も数字と見なして int() で落ちるので、ASCII の数字だけを通す
        if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
            print("--days には 1 以上の日数を書く", file=sys.stderr)
            return 2
        days = int(value)
        del args[i:i + 2]
    if len(args) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, topic = args[0], Path(args[1]).expanduser()
    if cmd == "add" and len(args) >= 3:
        return cmd_add(topic, args[2], args[3] if len(args) > 3 else None)
    elif cmd == "list":
        for row in load_watch(topic):
            print("\t".join(row))
    elif cmd == "check":
        cmd_check(topic, days, fresh)
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0

def fetch_final(url: str) -> tuple[bytes, str, str]:
    return _broker_get(url)

if __name__ == "__main__":
    raise SystemExit("Use scripts/run.py <topic> <command>; direct execution is disabled")
