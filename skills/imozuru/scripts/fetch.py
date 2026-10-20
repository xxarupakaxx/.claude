"""Restricted HTML/text adapter, derived from MaryCache/imozuru (see SOURCE.md)."""
import codecs
import re
import sys
import urllib.parse
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

MIN_TEXT_CHARS = 3000

MIN_HTML_CHARS = 1000

WALL_PATTERNS = (
    "404 not found",
    "page not found",
    "access denied",
    "you do not currently have access",
    "sign in to continue",
    "log in to continue",
    "enable javascript",
    "are you a robot",
    "captcha",
    # Anubis（ボット除けの計算をさせるページ）。HAL などが使う。中身の無い 1,000 字ほどのページが
    # HTML の下限を越えて OK になった（2026-10-20）
    "you're not a bot",
)

_CHARSET_ALIASES = {"shift_jis": "cp932", "shift-jis": "cp932", "sjis": "cp932", "x-sjis": "cp932",
                    "windows-31j": "cp932", "ms_kanji": "cp932"}

_DOCUMENT_CODECS = {codecs.lookup(n).name for n in (
    "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be",
    "ascii", "cp932", "shift_jis", "euc_jp", "euc_jis_2004", "iso2022_jp", "iso2022_jp_2",
    "gb2312", "gbk", "gb18030", "big5", "big5hkscs", "euc_kr", "cp949", "iso2022_kr",
    "latin-1", "iso8859_2", "iso8859_3", "iso8859_4", "iso8859_5", "iso8859_6", "iso8859_7",
    "iso8859_8", "iso8859_9", "iso8859_10", "iso8859_13", "iso8859_14", "iso8859_15", "iso8859_16",
    "cp1250", "cp1251", "cp1252", "cp1253", "cp1254", "cp1255", "cp1256", "cp1257", "cp1258",
    "koi8_r", "koi8_u", "mac_roman", "tis_620", "cp874")}

_BOMS = ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF32_LE, "utf-32"), (codecs.BOM_UTF32_BE, "utf-32"),
         (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16"))

def _declared_charsets(body: bytes, ctype: str) -> list[str]:
    """Content-Type と HTML の meta が名乗る文字コードを、この順に返す。"""
    found = re.findall(r"charset\s*=\s*[\"']?([\w.:-]+)", ctype or "", re.I)
    # meta はファイルの頭に置かれる決まり（HTML 仕様で先頭 1024 バイト以内）。余裕を見て 4096 まで見る
    found += re.findall(rb"<meta[^>]*charset\s*=\s*[\"']?([\w.:-]+)", body[:4096], re.I)
    names = [(n.decode("ascii", "ignore") if isinstance(n, bytes) else n).lower() for n in found]
    return [_CHARSET_ALIASES.get(n, n) for n in names]

def decode_text(body: bytes, ctype: str = "") -> str:
    """本文を、書かれている文字コードで文字にする。

    いつも UTF-8 で読んでいたため、Shift_JIS の日本語記事が U+FFFD の羅列になって中身が消えた
    （pju-hoge さんのフォークで見つかった・2026-10-15）。名乗りは嘘のこともあるので、
    BOM → UTF-8 → 名乗った文字コード → 日本語の定番の順に「化けずに読めるか」で試し、最初に通ったものを使う。
    どれも通らなければ、置換文字のいちばん少ないものを採る。

    UTF-8 を名乗りより先に試すのは、latin-1 のようにどんな並びでも読めてしまう名乗りがあるため。
    UTF-8 の文法に合う並びは、ほかの文字コードの文章からはまず偶然には生まれない。
    名乗りはページを書いた他人が決めるので、_DOCUMENT_CODECS に無いものは飛ばす
    （zlib_codec と名乗るだけで fetch.py が LookupError で止まった・2026-10-20 のレビュー）。
    """
    for bom, codec in _BOMS:
        if body.startswith(bom):
            try:
                return body.decode(codec)
            except UnicodeError:
                break
    candidates = []
    for name in ["utf-8", *_declared_charsets(body, ctype), "cp932", "euc_jp"]:
        try:
            info = codecs.lookup(name)
        except LookupError:  # 知らない名乗り（x-user-defined など）は飛ばす
            continue
        if info.name not in _DOCUMENT_CODECS:
            continue
        if info.name not in candidates:
            candidates.append(info.name)
    for codec in candidates:
        try:
            return body.decode(codec)
        except UnicodeError:
            continue
    decoded = []
    for codec in candidates:
        try:
            decoded.append(body.decode(codec, errors="replace"))
        except UnicodeError:  # idna など、置き換えでも読めない文字コードがある
            continue
    return min(decoded, key=lambda t: t.count("�"))

def md_text(value):
    return value.replace('\\', '\\\\').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('[', r'\[').replace(']', r'\]').replace('`', r'\`')


def md_href(value):
    if any(unicodedata.category(c) in {'Cc', 'Cf', 'Zl', 'Zp'} for c in value):
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {'http', 'https'} or not parsed.hostname:
        return None
    return urllib.parse.quote(value, safe="/:?#@!$&'*+,;=%~")


class _TextExtractor(HTMLParser):
    """ax が無い環境で、HTML から本文の文字を取り出す。

    ax ほど本文を見分けられない。<main> か <article> があって中身が十分なら、その中だけを使う。
    無いページではナビゲーションやフッターの文字も混ざるが、行番号で原文を指すには足りる。
    リンクは「後ろへ」たどる手がかりなので `[文字](URL)` で残す。
    """

    FOCUS = {"main", "article"}

    SKIP = {"script", "style", "noscript", "svg", "template", "iframe"}
    BLOCK = {"p", "div", "section", "article", "main", "header", "footer", "nav", "aside",
             "li", "tr", "br", "hr", "pre", "blockquote", "table", "ul", "ol", "dl", "dt", "dd",
             "figure", "figcaption"}
    HEADING = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "##### ", "h6": "###### "}

    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.parts: list[str] = []
        self.skip = 0
        self.href: str | None = None
        self.link_text: list[str] = []
        self.focus = 0
        self.focus_parts: list[str] = []

    def _emit(self, piece: str) -> None:
        self.parts.append(piece)
        if self.focus:
            self.focus_parts.append(piece)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif self.skip:
            return
        elif tag in self.FOCUS:
            self.focus += 1
        elif tag in self.HEADING:
            self._emit("\n\n" + self.HEADING[tag])
        elif tag in self.BLOCK:
            self._emit("\n")
        elif tag == "a":
            href = (dict(attrs).get("href") or "").strip()
            if href and not href.startswith("#"):
                full = urllib.parse.urljoin(self.base, href)
                # JavaScript: や data: のリンクは、.md を開いた先で押すとページの中で動く。http(s) だけ残す
                if md_href(full):
                    self.href = md_href(full)
                    self.link_text = []

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif self.skip:
            return
        elif tag in self.FOCUS:
            self.focus = max(0, self.focus - 1)
        elif tag in self.HEADING or tag in self.BLOCK:
            self._emit("\n")
        elif tag == "a" and self.href is not None:
            text = " ".join("".join(self.link_text).split())
            # 「\」を先に符号化する。後にすると、元からある「\]」が「\\]」になって「]」が効き直す
            text = md_text(text)
            self._emit(f"[{text}]({self.href})" if text else "")
            self.href = None

    def handle_data(self, data):
        if self.skip:
            return
        if self.href is not None:
            self.link_text.append(data)
        else:
            self._emit(md_text(data))

    def text(self) -> str:
        focused = "".join(self.focus_parts)
        # 中身の薄い <main>（ページの殻だけ）を掴んだときは全体に戻す
        raw = focused if len(focused.strip()) >= MIN_HTML_CHARS else "".join(self.parts)
        lines = (" ".join(line.split()) for line in raw.splitlines())
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"

