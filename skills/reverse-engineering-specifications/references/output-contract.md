# Output Contract

4成果物は同じrepository source identityとscopeを参照する。
各fileの先頭に次のmetadataを置く。

```yaml
---
task:
phase_or_step: specification-extraction
created_at:
repository:
scope:
source_identity:
  revision:
  working_tree: clean
  changed_paths: []
  untracked_paths: []
  diff_digest:
  untracked_digest:
  submodule_revisions: []
generated_at:
generator: reverse-engineering-specifications-v1
---
```

host workflowが追加metadataを要求する場合は削除せず併合する。
dirtyでは変更pathと各digestを必須とし、revision SHAだけをsource identityとして扱わない。
pathは安全なrepo-relative表現にし、機微情報を含む場合は`[REDACTED_PATH]:sha256:<digest>`にする。
dirtyなsubmoduleは記録済みrevisionだけを使い、未commit内容をEvidenceへ含めずUnknownへ記録する。
## 共通item fields
REQ、DES、TC、Fの全itemはClassification、Confidence、Evidenceを必須とする。

```markdown
### REQ-001: <short title>

- Classification: Observed | Inferred | Unknown
- Confidence: High | Medium | Low
- Evidence:
  - `path/to/file.ext:42` — `symbol`が示す挙動
- Traces to: DES-001, TC-001
- Alternatives: <Inferredの場合の代替解釈>
- Open question: <Unknownの場合に必要な追加証拠>
```

REQはacceptance criteria、DESはtraces-to REQ、TCは対象REQとpass/fail条件、Fはseverity、affected IDs、impact、remediationも必須とする。
Evidenceはrepo-relative pathとsource identityに含まれる内容のlineを指す。
lineを安定して取得できないbinary、generated file、外部serviceは、参照できるmanifestまたはinterfaceを示し、制約を説明する。
secret、credential、個人情報の実値は引用せず、symbol名またはredactionだけを使う。

## requirements.md
次の順で書く。

1. Overview
2. Repository and Revision
3. Scope and Non-Goals
4. Definitions and Glossary
5. Functional Surface
6. Requirements
7. Dependencies
8. Assumptions
9. Risks
10. Unknowns
11. Revision History

各requirementは`REQ-NNN`を持ち、次を含める。

- actorまたはcalling system
- preconditionとinput
- observable behaviorとoutput
- errorまたはnegative behavior
- invariantまたはconstraint
- 一つ以上の`AC-N` acceptance criteria
- Classification、Confidence、Evidence

根拠のないpersona、KPI、business rationaleはrequirementsへ確定記載しない。
## design.md
次の順で書く。

1. Overview
2. Architecture and Boundaries
3. Components and Responsibilities
4. Data Models and State
5. Interfaces and Data Flows
6. Failure Handling
7. Security and Trust Boundaries
8. Operational Concerns
9. Constraints and Tradeoffs
10. Open Questions
11. Revision History

各design要素は`DES-NNN`を持ち、一つ以上の`REQ-NNN`へtraceする。
実在する構造と推定した設計意図を同じ文で混ぜない。

## validation.md
次の順で書く。

1. Overview
2. Validation Scope
3. Existing Test Evidence
4. Requirements Traceability Matrix
5. Test Cases
6. Coverage Gaps
7. Risk-Based Priorities
8. Entry and Exit Criteria
9. Revision History

matrixは最低限、次の列を持つ。

| Requirement | Acceptance Criteria | Design | Test Case | Existing Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | AC-1 | DES-001 | TC-001 | `tests/example:20` | verified / partial / gap |

各test caseは`TC-NNN`を持ち、対象requirement、test level、setup、observable result、pass/fail条件を記す。
既存testと提案testを明確に分ける。

## audit.md
次の順で書く。

1. Executive Summary
2. Audit Scope
3. Evidence Coverage
4. Forward Traceability
5. Backward Traceability
6. Consistency Findings
7. Unknown and Conflict Register
8. Remediation
9. Verdict
10. Re-extraction Triggers
11. Revision History

findingは`F-NNN`を持ち、severityを`CRITICAL`、`IMPORTANT`、`MINOR`で示す。
各findingにaffected IDs、Evidence、impact、remediationを含める。

verdictは次のいずれかである。

- `PASS`: 重大なtraceability gapがなく、Unknownが明示されている。
- `REVISE`: boundedな修正または人間確認で整合できる。
- `RESTART`: scopeまたはrepository理解が根本的に不足している。

再抽出条件には、少なくともsource revision変更、public interface変更、schema変更、重要test変更、Unknownの解決を含める。
