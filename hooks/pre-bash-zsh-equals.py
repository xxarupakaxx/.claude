#!/usr/bin/env python3
"""PreToolUse(Bash): zsh の = 展開で失敗する `echo =====` を、実行の前に止める。

zsh は引用符のない `=word` をコマンド名の展開として扱う。`echo =====` は
「==== not found」で失敗し、同じ行の残りのコマンドも実行されない。

対象は echo / printf / print の引数だけにしている。shell の文法を完全には
追わないので、範囲を広げると正しいコマンドを止める危険が先に立つ。
二重引用符の中のコマンド置換に引用符が入れ子になっている場合は、引用符の
対応を追えないので判定しない。
止めるときは終了コード 2、それ以外（判定できない場合を含む）は 0 で終わる。
"""
import json
import os
import re
import sys

HEREDOC_START = re.compile(r"(?<!<)<<(?!<)[-~]?\s*(['\"\\]?)(\w+)\1?")
QUOTED = re.compile(r"""\\\n|\$'(?:\\.|[^'\\])*'|'[^']*'|"(?:\\.|[^"\\])*"|\\.""", re.S)
COMMENT = re.compile(r"(?m)(^|\s)#.*$")
ARITHMETIC = re.compile(r"\$\(\([^()]*\)\)|\$\[[^\[\]]*\]")  # $((…)) と $[…]。中の == は比較である
SUBSTITUTION = re.compile(r"\$\{[^{}]*\}|\$\([^()]*\)")  # 最も内側の ${…} と $(…)
QUOTE_MARK, VALUE_MARK = "\x00", "\x01"  # 引用符の中身と、置換の結果の代わりに置く印
SEPARATORS = re.compile(r"[;&|\n(){}]+")
LEADING = re.compile(r"^(?:then|do|else|elif|if|while|until|time|!|\w+=\S*)$")
TARGETS = {"echo", "printf", "print"}
MESSAGE = (
    "[Hook] BLOCKED: zsh は引用符のない「{word}」をコマンド名の展開（=cmd）として扱い、"
    "「not found」で失敗する。同じ行の残りも実行されない。"
    "区切りは echo '{word}' のように引用符で囲んで、もう一度実行する。\n"
)


def strip_heredocs(command):
    kept, lines, index = [], command.split("\n"), 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        for start in HEREDOC_START.finditer(line):
            while index < len(lines) and lines[index].strip() != start.group(2):
                index += 1
            index += 1
    return "\n".join(kept)


def nests_quotes(quoted):
    """"$(cmd "x")" や "${x:-"y"}" のように、置換の途中で二重引用符が閉じて見える場合。"""
    if not quoted.startswith('"'):
        return False
    while ARITHMETIC.search(quoted) or SUBSTITUTION.search(quoted):
        quoted = SUBSTITUTION.sub("", ARITHMETIC.sub("", quoted))
    return "$(" in quoted or "${" in quoted or quoted.count("`") % 2 == 1


def equals_argument(text):
    for segment in SEPARATORS.split(text):
        words = segment.split()
        while words and LEADING.match(words[0]):
            words.pop(0)
        if not words or words[0] not in TARGETS:
            continue
        for word in words[1:]:
            if word.startswith("=="):
                return word.replace(QUOTE_MARK, "").replace(VALUE_MARK, "")
    return None


def offending_word(command):
    text = strip_heredocs(command)
    if any(nests_quotes(quoted.group()) for quoted in QUOTED.finditer(text)):
        return None
    text = QUOTED.sub(lambda quoted: " " if quoted.group() == "\\\n" else QUOTE_MARK, text)
    text = ARITHMETIC.sub(VALUE_MARK, COMMENT.sub(r"\1", text))
    # 置換の中のコマンドと、置換を1語に畳んだ外側のコマンドの両方を見る。
    collapsed = text
    while SUBSTITUTION.search(collapsed):
        collapsed = SUBSTITUTION.sub(VALUE_MARK, collapsed)
    return equals_argument(text) or equals_argument(collapsed)


def main():
    if os.path.basename(os.environ.get("SHELL", "")) != "zsh":
        return 0
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
    except (ValueError, KeyError, TypeError):
        return 0
    word = offending_word(command) if isinstance(command, str) else None
    if not word:
        return 0
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.write(MESSAGE.format(word=word))
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception as error:  # フックの不具合で Bash を止めない
        sys.stderr.write("[Hook] pre-bash-zsh-equals: not checked (%s)\n" % type(error).__name__)
        code = 0
    sys.exit(code)
