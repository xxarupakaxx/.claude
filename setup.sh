#!/bin/bash
# Claude Code 設定セットアップスクリプト
# 使用方法:
#   新規端末: git clone <repo> ~/.claude && ~/.claude/setup.sh
#   既存端末: cd ~/.claude && git pull && ./setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "=== Claude Code Setup ==="

# 1. スクリプトが~/.claudeから実行されているか確認
if [ "$SCRIPT_DIR" != "$CLAUDE_DIR" ]; then
    echo "警告: このスクリプトは ~/.claude 以外から実行されています"
    echo "現在の場所: $SCRIPT_DIR"
    echo ""
    read -p "~/.claude にシンボリックリンクを作成しますか？ [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        if [ -e "$CLAUDE_DIR" ]; then
            BACKUP_DIR="$HOME/.claude-backup-$(date +%Y%m%d%H%M%S)"
            echo "既存の ~/.claude を $BACKUP_DIR にバックアップ..."
            mv "$CLAUDE_DIR" "$BACKUP_DIR"
        fi
        ln -s "$SCRIPT_DIR" "$CLAUDE_DIR"
        echo "シンボリックリンクを作成しました: ~/.claude -> $SCRIPT_DIR"
    else
        echo "中止しました"
        exit 1
    fi
fi

# 2. 必要なディレクトリを作成
echo "ディレクトリを作成中..."
mkdir -p "$CLAUDE_DIR/.local/memory"
mkdir -p "$CLAUDE_DIR/.local/memories"
mkdir -p "$CLAUDE_DIR/.local/issues"
mkdir -p "$CLAUDE_DIR/cache"
mkdir -p "$CLAUDE_DIR/plans"

# 3. 依存ツールの確認
echo ""
echo "=== 依存ツールの確認 ==="
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1: $(command -v $1)"
    else
        echo "✗ $1: 未インストール"
        return 1
    fi
}

check_tool "jq" || echo "  → brew install jq"
check_tool "git" || echo "  → brew install git"
check_tool "gh" || echo "  → brew install gh"

# 4. MCPサーバーの確認（npxが必要）
echo ""
echo "=== MCP サーバー ==="
if command -v npx &> /dev/null; then
    echo "✓ npx: 利用可能"
    echo "  context7 MCP: npx -y @upstash/context7-mcp@latest"
else
    echo "✗ npx: 未インストール（Node.js が必要）"
fi

# 5. 設定ファイルの確認
echo ""
echo "=== 設定ファイル ==="
[ -f "$CLAUDE_DIR/settings.json" ] && echo "✓ settings.json" || echo "✗ settings.json が見つかりません"
[ -f "$CLAUDE_DIR/CLAUDE.md" ] && echo "✓ CLAUDE.md" || echo "✗ CLAUDE.md が見つかりません"

# 6. Gitの設定確認
echo ""
echo "=== Git 設定 ==="
if [ -d "$CLAUDE_DIR/.git" ]; then
    echo "✓ Gitリポジトリ: 初期化済み"
    REMOTE=$(git -C "$CLAUDE_DIR" remote get-url origin 2>/dev/null || echo "未設定")
    echo "  リモート: $REMOTE"
else
    echo "✗ Gitリポジトリ: 未初期化"
fi

# 7. グローバルgitignoreに.local/を追加
echo ""
echo "=== Global gitignore ==="
GLOBAL_GITIGNORE=$(git config --global core.excludesfile 2>/dev/null || echo "$HOME/.gitignore_global")
if [ -z "$GLOBAL_GITIGNORE" ]; then
    GLOBAL_GITIGNORE="$HOME/.gitignore_global"
    git config --global core.excludesfile "$GLOBAL_GITIGNORE"
fi

if [ -f "$GLOBAL_GITIGNORE" ]; then
    if grep -q "^\.local/$" "$GLOBAL_GITIGNORE" 2>/dev/null; then
        echo "✓ .local/ は既にグローバルgitignoreに含まれています"
    else
        echo ".local/" >> "$GLOBAL_GITIGNORE"
        echo "✓ .local/ をグローバルgitignoreに追加しました"
    fi
else
    echo ".local/" > "$GLOBAL_GITIGNORE"
    echo "✓ グローバルgitignoreを作成し、.local/ を追加しました"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. Claude Code を再起動してください"
echo "2. 設定変更後は: cd ~/.claude && git add -A && git commit -m 'update' && git push"
echo ""
