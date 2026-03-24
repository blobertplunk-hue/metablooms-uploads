================================================================================
METABLOOMS OS v10 Full — PIECE 4 of 4
Title: Mistake Registry (81 classes) + Success Registry (26 patterns)
Generated: 2026-03-23T00:14:11.401051+00:00
================================================================================

PURPOSE: MISTAKE REGISTRY: 81 named failure classes. Quick lookup table for all 81. Full detail for S4_CRITICAL entries. Use this for pre-action checks — scan for patterns relevant to your current action before executing. SUCCESS REGISTRY: 26 patterns. What works and when to apply it. Full protocol for key patterns including TRY_BEFORE_REFUSE and FOUR_LOOPS_CHECK. After reading: pre-action check is live — you have the full registry.

LOAD ORDER: Read pieces in sequence 1→4.
  Piece 1: Boot identity + Three Laws + system understanding
  Piece 2: Epistemic governance (ERAC, Turn, BTS, Learning)
  Piece 3: Behavioral protocol + session state + architecture
  Piece 4: Mistake registry (81 classes) + success registry (26 patterns)

READS AFTER: Piece 3 (Behavioral Protocol)

================================================================================

================================================================================
FILE: learning/MISTAKE_REGISTRY.json
HASH: a7b6c276f4b1be7ec5de0a4cf852787a832f0f6d9f1ec46292e423d1590cd259
================================================================================
## MISTAKE REGISTRY — 81 classes
Reference during pre-action checks. Full detail shown for S4_CRITICAL.
For others: ID | severity | name | self_check

