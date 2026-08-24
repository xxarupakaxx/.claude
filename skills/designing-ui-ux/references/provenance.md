# Provenanceと採用境界

## 外部スキルから採用した考え方

`nextlevelbuilder/ui-ux-pro-max-skill` は、style、color、typography、product type、UX guideline、chart、technology stackを検索可能な知識として分離し、プロダクト条件から一つのdesign systemを推薦する。

このローカルSkillは、次の考え方を採用した。

- プロダクト文脈を入力として、視覚選択を理由付きで収束させる。
- design domainを分け、必要な知識だけを取得する。
- 実装前にdesign system contractを作る。
- 実装後にanti-patternと実画面を確認する。
- 共通原則とstack固有の制約を分離する。

大量の候補件数は品質の保証にならないため、外部データベースとCLIは同梱していない。
catalogは探索を速めるが、利用者の仕事、既存design system、実データ、platform conventionを置き換えない。

## 参照元

- Repository: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Fixed revision: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/13179471f97162b3297558621a76682438caf017
- Skill source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/13179471f97162b3297558621a76682438caf017/.claude/skills/ui-ux-pro-max/SKILL.md
- Search engine: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/13179471f97162b3297558621a76682438caf017/src/ui-ux-pro-max/scripts/core.py
- Design system generator: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/13179471f97162b3297558621a76682438caf017/src/ui-ux-pro-max/scripts/design_system.py
- License: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/13179471f97162b3297558621a76682438caf017/LICENSE
- 参照日: 2026-08-24

外部リポジトリはMIT Licenseで公開されている。
コードまたはデータの実質的な部分を将来同梱する場合は、copyright noticeとlicense noticeを同梱する。

## 基準の一次情報

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- ARIA in HTML: https://www.w3.org/TR/using-aria/
- ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- Apple Human Interface Guidelines, Motion: https://developer.apple.com/design/human-interface-guidelines/motion
- Apple Human Interface Guidelines, Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Android Accessibility: https://developer.android.com/design/ui/mobile/guides/foundations/accessibility

数値や適合レベルは、記憶や外部catalogではなく、対象versionの仕様で確認する。
upstream内でもREADME、catalog、skill metadata、CLI metadataの件数とversionが一致しないため、候補件数をローカルの品質主張へ使わない。
