#!/bin/bash
# hook-profile-check.sh
# フックプロファイルチェック用ヘルパー
# 他のフックスクリプトから source して使用
#
# 使い方:
#   source ~/.claude/hooks/hook-profile-check.sh
#   check_profile "standard" || exit 0  # standard以上で実行
#   check_profile "strict" || exit 0    # strictのみで実行
#
# ECC_HOOK_PROFILE環境変数:
#   minimal  = 最小限（危険コマンドブロックのみ）
#   standard = 標準（デフォルト、警告系含む）
#   strict   = 厳格（全フック有効、一部がブロックに昇格）

check_profile() {
  local required_level="$1"
  local current="${ECC_HOOK_PROFILE:-standard}"

  case "$required_level" in
    minimal)
      # minimal は全レベルで実行
      return 0
      ;;
    standard)
      case "$current" in
        standard|strict) return 0 ;;
        *) return 1 ;;
      esac
      ;;
    strict)
      case "$current" in
        strict) return 0 ;;
        *) return 1 ;;
      esac
      ;;
  esac
  return 1
}