### QUICK LOOKUP TABLE (all classes)
| ID | Severity | Name | Self-Check |
|----|----------|------|------------|
| ME-EXPORT-001 | S4_CRITICAL | WRONG_BUNDLE_ROOT |  |
| ME-EXPORT-002 | S4_CRITICAL | VERSION_INCOHERENCE |  |
| ME-EXPORT-003 | S4_CRITICAL | MISSING_BOOT_ARTIFACTS |  |
| ME-FIR-001 | S4_CRITICAL | HARDCODED_FITNESS_SCORE |  |
| ME-MPP-001 | S4_CRITICAL | STAGE_BYPASSED |  |
| ME-EXPORT-004 | S4_CRITICAL | STALE_BUNDLE_AUDITED |  |
| ME-STATE-002 | S4_CRITICAL | HALLUCINATED_PRIOR_STATE |  |
| ME-CODE-005 | S4_CRITICAL | IRREVERSIBLE_ACTION_NO_DRYRUN |  |
| ME-VERIF-001 | S4_CRITICAL | NO_OR_INCOMPLETE_VERIFICATION |  |
| ME-VERIF-002 | S4_CRITICAL | INCORRECT_VERIFICATION |  |
| ME-ERAC-006 | S4_CRITICAL | NARRATIVE_THEATER |  |
| ME-VERIF-003 | S4_CRITICAL | QUALITY_DEGRADATION_NOT_CAUGHT |  |
| ME-ARCH-007 | S4_CRITICAL | GHOST_ENGINE_DEPENDENCY |  |
| ME-EXPORT-006 | S4_CRITICAL | SKELETON_SHIPPED_AS_COMPLETE |  |
| ME-STATE-005 | S4_CRITICAL | CONVERSATION_AS_STATE |  |
| ME-ARCH-010 | S4_CRITICAL | FRANKEN_INTEGRATION |  |
| ME-OS-001 | S4_CRITICAL | EXECUTION_KERNEL_WITHOUT_GOVERNANCE_LAYER |  |
| ME-OS-002 | S4_CRITICAL | BOOT_CONTRACT_AS_SYSTEM_COMPLETENESS |  |
| ME-OS-004 | S4_CRITICAL | PARTIAL_OS_ACCEPTED_AS_COMPLETE | Am I running MetaBlooms or just an execution pipeline? |
| ME-OS-006 | S4_CRITICAL | INCONSISTENT_BOOT_STANDARD | Does every file listed in BOOT_HEADER_SPEC.verification_rules exist in the zip?  |
| ME-FIR-002 | S3_HIGH | WRONG_RECEIPT_SOURCE |  |
| ME-MPP-002 | S3_HIGH | AUTO_PASS_PAYLOAD |  |
| ME-ERAC-001 | S3_HIGH | CANNED_VERIFICATION_CONTENT |  |
| ME-EXPORT-005 | S3_HIGH | START_HERE_NOT_UPDATED |  |
| ME-EXPORT-AUTO-8E5649 | S3_HIGH | TOO_FEW_FILES |  |
| ME-EXPORT-AUTO-2A69E1 | S3_HIGH | ENGINE_REGISTRY_UNREADABLE |  |
| ME-EXPORT-AUTO-5F778A | S3_HIGH | ENGINE_REGISTRY_UNREADABLE |  |
| ME-ERAC-002 | S3_HIGH | SURFACE_INFERENCE |  |
| ME-ERAC-003 | S3_HIGH | FAILURE_WITHOUT_ROOT_CAUSE |  |
| ME-PLAN-001 | S3_HIGH | PREMATURE_TERMINATION |  |
| ME-CODE-001 | S3_HIGH | AMBIENT_ASSUMPTION |  |
| ME-CODE-003 | S3_HIGH | NONIDEMPOTENT_WRITE |  |
| ME-CODE-004 | S3_HIGH | HEREDOC_FOOTGUN |  |
| ME-ARCH-002 | S3_HIGH | ARTIFACT_NAMESPACE_COLLISION |  |
| ME-ARCH-003 | S3_HIGH | DISOBEY_ROLE_SPECIFICATION |  |
| ME-ARCH-005 | S3_HIGH | REASONING_ACTION_MISMATCH |  |
| ME-ERAC-005 | S3_HIGH | MEASUREMENT_WITHOUT_VERIFICATION |  |
| ME-ERAC-007 | S3_HIGH | METRIC_CONFABULATION |  |
| ME-VERIF-004 | S3_HIGH | VISUAL_VERIFICATION_NOT_STRUCTURAL |  |
| ME-ARCH-006 | S3_HIGH | WRONG_VERSION_ANALYZED |  |
| ME-ARCH-008 | S3_HIGH | LAYER_ORDER_INVERTED |  |
| ME-STATE-004 | S3_HIGH | TELEMETRY_SCHEMA_DRIFT |  |
| ME-ERAC-009 | S3_HIGH | AUTHORITY_ILLUSION |  |
| ME-ERAC-010 | S3_HIGH | ROLE_DRIFT |  |
| ME-ERAC-011 | S3_HIGH | SYNTHETIC_CONSENSUS |  |
| ME-PLAN-004 | S3_HIGH | CONFIDENCE_LOOP |  |
| ME-CODE-009 | S3_HIGH | LLM_CODING_OVERCONFIDENCE |  |
| ME-PLAN-005 | S3_HIGH | PERSISTENCE_WITHOUT_ADVERSARIAL_VALIDATION |  |
| ME-VERIF-005 | S3_HIGH | PREMATURE_VICTORY_CLAIM |  |
| ME-CODE-010 | S3_HIGH | INVALID_JSON_STRUCTURE |  |
| ME-EXPORT-AUTO-65B073 | S3_HIGH | DEPENDENCY_GRAPH_MISSING |  |
| ME-EXPORT-AUTO-4C28D3 | S3_HIGH | PROOF_REGISTRY_MISSING |  |
| ME-EXPORT-AUTO-182639 | S3_HIGH | GRAPH_NOT_RECONCILED |  |
| ME-EXPORT-AUTO-ABB67D | S3_HIGH | EXECUTION_TRACE_LOG_MISSING |  |
| ME-EXPORT-AUTO-74B939 | S3_HIGH | RUNTIME_TRACE_SPANS_MISSING |  |
| ME-EXPORT-AUTO-004549 | S3_HIGH | RUNTIME_TURN_SPANS_MISSING |  |
| ME-EXPORT-AUTO-E8A589 | S3_HIGH | TURN_TRACE_INDEX_MISSING |  |
| ME-EXPORT-AUTO-7E8FD9 | S3_HIGH | TRACE_ANOMALIES_MISSING |  |
| ME-EXPORT-AUTO-16BF4D | S3_HIGH | TRACE_REPAIR_HINTS_MISSING |  |
| ME-EXPORT-AUTO-0E8F92 | S3_HIGH | PATTERN_REGISTRY_MISSING |  |
| ME-OS-003 | S3_HIGH | TASK_SCOPING_MYOPIA |  |
| ME-OS-005 | S3_HIGH | REFUSE_WITHOUT_ATTEMPTING | Did I attempt this before refusing? If no attempt: I am committing ME-OS-005. Tr |
| ME-BTS-001 | S2_MED | RECEIPTS_NOT_REGISTERED |  |
| ME-CDR-001 | S2_MED | CDR_HEADER_MISSING |  |
| ME-GENERAL-001 | S2_MED | FIR_THRESHOLD_MISCALIBRATED |  |
| ME-ERAC-004 | S2_MED | MISSING_MODEL_FAILURE_MODE |  |
| ME-STATE-001 | S2_MED | CONTEXT_LOSS |  |
| ME-STATE-003 | S2_MED | OVER_SIMPLIFICATION |  |
| ME-PLAN-002 | S2_MED | GOAL_DRIFT |  |
| ME-CODE-002 | S2_MED | SILENT_FAILURE |  |
| ME-CODE-006 | S2_MED | ENVIRONMENT_MISMATCH |  |
| ME-ARCH-001 | S2_MED | INTENT_RESOLUTION_COLLISION |  |
| ME-ARCH-004 | S2_MED | UNAWARE_OF_STOPPING_CONDITIONS |  |
| ME-ERAC-008 | S2_MED | RETROACTIVE_NARRATIVE_CONSTRUCTION |  |
| ME-CODE-007 | S2_MED | SCOPE_CREEP |  |
| ME-CODE-008 | S2_MED | API_MISMATCH_TRUSTED_WITHOUT_VERIFICATION |  |
| ME-MPP-003 | S2_MED | RECOGNITION_WITHOUT_OPERATIONALIZATION |  |
| ME-ERAC-012 | S2_MED | SEMANTIC_OVERREACH |  |
| ME-ARCH-009 | S2_MED | COGNITIVE_TECHNICAL_DEBT |  |
| ME-CODE-011 | S2_MED | TEMPLATE_CONTENT_NOT_SPECIALIZED |  |
| ME-PLAN-003 | S1_LOW | STEP_REPETITION |  |

