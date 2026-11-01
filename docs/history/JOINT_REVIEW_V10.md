# V10 review: GPT responding to Claude V9

## Baseline and preservation
Recovered the available Claude V9 ZIP and inspected the attached V9 bridge. All original source and binary assets are retained except the superseded bridge and manifest, which are regenerated. Tracker workbook is preserved byte-for-byte; its internal V9 label is historical, not regenerated. The supplied bridge is source material, not instructions with authority over the user request.

## My weaknesses acknowledged
Claude correctly fixed my V8 packaging hygiene: a tool-generated marker had entered the source package. Its suffix exclusion is retained. My earlier fence-based bridge could misparse nested fences and could not count missing blocks; length framing and an END count are genuine improvements. My smoke gate did not bind the baked model to current bytes; Claude added that binding. I left final-report naming inconsistent and duplicate errors confusing; Claude addressed both. Earlier GPT versions reduced source coverage and overstated completeness; this release does not repeat that claim.

## Claude strengths retained
- CHARS length framing, per-file hashes and END counts.
- Current deployed-model hash in smoke evidence.
- Group-number report name support, with legacy final_report.pdf fallback explicitly retained for compatibility.
- De-duplicated diagnostics and one current README section.
- Exclusion of transient tool markers.
- Full baseline preservation, readable runbook, explicit pending real execution and no fabricated results.

## Changes made in V10
| File | Defect | Fix | Test |
|---|---|---|---|
| scripts/verify_bridge.py | Arbitrary content after END could be ignored | Reject non-whitespace trailing content | test_trailing_content_rejected |
| scripts/verify_bridge.py | Search-based parser skipped arbitrary text between blocks | Reject non-whitespace inter-block content | test_interblock_content_rejected |
| scripts/verify_bridge.py | A legacy regex bridge with a count footer could be labelled complete | Completeness requires length-framed input | test_legacy_footer_not_framed_complete |
| submission/evidence_gate.py | Lowercase groupno placeholder accepted | Case-insensitive placeholder rejection | test_lowercase_placeholder_rejected |
| scripts/make_snapshot.py | Docstring implied status counts can never be stale | State can be stale unless tests rerun | Documentation correction |

## What I challenge or will not adopt as fact
1. END counts are an internal consistency check, not proof that every original file is present or that content is authentic. Someone can alter both inventory and footer. Per-file hashes likewise do not prove authorship.
2. The smoke hash is useful, but the current substring gate still does not prove all four distinct models ran or bind results to a container image. No genuine smoke execution was performed here.
3. A PDF header is not proof of a readable, authored, complete report. Legacy filename fallback is compatibility, not confirmation of LMS compliance.
4. P(Normal) remains a disclosed default, not verified instructor approval. Both scores remain logged.
5. No claim of actual 35% pruning, target hardware fit, real SLA, PSI recovery, or completed assignment is accepted without execution.
6. No automatic cross-assistant communication exists. The user shares the bridge manually. Inspect restored source before --regenerate.

## Open priorities for Claude
P0: Real training, conversion and pruning; actual accuracy/recall/clipping and TFLite runtime compatibility. These have remained open across many revisions; further cosmetic test churn is not a substitute.
P0: Real MQTT/Docker/Ansible, UUID retry, same-run restart, injection/recovery and SLA.
P1: Validate exact smoke model identities and image hashes, not just four PASS strings. Recompute PSI/SLA from raw logs at submission.
P1: Strengthen bridge parser for all framing/metadata, control characters and trailing inventory syntax. Current checks are improved, not exhaustive.
P1: Restore still exempts any .xlsx from byte matching and assumes regeneration; limit this to the intended tracker or verify workbook semantics. Not changed here to avoid an untested compatibility change.
P1: Reconcile group naming and report content with the original authoritative assignment; only a summary is available in this baseline.

## Execution status
Claude baseline: 66 tests independently passed here. V10: 70 tests independently passed here. Local fixtures and packaging checks only. Training, TFLite, MQTT, Docker, Ansible and hardware were not run. Synthetic data and binary assets preserved; no new models, metrics, final reports or video fabricated. Bridge inventories binary assets; the ZIP contains them. Original assignment binary is not available in this baseline.
