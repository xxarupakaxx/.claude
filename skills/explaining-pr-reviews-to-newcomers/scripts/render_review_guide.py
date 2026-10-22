#!/usr/bin/env python3
"""PR レビュー解説 HTML を、git から機械的に切り出した抜き書き付きで生成・照合する。

render: spec.json（抜き書きの定義）と body.html（本文。[[q-id]] と [[TAG:種類]] を含む）から HTML を作る。
        CSS は creating-html-documents のテンプレートの CSS に、このSkillの部品の CSS を足したもの。
verify: 生成済み HTML の各抜き書きについて、見出しのパス・行範囲・短い SHA、GitHub のリンク、
        行番号の連続、各行の内容が、記録された commit と path の git の内容と一致するかを確かめる。
text:   本文の見える文章（抜き書き・コードブロック・図・目次を除き、文中のコードは残す）をテキストに書き出す。日本語の lint に使う。

使い方:
  python3 -I render_review_guide.py render --spec spec.json --body body.html --out review-guide.html
  python3 -I render_review_guide.py verify --repo /path/to/repo review-guide.html
  python3 -I render_review_guide.py text review-guide.html --out "$TMPDIR/review-guide.md"
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote as url_quote

SKILL_DIR = Path(__file__).resolve().parent.parent
CSS_PATH = SKILL_DIR / "assets" / "review-guide.css"
TEMPLATE_PATH = SKILL_DIR.parent / "creating-html-documents" / "assets" / "editorial-document.html"
CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"
TAGS = {"fact": "確認済み", "cited": "出典の記載", "guess": "推測", "open": "未確認"}
QUOTE_ID = re.compile(r"q-[a-z0-9-]+")
QUOTE_TOKEN = re.compile(r"\[\[(q-[a-z0-9-]+)\]\]")
TAG_TOKEN = re.compile(r"\[\[TAG:([a-z]+)\]\]")
ANY_TOKEN = re.compile(r"\[\[[^\]\n]*\]\]")
MARKS = {"抜き書き", "注目"}
FORBIDDEN_BODY = re.compile(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]|<style[\s>]|<script[\s>]", re.I)
QUOTE_START = re.compile(r'<div\b[^>]*\bclass="[^"]*\bquote\b[^"]*"[^>]*>')
SHA = re.compile(r"[0-9a-f]{40}")
LINE_SPAN = re.compile(r'<span class="ln[^"]*"><span class="no">(\d+)</span>(.*?)</span>(?=<span class="ln|</code>)', re.S)


class SpecError(Exception):
    pass


def git(repo: str, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if proc.returncode != 0:
        raise SpecError(f"git {' '.join(args)} に失敗: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git_lines(repo: str, rev: str, path: str, cache: dict) -> list[str]:
    key = (rev, path)
    if key not in cache:
        try:
            text = git(repo, "show", f"{rev}:{path}").decode("utf-8")
        except UnicodeDecodeError as e:
            raise SpecError(f"{path} は UTF-8 として読めない: {e}") from e
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()  # 末尾の改行は行を増やさない
        cache[key] = [line[:-1] if line.endswith("\r") else line for line in lines]
    return cache[key]


def display(line: str) -> str:
    return line.replace("\t", "    ")


def require(obj: object, keys: tuple[str, ...], where: str) -> None:
    if not isinstance(obj, dict):
        raise SpecError(f"{where} はオブジェクトで書く")
    missing = [k for k in keys if k not in obj]
    if missing:
        raise SpecError(f"{where} に必須の項目が無い: {missing}")


def check_types(q: dict) -> None:
    where = f"quote {q.get('id')!r}"
    for key in ("id", "rev", "path", "find", "title"):
        if key in q and not isinstance(q[key], str):
            raise SpecError(f"{where}: {key} は文字列で書く")
    for key in ("start", "end", "ctx", "before", "after"):
        if key in q and (not isinstance(q[key], int) or isinstance(q[key], bool) or q[key] < 0):
            raise SpecError(f"{where}: {key} は0以上の整数で書く")
    if "focus" in q and not (isinstance(q["focus"], list) and all(isinstance(f, int) and not isinstance(f, bool) for f in q["focus"])):
        raise SpecError(f"{where}: focus は整数の配列で書く")
    if "find" in q and ("start" in q or "end" in q):
        raise SpecError(f"{where}: find と start・end は同時に書かない")


def resolve_range(q: dict, lines: list[str]) -> tuple[int, int]:
    if "find" in q:
        hits = [i + 1 for i, text in enumerate(lines) if q["find"] in text]
        if len(hits) != 1:
            raise SpecError(f"{q['id']}: find {q['find']!r} が {len(hits)} 件（1件に絞る）")
        start, end = hits[0] - int(q.get("before", 0)), hits[0] + int(q.get("after", 0))
    elif "start" in q and "end" in q:
        start, end = int(q["start"]), int(q["end"])
    else:
        raise SpecError(f"{q['id']}: start と end、または find を指定する")
    if not (1 <= start <= end <= len(lines)):
        raise SpecError(f"{q['id']}: 行範囲 {start}-{end} がファイル（{len(lines)}行）の外")
    return start, end


def code_block(lines: list[str], a: int, b: int, hl: tuple[int, int] | None = None, focus: tuple[int, ...] = ()) -> str:
    rows = []
    for i in range(a, b + 1):
        mark = ""
        if hl:
            cls = "ln hl" if hl[0] <= i <= hl[1] else "ln"
            if i == hl[0]:
                mark = '<span class="mk">抜き書き</span>'
        else:
            cls = "ln fx" if i in focus else "ln"
            if i in focus and (i - 1) not in focus:
                mark = '<span class="mk">注目</span>'
        text = html.escape(display(lines[i - 1])).replace("[", "&#91;") or " "
        rows.append(f'<span class="{cls}"><span class="no">{i}</span>{text}{mark}</span>')
    return '<pre class="src"><code>' + "".join(rows) + "</code></pre>"


def render_quote(q: dict, spec: dict, shas: dict, cache: dict) -> str:
    sha = shas[q["rev"]]
    lines = git_lines(spec["repo"], sha, q["path"], cache)
    a, b = resolve_range(q, lines)
    focus = tuple(int(f) for f in q.get("focus", []))
    if any(not (a <= f <= b) for f in focus):
        raise SpecError(f"{q['id']}: focus が抜き書きの範囲外")
    ctx = int(q.get("ctx", 8))
    ca, cb = max(1, a - ctx), min(len(lines), b + ctx)
    rng = f"{a}" if a == b else f"{a}〜{b}"
    note = "・黄色は注目行" if focus else ""
    link = ""
    if spec.get("github"):
        plain = "?plain=1" if q["path"].lower().endswith((".md", ".markdown")) else ""
        url = f"https://github.com/{spec['github']}/blob/{sha}/{url_quote(q['path'])}{plain}#L{a}-L{b}"
        link = f'<a href="{html.escape(url)}" rel="noopener noreferrer">GitHubで開く</a>'
    return (
        f'<div class="quote wide" id="{q["id"]}" data-rev="{sha}" data-path="{html.escape(q["path"])}">'
        f'<p class="qhead"><span class="qid">{q["id"]}</span><span class="qtitle">{html.escape(q.get("title", ""))}</span>'
        f'<code class="path">{html.escape(q["path"])}</code><span class="rev">{rng}行・{html.escape(q["rev"])} {sha[:7]}{note}</span>{link}</p>'
        f"{code_block(lines, a, b, focus=focus)}"
        f'<details class="ctx"><summary>前後を読む（{ca}〜{cb}行。抜き書きの行は黄色）</summary>'
        f"{code_block(lines, ca, cb, (a, b))}</details></div>"
    )


def load_css() -> str:
    if not TEMPLATE_PATH.is_file():
        raise SpecError(f"creating-html-documents のテンプレートが見つからない: {TEMPLATE_PATH}")
    m = re.search(r"<style>(.*?)</style>", TEMPLATE_PATH.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SpecError("テンプレートに <style> が無い")
    return m.group(1).strip() + "\n" + CSS_PATH.read_text(encoding="utf-8")


def check_document(doc: str) -> None:
    ids = re.findall(r'\sid="([^"]+)"', doc)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    broken = sorted({h for h in re.findall(r'href="#([^"]+)"', doc) if h not in set(ids)})
    if dup or broken:
        raise SpecError(f"id重複={dup} リンク切れ={broken}")


def render(spec_path: Path, body_path: Path, out_path: Path) -> None:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        body = body_path.read_text(encoding="utf-8").strip("\n")
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SpecError(f"spec または body を読めない: {e}") from e
    require(spec, ("repo", "title", "reader", "revs", "quotes"), "spec")
    if not isinstance(spec["title"], str) or not isinstance(spec["reader"], str):
        raise SpecError("spec の title と reader は文字列で書く")
    if not isinstance(spec["revs"], dict) or not spec["revs"]:
        raise SpecError("spec の revs は {名前: 40桁の SHA} のオブジェクトで書く")
    bad_revs = {k: v for k, v in spec["revs"].items() if not (isinstance(v, str) and SHA.fullmatch(v))}
    if bad_revs:
        raise SpecError(f"revs は40桁の SHA で固定する（ref 名は再生成のたびに版が変わる）: {bad_revs}")
    if not isinstance(spec["quotes"], list):
        raise SpecError("spec の quotes は配列で書く")
    if FORBIDDEN_BODY.search(body):
        raise SpecError("body.html には <div class=\"page\"> の中身だけを書く。doctype・html・head・body・style・script は書かない（文書の枠と CSS は render が付ける）")
    quotes: dict[str, dict] = {}
    for q in spec["quotes"]:
        require(q, ("id", "rev", "path"), f"quote {q.get('id', '?') if isinstance(q, dict) else q!r}")
        check_types(q)
        if not QUOTE_ID.fullmatch(q["id"]):
            raise SpecError(f"抜き書きの id は q- で始まる英小文字・数字・ハイフンにする: {q['id']!r}")
        if q["id"] in quotes:
            raise SpecError(f"spec の quotes に同じ id がある: {q['id']}")
        if q["rev"] not in spec["revs"]:
            raise SpecError(f"{q['id']}: rev {q['rev']!r} が revs に無い")
        quotes[q["id"]] = q
    # トークンの検査と根拠ラベルの置換は、抜き書きを入れる前の本文に対して行う（コード中の [[ ]] と混ざらないようにする）
    used = QUOTE_TOKEN.findall(body)
    dup = sorted({u for u in used if used.count(u) > 1})
    missing = sorted(set(used) - set(quotes))
    unused = sorted(set(quotes) - set(used))
    bad_tags = sorted(set(TAG_TOKEN.findall(body)) - set(TAGS))
    if dup or missing or unused or bad_tags:
        raise SpecError(f"トークン: 抜き書きの重複={dup} spec に無い={missing} 本文で未使用={unused} 未知の根拠ラベル={bad_tags}")
    body = TAG_TOKEN.sub(lambda m: f'<span class="tag {m.group(1)}">{TAGS[m.group(1)]}</span>', body)
    leftover = [t for t in ANY_TOKEN.findall(body) if not QUOTE_TOKEN.fullmatch(t)]
    if leftover:
        raise SpecError(f"解釈できないトークン: {leftover[:5]}")
    for rev in spec["revs"].values():
        git(spec["repo"], "cat-file", "-e", f"{rev}^{{commit}}")
    shas = dict(spec["revs"])
    cache: dict = {}
    body = QUOTE_TOKEN.sub(lambda m: render_quote(quotes[m.group(1)], spec, shas, cache), body)
    doc = (
        '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
        '<meta name="artifact-kind" content="html-document">\n'
        f'<meta name="reader" content="{html.escape(spec["reader"])}">\n'
        f"<title>{html.escape(spec['title'])}</title>\n"
        f"<style>\n{load_css()}</style>\n</head>\n<body>\n"
        f'<div class="page">\n{body}\n</div>\n</body>\n</html>\n'
    )
    check_document(doc)
    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path}（抜き書き {len(quotes)} 本）")


def code_rows(pre: str) -> list[tuple[int, str]]:
    rows = []
    for no, inner in LINE_SPAN.findall(pre):
        mark = re.search(r'<span class="mk">([^<]*)</span>$', inner)
        if mark:
            if mark.group(1) not in MARKS:
                raise SpecError(f"{no}行目の印 {mark.group(1)!r} は認めていない")
            inner = inner[: mark.start()]
        if re.search(r"<[a-z]", inner):
            raise SpecError(f"{no}行目の抜き書きに想定外のタグがある")
        rows.append((int(no), html.unescape(inner)))
    return rows


def check_block(qid: str, block: str, sha: str, path: str, lines: list[str]) -> str | None:
    shown = re.search(r'<code class="path">([^<]*)</code>', block)
    if not shown or html.unescape(shown.group(1)) != path:
        return f"{qid}: 見出しのパスが data-path と一致しない"
    head = re.search(r'<span class="rev">(\d+)(?:〜(\d+))?行・[^<]* ([0-9a-f]{7})', block)
    if not head or head.group(3) != sha[:7]:
        return f"{qid}: 見出しの行範囲か短い SHA が data-rev と一致しない"
    for href in re.findall(r'href="(https://github\.com/[^"]+)"', block):
        if f"/blob/{sha}/{url_quote(path)}" not in html.unescape(href):
            return f"{qid}: GitHub のリンクが data-rev・data-path と一致しない"
    pres = re.findall(r'<pre class="src"><code>.*?</code></pre>', block, re.S)
    if len(pres) != 2:
        return f"{qid}: 抜き書きと前後を読むの2つのコードが見つからない"
    a, b = int(head.group(1)), int(head.group(2) or head.group(1))
    main_rows, ctx_rows = code_rows(pres[0]), code_rows(pres[1])
    if [n for n, _ in main_rows] != list(range(a, b + 1)):
        return f"{qid}: 抜き書きの行番号が見出しの {a}〜{b} 行と一致しない"
    ctx_nos = [n for n, _ in ctx_rows]
    if not ctx_nos or ctx_nos != list(range(ctx_nos[0], ctx_nos[-1] + 1)) or ctx_nos[0] > a or ctx_nos[-1] < b:
        return f"{qid}: 前後を読むの行番号が連続していないか、抜き書きを含まない"
    for no, text in main_rows + ctx_rows:
        # 空行は表示用に半角スペース1つで出力しているので、同じ規則で比べる
        if no > len(lines) or (display(lines[no - 1]) or " ") != text:
            return f"{qid}: {no}行目が git の内容と一致しない"
    return None


def quote_blocks(doc: str) -> list[tuple[str, str, str, str]]:
    """抜き書きの枠ごとに (id, data-rev, data-path, 枠の中身) を返す。属性の順には頼らない。"""
    blocks = []
    for m in QUOTE_START.finditer(doc):
        attrs = dict(re.findall(r'([a-z-]+)="([^"]*)"', m.group(0)))
        end = doc.find("</details></div>", m.end())
        body = doc[m.end(): end] if end != -1 else ""
        blocks.append((attrs.get("id", "?"), attrs.get("data-rev", ""), html.unescape(attrs.get("data-path", "")), body))
    return blocks


def verify(html_path: Path, repo: str) -> int:
    doc = html_path.read_text(encoding="utf-8")
    cache: dict = {}
    blocks = quote_blocks(doc)
    failures = []
    if not blocks:
        failures.append("抜き書きが1本も見つからない")
    for qid, sha, path, block in blocks:
        if not SHA.fullmatch(sha) or not path or not block:
            failures.append(f"{qid}: data-rev・data-path か、枠の終わりが見つからない")
            continue
        try:
            problem = check_block(qid, block, sha, path, git_lines(repo, sha, path, cache))
        except SpecError as e:
            problem = f"{qid}: {e}"
        if problem:
            failures.append(problem)
    for f in failures:
        print(f"NG {f}", file=sys.stderr)
    print(f"verify: 抜き書き {len(blocks)} 本、不一致 {len(failures)} 件")
    return 1 if failures else 0


def visible_text(html_path: Path) -> str:
    doc = html_path.read_text(encoding="utf-8")
    body = re.search(r"<body>(.*)</body>", doc, re.S).group(1)
    for _, _, _, block in quote_blocks(body):
        body = body.replace(block, "")
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"<(pre|svg|style|nav)\b.*?</\1>", "", body, flags=re.S)
    body = re.sub(r"</a>\s*<a\b", "</a>\n<a", body)
    body = re.sub(r"</(p|li|h[1-6]|dt|dd|summary|figcaption|div|section|article)>", "\n", body)
    text = html.unescape(re.sub(r"<[^>]+>", "", body))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--spec", type=Path, required=True)
    r.add_argument("--body", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--repo", required=True)
    v.add_argument("html", type=Path)
    t = sub.add_parser("text")
    t.add_argument("html", type=Path)
    t.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "render":
            render(args.spec, args.body, args.out)
            return 0
        if args.cmd == "text":
            args.out.write_text(visible_text(args.html), encoding="utf-8")
            print(f"wrote {args.out}")
            return 0
        return verify(args.html, args.repo)
    except (SpecError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