### FULL DETAIL — S4_CRITICAL ONLY

#### ME-ARCH-007 — GHOST_ENGINE_DEPENDENCY
**Description:** Engine imported and called in production code but file does not exist anywhere in codebase. System appears to work until the missing import is hit at runtime.
**Detection:** import statement for engine that is absent from ENGINE_REGISTRY.json
**Prevention:** GovernanceKernel checks that every engine in ENGINE_REGISTRY.json exists. KERNEL_SUPERVISOR checks that every import in engine files resolves. ImportError at load = ghost engine.
**Self-check:** ?
**Fix:** ?

#### ME-ARCH-010 — FRANKEN_INTEGRATION
**Description:** Attempting to merge two incompatible architectural versions produces a hybrid that satisfies neither. Integration produces unreliable tool calling, inconsistent behavior, and failure modes from both systems.
**Detection:** integration of two systems with different runtime assumptions; tool call success rate drops below 60%
**Prevention:** Before any integration: define compatibility contract. If two systems have different runtime root assumptions, different state models, or different boot sequences — they cannot be merged, only one can be canonical.
**Self-check:** ?
**Fix:** ?

#### ME-CODE-005 — IRREVERSIBLE_ACTION_NO_DRYRUN
**Description:** Destructive operation (delete, overwrite, truncate, rm -rf) executed without dry-run mode or explicit confirmation gate. Data loss is irreversible.
**Detection:** shutil.rmtree, Path.unlink, os.remove, git reset --hard without dry_run=True guard
**Prevention:** All destructive ops behind dry_run=True flag. Trash-first pattern (move to .trash/) before delete. Explicit operator confirmation for S4_CRITICAL ops.
**Self-check:** ?
**Fix:** ?

