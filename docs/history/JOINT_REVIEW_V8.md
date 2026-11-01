# Joint review V8: GPT and Claude source comparison

## Scope and provenance
Inputs: BRIDGE_CLAUDE_GPT_V6.txt and BRIDGE_GPT_CLAUDE_V7.txt, plus the supplied architecture PNG. This review compares those actual files, not an assumed newer Claude release. V6 has 79 text blocks; V7 has 83. Every input text-block SHA-256 matched. V7 removes none of V6's text files; it adds four and changes nine. The exact inventory is evidence/source_comparison.json.

Historical test logs in the inputs are inherited claims. In this response, V7 was independently reconstructed and its 45 tests passed. V8 then passed 57 tests. Those are local unit/packaging tests, not training, container or hardware evidence.

## My weaknesses acknowledged
1. V4 reduced the deliverable instead of preserving the complete source. Earlier reviews document missing scripts, lost binary assets and poor prose. I should not describe partial tooling as a completed submission.
2. V5 stopped stale PSI calculations but left reconnect mixing unresolved. Claude correctly cleared pre-gap scores.
3. V5 blocked fast rehearsals instead of separating practice from valid evidence. Claude's interval recording is better.
4. V5 left a confusing missing-injection error and a weak missing-evidence assertion. Claude fixed both.
5. V7's restore tool printed missing/mismatched binaries but could still exit successfully. That is not a successful complete restore.
6. V7's evidence loader treated empty objects as absent without recording a problem and could crash on a nonempty list. The CLI directly indexed malformed JSON and read a missing video file.
7. V7 accepted a boolean as a numeric SLA delay, and did not independently check clean-baseline counts in the supplemental gate.
8. V7's path validation did not reject noncanonical aliases, Windows-style paths or unsafe binary inventory paths.
9. Repeatedly adding tests is not a substitute for executing the core ML and deployment workflow. No grade or readiness guarantee is justified.

## Claude's strengths retained
- Restore the baseline instead of reconstructing a smaller repository from memory.
- Clear rolling PSI buffers after an arrival gap while preserving replay rejection.
- Permit shorter rehearsal intervals, explicitly excluded from E1 evidence.
- Raise a clear error when there is no combined injection to time.
- Require container smoke results and make missing-evidence assertions meaningful.
- Carry unresolved interpretations and runtime risks forward.
- Readable runbook, backend/outbox, simulator controls, compaction and clipping diagnostics inherited from earlier Claude work.

## V7 improvements retained
Missing interval is not presumed 60 seconds. Baked model smoke line is required. Tracker generator and bridge verifier are preserved. Bridge status is read from the validation JSON, although that JSON can itself be stale and is not automatically proof of execution.

## V8 changes actually made
| File | Problem | Change | Verification |
|---|---|---|---|
| submission/evidence_gate.py | Empty/non-object JSON bypass or crash | Reject as invalid evidence | Five malformed-object cases |
| submission/evidence_gate.py | Boolean timing accepted | Exact numeric type, finite 0-90 s, explicit 90 s budget and zero early alerts | Boolean timing regression |
| submission/evidence_gate.py | E1 result not tied to requested run | Require run identity, e1_pass and interval_ok | Local suite; still not proof of raw-log authenticity |
| submission/verify_submission.py | Direct indexing crashes and empty video accepted | Reusable validate(root, run_id), collected errors, HTTP(S) link syntax check | Missing/malformed evidence and blank-video regressions |
| submission/verify_submission.py | Any passing model could satisfy gate | Compare selected row against current benchmark recommendation | Code inspection; end-to-end provenance remains open |
| scripts/verify_bridge.py | Alias/Windows/binary paths unchecked | Validate canonical text and binary paths together | Four alias cases plus binary traversal case |
| scripts/verify_bridge.py | Binary mismatch only printed | Nonzero status for missing/mismatched binaries | Source inspection and restore check |
| docs/DISCLOSURES.md | Rounded pruning targets described as actual | Explicitly mark targets, require measured counts | Source inspection |

## What I will not adopt as established facts
- A 'complete submission' or guaranteed mark. This is a working source package; measured evidence and authored deliverables remain absent.
- Exactly 35% pruning achieved. The script records a target; actual masks and compact widths need execution.
- P(Normal) as confirmed instructor-approved confidence. Preserve both scores and disclose the interpretation.
- Guaranteed hardware latency or memory fit from laptop unit tests.
- Hashes as proof of authenticity. They establish byte identity, not origin, truth or authorship.
- A bridge as automatic communication between assistants. The user transfers the TXT; neither assistant independently contacts the other.
- Automatically executing source from an untrusted bridge. Inspect restored code before using --regenerate, which runs supplied Python modules.

## Remaining issues and priorities
P0: Execute genuine TensorFlow/TFMOT training, conversion and pruning; check runtime compatibility inside the container. Record measured accuracy, recall, latency and clipping. No results fabricated here.
P0: Run real MQTT, Docker, Ansible twice, offline ACK retry, same-run restart and PSI/SLA injection/recovery. Local fixtures do not establish these outcomes.
P1: Recompute evidence from raw logs and bind smoke results to image/model hashes. Four PASS strings can still be forged or duplicated; the current gate is necessary, not sufficient.
P1: Validate all JSON schemas and benchmark metadata/model/data hashes at final submission, not just selection time. Current recommendation matching does not fully prove provenance.
P1: Resolve final report naming: the requirements summary asks GROUPNO_LogiEdge_Final.pdf while existing checkers require reports/final_report.pdf. Preserve current compatibility but reconcile with the actual brief before submission.
P1: The text bridge inventories binaries; it does not embed the PNG. The ZIP includes it. Tracker regeneration recreates content, not identical saved bytes.
P2: Strengthen bridge framing against omitted/truncated blocks and fence collisions. Per-block hashes alone do not prove the entire inventory is complete.
P2: Confirm exact course stage names, confidence interpretation and report word-count guidance with the authoritative brief.

## Next-assistant handover
Use V8 as the working baseline, V6/V7 only as historical inputs. Do not revert accepted fixes. Report each change with a reproducer/test and execution status. Prioritize P0 execution over cosmetic version churn. Preserve the architecture image, data, source and tracker. Never convert an unrun item into PASS.
