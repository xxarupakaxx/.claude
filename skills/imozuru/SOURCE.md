# 出典とローカル調整

- Repository: https://github.com/MaryCache/imozuru
- 固定commit: `980ec7f50f0b954e9e1b1d85865c29a427c8e776`
- 原典directory: `skills/imozuru`
- 原典package Git tree: `4c2f54bfe0750a1f98d875701a90393f05a2eb7a`
- 原典SKILL blob: `0d0ebe99d3b478468702587cfc525640ba1e34d4`
- 原典6fileの検査用tree SHA-256: `33a79d5de6e28e20582f35d439ef753d691ae5537506888195f9e6442ce0b75b`
- License: MIT。原典のLICENSEを同梱する。
- 固定日: 2026-10-20

原本はruntime外のquarantineで保持する。この導入版は、原本の純粋なHTML抽出、引用探索、RSS解析、引用照合を残し、直接通信・外部プロセス起動を除去した適応版である。通信は専用runnerが管理する。PDF、OCR、動画取得、外部ツールは無効。

追加したrun.pyは、公開IPへの固定接続、完全network-denyの取得処理と資料処理、FDによる保存先保持、時間・容量・メモリ上限、起動時のrestricted-auditを担当する。固定scopeのcapability判定を明示して使い、全体監査の警告と個別の実行可否を分ける。固定Pythonのisolated/no-site起動を要求し、調査メモと引用データはputから同じworkerで保存する。取得した原文のHTML・画像記法は表示時に動かないようescapeする。書込は新規一時inodeを検査してから置き換え、既存inodeを直接truncate・appendしない。HTMLにはCSP、artifact-kind、focus表示を加えた。不可視の方向制御文字はASCII escapeにした。

制限と運用は[利用条件](references/local-integration.md)を参照する。更新は自動で行わず、新しいsourceとtargetの審査・承認を必要とする。