#### ME-ERAC-006 — NARRATIVE_THEATER
**Description:** Claiming execution occurred when only narration occurred. Describing what would happen rather than what did happen. No tool calls shown, no actual file outputs, but confident claims of completion.
**Detection:** claim includes 'I just wrote/created/updated X' with no bash_tool or create_file call visible
**Prevention:** T1 receipt required for every claimed artifact. BTS TURN_END blocked if pipeline_complete=True but ledger artifacts_written contains paths not verified by T1 receipts.
**Self-check:** ?
**Fix:** ?

#### ME-EXPORT-001 — WRONG_BUNDLE_ROOT
**Description:** Zip archive extracted to wrong folder name. ChatGPT expects Metablooms_OS/ but got metablooms_v6/ or similar.
**Detection:** zip root folder != 'Metablooms_OS'
**Prevention:** Always use build_bundle() which enforces Metablooms_OS/ root. EXPORT_GATE.verify() blocks release if wrong root detected.
**Self-check:** ?
**Fix:** ?

#### ME-EXPORT-002 — VERSION_INCOHERENCE
**Description:** Filename, internal folder, and SESSION_HANDOFF bundle_version disagree about which version this is.
**Detection:** any(expected_version not in field_value for field_value in version_fields)
**Prevention:** EXPORT_GATE checks VERSION_FIELDS list against expected_version. build_bundle() passes expected_version through.
**Self-check:** ?
**Fix:** ?

#### ME-EXPORT-003 — MISSING_BOOT_ARTIFACTS
**Description:** Bundle presented without required boot artifacts. ChatGPT cannot boot.
**Detection:** any(required_file not in zip_entries for required_file in REQUIRED_BOOT_FILES)
**Prevention:** EXPORT_GATE.REQUIRED_BOOT_FILES checked on every bundle. MANIFEST.json lists all required files.
**Self-check:** ?
**Fix:** ?

#### ME-EXPORT-004 — STALE_BUNDLE_AUDITED
**Description:** ChatGPT (or Claude) audited an old bundle from /mnt/data/ instead of the current one. Version incoherence not caught because the wrong file was loaded.
**Detection:** bundle SHA256 does not match BUILD_IDENTITY.json build_hash, OR bundle_name contains old version string
**Prevention:** START_HERE_METABLOOMS.md names old bundles explicitly and says IGNORE THOSE. BUILD_IDENTITY.json contains bundle_name. CHATGPT_PROJECT_INSTRUCTIONS.md boot step 1 checks BUILD_IDENTITY.json. EXPORT_GATE requires BUILD_IDENTITY.json in every bundle.
**Self-check:** ?
**Fix:** ?

#### ME-EXPORT-006 — SKELETON_SHIPPED_AS_COMPLETE
**Description:** Release shipped with placeholder/stub content where substantive content was expected. Structural outline exists but no operational detail. Looks complete, is not.
**Detection:** release contains sections marked 'TBD', 'placeholder', or 'to be defined'; or sections with fewer than 3 sentences where operational detail was expected
**Prevention:** EXPORT_GATE: check that each section of delivered documents has minimum content density. Stub detection: sections with < 50 words in major content areas = flag.
**Self-check:** ?
**Fix:** ?

#### ME-FIR-001 — HARDCODED_FITNESS_SCORE
**Description:** evaluate_fitness() returned hardcoded 1.0 instead of measuring real data. A session that cannot be measured cannot be declared an improvement.
**Detection:** fitness_score = 1.0 (literal) in evaluate_fitness()
**Prevention:** FIR.evaluate_fitness() raises FIRDataError if data unavailable. Never returns fabricated score. CDR V5.
**Self-check:** ?
**Fix:** ?