def clean(s: str) -> str:
    """端末に出す文字列から、制御文字（色やクリップボードを操る ESC の並び）と改行の仲間を空白にする。

    他人が決めた文字列（本文・転送先の URL・HTTP のエラーの文）は、1行の出力の列や行を増やしたり、
    端末を操ったりできる（2026-10-20 の2回目のレビュー）。
    文字の向きを変える制御文字（U+202E など）と幅の無い空白も消す。ZWJ・ZWNJ は絵文字や一部の文字で要るので残す。
    """
    return re.sub(r"[\s\x00-\x1f\x7f-\x9f\u2028\u2029\u200b\u200e\u200f\u202a-\u202e\u2060-\u2069\ufeff]+", " ", s).strip()

def first_line(text: str) -> str:
    """本文の最初の意味のある1行。端末に出すので clean() を通す。"""
    for line in text.splitlines():
        line = clean(line)
        if len(line) > 8:
            return line[:100]
    return ""

def valid_source_name(name: str) -> bool:
    """保存する原文の名前は、パスではなく単一のファイル名に限る。

    Windows で使えない字（<>"|?*）は、そこで保存が OSError で止まるので先に断る。
    字の向きを変える制御文字（U+202E など）は、名前の見た目を偽れるので断る。
    """
    device = name.split(".", 1)[0].rstrip(" ").upper()
    return (bool(name.strip(" .")) and name == name.rstrip(" .")
            and not any(c in name for c in "/\\:<>\"|?*")
            and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in name)
            and not re.search(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]", name)
            and device not in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
            and not re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", device))

def main() -> int:
    if len(sys.argv) != 4:
        raise ValueError("fetch requires name and URL")
    sources, name, url = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    if not valid_source_name(name):
        raise ValueError("invalid source name")
    body, ctype, final = _broker_get(url)
    if body.startswith(b"%PDF-") or "pdf" in ctype.lower():
        raise ValueError("PDF/OCR and external tools are disabled in this installation")
    if not body.strip():
        raise ValueError("empty response")
    ctype = ctype.lower()
    if ctype.startswith(("text/plain", "text/markdown", "application/json", "text/csv")):
        text = md_text(decode_text(body, ctype))
    elif "html" in ctype or body.lstrip().startswith(b"<"):
        parser = _TextExtractor(final)
        parser.feed(decode_text(body, ctype))
        text = parser.text()
    else:
        raise ValueError("unsupported content type")
    wall = next((p for p in WALL_PATTERNS if p in text[:4000].lower()), None)
    if len(text) < MIN_HTML_CHARS or (wall and len(text) < MIN_TEXT_CHARS * 4):
        raise ValueError("source is too short or behind a login/bot wall")
    sources.mkdir(exist_ok=True)
    out = sources / (name + ".md")
    if out.exists():
        raise ValueError("source exists; choose a new name")
    _safe_write(out, text)
    print(f"OK\t{name}\t{out}\t{len(text)}\t{first_line(text)}")
    return 0

if __name__ == "__main__":
    raise SystemExit("Use scripts/run.py <topic> <command>; direct execution is disabled")
