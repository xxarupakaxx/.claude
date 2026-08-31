# Quality gate

## 静的構造

- [ ] stage target は regular file / directory だけで、symlink・実行 bit・binary を含まない。
- [ ] `SKILL.md` の frontmatter は full YAML で解析でき、`name`、`description`、`license`、`metadata.version` がある。
- [ ] 参照された JIT file が存在し、常時読む全 reference の列挙になっていない。
- [ ] `SOURCE` は固定 commit、package tree、manifest、quarantine path、license evidence、runtime status を指す。
- [ ] `LICENSE` は upstream root の原文 evidence と区別されている。

## HTML / SVG

- [ ] HTML は self-contained、inline CSS、inline SVG、text fallback、source list を持つ。
- [ ] HTML / SVG の外部 URL、remote font、`@import`、`<script>`、iframe、`foreignObject`、network API、browser export が0。
- [ ] SVG は `viewBox`、`role="img"`、`aria-labelledby`、非空 title / desc を持つ。
- [ ] connector は直交、label mask は線から離れ、node より先に描かれる。
- [ ] CJK は system fallback、文字サイズを小さくして詰めていない。
- [ ] source anchor、Before / After id、unknown、fidelity ledger が表示される。

## 用途 fixture

静的 checker は「正しい図を生成できる」ことを証明するものではなく、代表 fixture の契約を確認するものとする。

1. positive trigger: dependency、process、architecture、comparison の問いが type に到達する。
2. negative trigger: 短い表、progress dashboard、canonical state、根拠なしの装飾は図を選ばない。
3. dependency: Before の平坦な列挙と candidate の rank / fan-in / shared dependency を計測する。
4. source trace: fixture はデモと明記し、実プロジェクトの完了・効果・採用状態を推測しない。

この gate の PASS は構文・静的契約の PASS であり、context 削減や読者の理解向上を実測したという意味ではない。