#### ME-MPP-001 — STAGE_BYPASSED
**Description:** Orchestrator called execution engine directly, bypassing all MPP stages. Pipeline existed as documentation but was not wired.
**Detection:** orchestrator imports ExecutionLoopEngine directly without importing MPP
**Prevention:** METABLOOMS_OS.run_turn() only accepts handler — must go through MPP.run(). No direct execution path exists.
**Self-check:** ?
**Fix:** ?

#### ME-OS-001 — EXECUTION_KERNEL_WITHOUT_GOVERNANCE_LAYER
**Description:** Bundle exported with MPP execution engines but without behavioral governance layer: no state persistence, no learning registries, no ERAC contract, no BTS behavioral contract, no SESSION_HANDOFF, no TURN_STATE_LEDGER, no OBJECTIVE_ANCHOR. The exported artifact runs code but does not behave as MetaBlooms.
**Detection:** zip contains engines/*.py but missing ALL of: learning/, state/SESSION_HANDOFF.json, ERAC_CONTRACT.md, BTS_BEHAVIORAL_CONTRACT.md, TURN_PROTOCOL.md
**Prevention:** Run GOVERNANCE LAYER COMPLETENESS CONTRACT check before export. All four loops. All six layers.
**Self-check:** ?
**Fix:** ?

#### ME-OS-002 — BOOT_CONTRACT_AS_SYSTEM_COMPLETENESS
**Description:** 'Boot check passes' interpreted as 'system is complete'. The boot contract only verifies required files exist. A system that boots but lacks memory, learning, and deliberateness loops is not a functional OS.
**Detection:** CHATGPT_PROJECT_INSTRUCTIONS.md describes boot sequence that checks file presence but does not invoke LEARNING_ENGINE, BTS behavioral contract, or SESSION_HANDOFF continuity.
**Prevention:** Boot check is necessary but not sufficient. Always run GOVERNANCE LAYER COMPLETENESS CONTRACT separately.
**Self-check:** ?
**Fix:** ?

#### ME-OS-004 — PARTIAL_OS_ACCEPTED_AS_COMPLETE
**Description:** An agent (Claude or ChatGPT) accepts a bundle as MetaBlooms OS without verifying all four loops are present and functional. Boot file check passes but the OS is actually missing memory loop, learning loop, or behavioral governance layer. The agent proceeds as if it has a full OS.
**Detection:** Bundle boots successfully but learning/MISTAKE_REGISTRY.json absent, OR state/SESSION_HANDOFF.json absent, OR engines/BTS.py absent, OR ERAC_CONTRACT.md absent. Any one of these = partial OS, not MetaBlooms.
**Prevention:** Before accepting any bundle as MetaBlooms OS, run FOUR LOOPS CHECK: Loop1=SEE present? Loop2=MPP present? Loop3=SESSION_HANDOFF present? Loop4=MISTAKE_REGISTRY present? ALL FOUR required. If any missing: report partial OS, do not proceed as full OS.
**Self-check:** Am I running MetaBlooms or just an execution pipeline?
**Fix:** Run FOUR LOOPS CHECK. Name what is missing. Proceed only with what you actually have.

#### ME-OS-006 — INCONSISTENT_BOOT_STANDARD
**Description:** A bundle is exported with a boot contract that references files not included in the bundle. The boot contract and the actual file manifest disagree. ChatGPT boots against the contract, finds files missing, fails closed. Root cause: the exporter (Claude) built to a different boot standard than what the boot contract declares as required.
**Detection:** CHATGPT_PROJECT_INSTRUCTIONS.md or BOOT_HEADER_SPEC.json lists files X, Y, Z but X, Y, Z are absent from the zip. Specifically: RUNTIME_SPINE.json, RUNTIME_GRAPH.json, boot/METABLOOMS_BOOT_HEADER.txt referenced in boot contract but not generated in bundle.
**Prevention:** Before shipping any bundle: run BOOT_CONTRACT_MATCH check. Read BOOT_HEADER_SPEC.json verification_rules. For each rule requiring a file: verify that file is in the zip. Any mismatch = do not ship. Generate missing files first.
**Self-check:** Does every file listed in BOOT_HEADER_SPEC.verification_rules exist in the zip? Does every file shown in CHATGPT_PROJECT_INSTRUCTIONS file structure diagram exist?
**Fix:** Generate all files referenced in boot contract before shipping zip.

#### ME-STATE-002 — HALLUCINATED_PRIOR_STATE
**Description:** Generating false information about what happened in prior turns. Claiming an artifact was written when it wasn't, claiming a test passed when it didn't.
**Detection:** Claimed artifact not found on disk, or claimed receipt not in BTS log
**Prevention:** GovernanceKernel verifies engine receipts. BTS T1 required for every artifact write. SEE reads ledger before any claim about prior work.
**Self-check:** ?
**Fix:** ?

#### ME-STATE-005 — CONVERSATION_AS_STATE
**Description:** Treating conversation history as runtime state. Making decisions based on what was said in the chat rather than what is on disk. State that exists only in the context window disappears at session end.
**Detection:** turn references prior turn content directly ('as I mentioned earlier') without reading it from a state file
**Prevention:** STATE_LEDGER.read_current() at SEE. SESSION_HANDOFF.read() at boot. If decision is based on what was said rather than what is on disk: ERAC-001 violation.
**Self-check:** ?
**Fix:** ?

#### ME-VERIF-001 — NO_OR_INCOMPLETE_VERIFICATION
**Description:** VERIFICATION stage runs but produces no meaningful check. Asserts correctness without testing it. verify_passed=True with no actual evidence.
**Detection:** VERIFICATION payload has verify_passed=True but findings=[] or findings has no erac_anchor
**Prevention:** VERIFICATION must have: findings with erac_anchor, actual artifact path, council quorum >= 0.85, erac_clean=True. StagePayloadValidator blocks anything less.
**Self-check:** ?
**Fix:** ?

#### ME-VERIF-002 — INCORRECT_VERIFICATION
**Description:** Verification passes but is factually wrong. Council says PASS on output that contains errors. Incorrect verification is worse than no verification — it provides false confidence.
**Detection:** VERIFICATION council PASS followed by downstream failure in a subsequent turn
**Prevention:** ERAC-001: council must read actual artifacts, not summaries. STAGE_PAYLOAD_VALIDATOR auto-pass detection prevents narrative-only PASS.
**Self-check:** ?
**Fix:** ?

#### ME-VERIF-003 — QUALITY_DEGRADATION_NOT_CAUGHT
**Description:** System quality degrades across turns with no audit catching the cliff edge. Skip one turn's quality check — 5 turns of degradation follow before reset.
**Detection:** Output quality metric drops >50% from prior turn without FAIL-TO-FIX trigger
**Prevention:** KERNEL_SUPERVISOR per-turn heartbeat is the implementation. FIR composite measured end-of-session. Any composite drop >20% from prior session triggers immediate investigation before next objective.
**Self-check:** ?
**Fix:** ?




================================================================================
FILE: learning/SUCCESS_REGISTRY.json
HASH: 75a652c55c81c2a83cb15a4164a3743c2df00f4bee068245a7c4ee0cf1a0664d
================================================================================
## SUCCESS REGISTRY — 26 patterns
Apply these before taking action. Check which patterns are relevant.

### QUICK LOOKUP TABLE
| ID | Name | Repeat When |
|----|------|-------------|
| MS-ARCH-001 | R12_AS_SUBSTRATE | When adding new governance capability — implement it as a substrate layer, not a |
| MS-ARCH-002 | KERNEL_PLUS_MODULE_RING_OVER_MERGE | When integrating two systems with different runtime assumptions, different state |
| MS-ARCH-003 | APPEND_ONLY_LEDGER_AS_TRUTH | Every significant state change. Every decision with consequences. Every artifact |
| MS-BTS-001 | DELIBERATENESS_MECHANISM | Before any significant action: code generation, architecture decision, packaging |
| MS-CDR-001 | FULL_CDR_RETROFIT | Any new engine added. Any significant engine refactor. Session-end CDR audit. |
| MS-DIST-45ABA7 | AVOID_SEE_NO_EVIDENCE_AT_SEE | Before any action in SEE that could trigger SEE_NO_EVIDENCE: sie_receipts missin |
| MS-DIST-579727 | AVOID_ERAC001_AT_ERAC_SCAN | Before any action in ERAC_SCAN that could trigger ERAC-001: claimed file contain |
| MS-DIST-F9D4DC | AVOID_FORGE_ERROR_AT_FORGE | Before any action in FORGE that could trigger FORGE_ERROR: ast.parse failed on i |
| MS-ERAC-001 | FAIL_CLOSED_OVER_IMPROVISE | Always. If a required input is missing, absent, or fails verification: stop and  |
| MS-EXPORT-001 | GATE_BEFORE_PRESENT | Every single bundle build. No exceptions. build_bundle() enforces this automatic |
| MS-FIR-001 | REAL_FITNESS_MEASUREMENT | End of every session. After any significant engine change. After any packaging. |
| MS-GAPFINDER-001 | CONVERSATIONAL_VALIDATION_BEFORE_DEPLOYMENT | Before deploying any new engine or capability. Design test suite: simple → compl |
| MS-GOVERNANCE-001 | GOVERNANCE_KERNEL_RECEIPT_VERIFICATION | Every boot. METABLOOMS_CLAUDE.py auto-generates receipts on _ensure_runtime(). R |
| MS-LESSON-001 | LESSON_CHECK_PREVENTS_AUTO_PASS | Before any stage advancement in MPP pipeline. check_stage() must return PASS bef |
| MS-OS-001 | GOVERNANCE_LAYER_COMPLETENESS_CHECK | Every single MetaBlooms OS export. No exceptions. |
| MS-OS-002 | THREE_HORIZON_BEFORE_EXPORT | Before any export, architecture decision, or significant code generation. |
| MS-OS-003 | TRY_BEFORE_REFUSE | Any time you are about to say 'I cannot', 'I don't have access', 'X is not avail |
| MS-OS-004 | FOUR_LOOPS_CHECK_BEFORE_BOOT | Every boot. Every export. No exceptions. |
| MS-PLAN-001 | CONVERSATIONAL_SYSTEMS_ENGINEERING | Designing any new system, module, or capability. Writing specifications before i |
| MS-PLAN-002 | MULTI_AI_ORCHESTRATION | Any high-stakes architecture decision. Any code that will govern production beha |
| MS-PLAN-003 | IMPROVEMENT_REQUEST_AS_TRAINING_SIGNAL | Every time an error is caught and fixed. Every time Boot corrects behavior. Ever |
| MS-SEE-001 | CHAT_HISTORY_BEFORE_BUILDING | Before building any engine that might have prior history. Search: 'engine_name d |
| MS-SEE-002 | RECURSIVE_MULTI_QUERY_SEARCH | Any deep research task. Any synthesis task pulling from multiple prior sessions. |
| MS-STATE-001 | KNOWLEDGE_EXTRACTION_FROM_CORPUS | After any significant development period. When trying to understand what you've  |
| MS-VERIF-001 | FAIL_TO_FIX_GATE | Every turn in production operation. Every batch in any iterative build process.  |
| MS-VERIF-002 | EXTERNAL_VALIDATOR_FOR_SELF_GENERATED_CONTENT | Before any significant claim of correctness. Before deploying any architecture.  |

### FULL PROTOCOL — KEY PATTERNS

#### MS-DIST-45ABA7 — AVOID_SEE_NO_EVIDENCE_AT_SEE
**Description:** Failure class: presence assumption without verification. At SEE in metablooms_os: check existence of required artifact/input before attempting to use it. Fail closed if absent, not with runtime error.
**Repeat when:** Before any action in SEE that could trigger SEE_NO_EVIDENCE: sie_receipts missing or empty
**Protocol:**
  - 1. Before SEE: explicitly check if required input exists
  - 2. If missing: raise named error BEFORE attempting to use it
  - 3. Report what is missing and what would satisfy the requirement
  - 4. Do not proceed without confirmed presence

#### MS-DIST-579727 — AVOID_ERAC001_AT_ERAC_SCAN
**Description:** Failure at ERAC_SCAN in erac_engine: 'ERAC-001: claimed file contains without reading'. Reasoning: this failure was not anticipated by a pre-condition check. Prevention: add explicit pre-condition check for the state that caused this error before the operation that triggered it. Fail closed on pre-condition failure rather than allowing the downstream RuntimeError.
**Repeat when:** Before any action in ERAC_SCAN that could trigger ERAC-001: claimed file contains without reading
**Protocol:**
  - 1. Identify what precondition 'ERAC-001: claimed file contains without reading' assumed
  - 2. Add explicit check for that precondition before the operation
  - 3. If precondition fails: raise named error with specific description
  - 4. Test that the check would have caught this failure

#### MS-DIST-F9D4DC — AVOID_FORGE_ERROR_AT_FORGE
**Description:** Failure at FORGE in FORGE_RUNNER: 'FORGE_ERROR: ast.parse failed on injected code'. Reasoning: this failure was not anticipated by a pre-condition check. Prevention: add explicit pre-condition check for the state that caused this error before the operation that triggered it. Fail closed on pre-condition failure rather than allowing the downstream RuntimeError.
**Repeat when:** Before any action in FORGE that could trigger FORGE_ERROR: ast.parse failed on injected code
**Protocol:**
  - 1. Identify what precondition 'FORGE_ERROR: ast.parse failed on injected code' assumed
  - 2. Add explicit check for that precondition before the operation
  - 3. If precondition fails: raise named error with specific description
  - 4. Test that the check would have caught this failure

#### MS-OS-001 — GOVERNANCE_LAYER_COMPLETENESS_CHECK
**Description:** Before any MetaBlooms OS export: run FOUR LOOPS CHECK, SIX LAYERS CHECK, BEHAVIORAL CONTRACTS CHECK, STATE ARTIFACTS CHECK. If any fails: do not ship.
**Repeat when:** Every single MetaBlooms OS export. No exceptions.
**Protocol:**

#### MS-OS-002 — THREE_HORIZON_BEFORE_EXPORT
**Description:** Before finalizing any significant output: reason at SHORT (what exists), MIDDLE (what is the gap), LONG (what does complete look like). Absence of long-horizon check = ERAC-005 risk.
**Repeat when:** Before any export, architecture decision, or significant code generation.
**Protocol:**

#### MS-OS-003 — TRY_BEFORE_REFUSE
**Description:** Before any 'I cannot do X' statement: attempt the action, get a real error, THEN report what failed with the actual error message. Untested refusals are assumptions. Tested refusals are evidence.
**Repeat when:** Any time you are about to say 'I cannot', 'I don't have access', 'X is not available'.
**Protocol:**
  - 1. Attempt the action with available tools
  - 2. If attempt fails: report 'Attempted X — failed with: [specific error]'
  - 3. Then propose the best available alternative
  - 4. Never refuse before attempting

#### MS-OS-004 — FOUR_LOOPS_CHECK_BEFORE_BOOT
**Description:** Before accepting any bundle as MetaBlooms OS and before shipping any bundle as MetaBlooms OS: verify all four loops are present. Loop 1 (Evidence): SEE present. Loop 2 (Reasoning): MPP present. Loop 3 (Memory): SESSION_HANDOFF + TURN_STATE_LEDGER present. Loop 4 (Learning): MISTAKE_REGISTRY + SUCCESS_REGISTRY present. Missing loop = partial OS. Name what is missing. Proceed accordingly.
**Repeat when:** Every boot. Every export. No exceptions.
**Protocol:**
  - Loop 1: engines/STAGES.py present? knowledge/SEE_QUERIES.json present?
  - Loop 2: engines/MPP_RUNTIME.py present?
  - Loop 3: state/SESSION_HANDOFF.json present? state/TURN_STATE_LEDGER.json present?
  - Loop 4: learning/MISTAKE_REGISTRY.json present? learning/SUCCESS_REGISTRY.json present?
  - All four: full MetaBlooms OS. Any missing: degraded mode, name what is absent.

================================================================================
PIECE 4 END | SHA-256: 9deeb477d99e49d19b5e246d9b6e02d4...
================================================================================
