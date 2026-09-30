# INBOUNDSHIELD AI: Project Analysis

**Status:** Repository analysis and proposed design only. No application has been implemented in this checkout.

This document separates repository-backed facts and stated project requirements from recommendations. It does not treat the synthetic CSV as real-world rules, image evidence, or evaluation ground truth.

## 1. Existing Repository Structure

The complete non-Git file inventory at analysis time is:

```text
.
|-- .github/
|   |-- CODEOWNERS
|   |-- pull_request_template.md
|   |-- scripts/submission-guard.sh
|   `-- workflows/submission-guard.yml
|-- data/
|   |-- README.md
|   `-- receiving_sample.csv
|-- submissions/
|   `-- _TEMPLATE/README.md
|-- .gitignore
|-- GITHUB-GUIDE.md
|-- README.md
|-- RULES.md
`-- docs/PROJECT_ANALYSIS.md (this document)
```

There are no application source files, test files, dependency manifests, database migrations, runtime configuration, or actual image fixtures in the checkout. `docs/PROJECT_ANALYSIS.md` is the only proposed addition in this analysis task.

## 2. Existing Functionality

**Existing repository functionality:**

- Provides the Receiving Manager problem brief, evaluation expectations, engineering rules, synthetic sample data and a participant submission template.
- Provides a GitHub Actions PR guard. For non-organiser pull requests targeting `main`, it checks that the branch matches the PR author's GitHub username and that changed paths are under `submissions/<author>/`. The action checks out the base commit and reads the PR file list; it does not run submitted application code.
- Provides CODEOWNERS and a pull-request template.
- Ignores common local environment files and generated dependency/cache directories.

There is no receiving workflow, AI integration, business-rule engine, API, UI, persistent evidence store, or automated application test suite yet.

## 3. Existing Data

`data/receiving_sample.csv` contains 100 synthetic receiving rows and is explicitly dummy data. It includes:

- Record, unit, tenant, purchase-order and line identifiers; supplier; SKU, ASIN and title.
- Expected colour, variant and components.
- Ordered/received cartons, units per carton and total quantities.
- Identity-match, carton-damage, unit-damage and quality-flag values.
- Placeholder photo references, operator IDs and UTC capture timestamps.

The two tenant IDs are `org_demo_alpha` and `org_demo_bravo`. The supplied photo references point to files that do not exist in this checkout; checking the three references per row yields 300 missing image targets. The sample is therefore structured reference data, not usable visual evidence.

Basic inspection found 100 rows; all rows satisfy `qty_received = cartons_received * units_per_carton_counted`. Across identity values there are 94 `yes`, 3 `no` and 3 `uncertain`; quantity differs from ordered quantity in 15 rows. Damage and quality values include examples of crushing, water, tears, uncertainty, wrong colour, wrong variant, missing components and obvious defects. These counts describe synthetic coverage only and are not model performance or real-world prevalence.

**Finding:** `data/README.md` says `uncertain` and `pending_review` appear on purpose, but `pending_review` does not occur in the CSV's headers or row values. The application may still need a pending processing/review state because `RULES.md` specifies it for model errors/timeouts; that is separate from the dataset. Report the reference-data inconsistency to the organisers rather than editing the official data.

No official evidence-contract artifact, organiser domain brief, or worked Returns Manager package is present in this checkout, although the top-level README refers to those materials as shared resources. Obtain them from the organisers before finalizing cross-pod integration or domain policy.

## 4. Existing Tests

There are no application tests or test runner configuration in the repository. The CSV arithmetic check above was an analysis-time consistency check, not an existing test suite. The PR guard is repository contribution validation, not application behavior validation.

## 5. Official Constraints Found in the Repository

The official repository material states the following constraints and evaluation expectations:

- Round 2 is an individual build, developed and submitted in the participant's own GitHub fork. The authorised build window begins 25 September 2026 at 9:00 AM IST; the final deadline is 1 October 2026 at 6:00 PM IST. Do not make Round 2 code changes after the build phase ends.
- Never commit secrets. Do not silently edit shared official docs or data; raise inconsistencies as findings.
- Every table must have organisation-scoped row-level security enabled and forced. Test that a second organisation sees no rows and cannot fetch another organisation's image by guessing a key.
- Batch all checks into one model call per unit, not one call per check.
- Fail open operationally: save the capture and create a `pending` record on model error or timeout; do not block the operator.
- `UNCERTAIN` is a legitimate first-class result, not a low-confidence PASS. Individual checks may be PASS, FAIL or UNCERTAIN.
- Use authoritative channel rules where published; do not let the model recall rules or infer them from the synthetic CSV.
- Preserve evidence and decision traceability. Operator overrides must retain the original verdict, replacement verdict and reason.
- Evaluation must use an unseen/held-out vision set and report methodology, per-check results, false positives, false negatives, uncertain cases and failure modes. `data/README.md` calls for 50 unseen units labelled independently by two humans.
- The submission deliverables include a working system, solution README, `ARCHITECTURE.md`, evaluation report/results, demo/video, deployment URL where applicable, and mandatory LinkedIn post URL.

**Repository workflow note:** `GITHUB-GUIDE.md` says no PR to the organiser repository is required and that participants build in their forks. The checked-in PR guard applies when a PR targets `main` and permits changes only under `submissions/<author>/`; this is repository contribution automation, not a requirement to submit the application through that PR flow. The checked-in template likewise describes a submission-folder layout. Follow the fork/submission instructions and confirm any uncertainty with organisers.

**Database compatibility risk:** the rule requires enabled and forced row-level security on every table. MySQL does not provide PostgreSQL-style native row-level security policies. Application checks, views or tenant-scoped queries alone must not be represented as satisfying that literal rule. Resolve the database/security approach with organisers before committing to MySQL for production; see the proposed model below.

## 6. Required Inputs

### Stated or supplied by the repository

- Purchase-order line expectations: item identity, agreed spec, carton count, units per carton and ordered quantity.
- Receiving photographs and receiving context (unit/PO-line association, capture time and operator/tenant context).
- The official evidence contract, once obtained, for downstream interoperability.

### Proposed application inputs, to confirm during implementation

- Authenticated organisation and operator context; never accept tenant identity solely from an untrusted request body.
- A selected PO line and its authoritative expected attributes, sourced from an operator-provided or integrated PO record.
- One or more receiving photos with capture metadata. The photo-taking workflow should request specific views when current coverage is insufficient.
- Physical counts entered or confirmed by the operator where a photograph cannot reliably establish carton or unit counts. Do not treat image estimates as exact counts without a validated method.

The source repository does not specify an actual PO integration, authentication provider, image limits, retention policy, or evidence-contract schema.

## 7. Required Outputs

### Stated outcomes

- An overall receiving outcome: `PASS`, `FAIL` or `UNCERTAIN`.
- Individual check outcomes with supporting findings. `UNCERTAIN` must remain available when evidence is insufficient.
- A traceable record of what was expected, what was inspected, observations, checks, decision and rationale.

### Proposed record fields

- Processing state (`pending`, `completed`, or an explicitly defined error/review state) independently of business verdict.
- Per-check outcome, evidence references, observation and rationale; missing-evidence items and recommended next photo when useful.
- Model/version and request metadata sufficient for diagnosis, timestamps, content hashes where useful, and complete operator override history.

Do not collapse `pending` processing state into `UNCERTAIN`: a failed/timed-out model call still saves the capture and a pending record under the official fail-open rule.

## 8. Required Inspection Checks

The user-provided project brief requires inspection of:

- Product/SKU identity against the PO.
- Expected versus observed quantity, carton count and units per carton.
- Visible carton damage and visible product damage, including crushing, water damage and tears.
- Wrong colour, wrong variant, missing components and other obvious quality issues.

The repository additionally structures product identity, colour, variant and component expectations and damage/quality flags in the sample CSV. These dummy labels illustrate data shape only. A check should return UNCERTAIN if its required evidence is absent, obstructed, ambiguous or outside validated capability.

## 9. Existing Reusable Components

- `data/receiving_sample.csv` can inform field names, relational joins, sample UI states and basic deterministic test cases. It is not production data, image fixtures, ground truth or an evaluation set.
- `data/README.md` documents the sample columns and cross-manager `unit_id` join.
- `submissions/_TEMPLATE/README.md` lists proposed participant deliverables, including a contract directory, headless agent, evaluation report and evidence-record page.
- The GitHub workflow, script, CODEOWNERS and PR template can be retained as repository governance if the participant continues using the same fork workflow.
- `.gitignore` already excludes common secret and generated files. It does not replace secret handling, access control, or image-storage protections.

No application module or test helper is currently reusable because none is present.

## 10. What We Need to Build

**Proposed functionality, not existing functionality:**

1. A receiving capture workflow that associates photos and operator-confirmed counts with an organisation and PO line.
2. Private image storage and durable evidence/receiving records, including safe behavior when AI processing is unavailable.
3. A vision observation layer that extracts only visible facts and references the images supporting them.
4. Evidence coverage logic that identifies which checks are supportable, which are not, and the next useful photograph to request.
5. Deterministic PO comparisons and a decision layer that produces PASS, FAIL or UNCERTAIN without inventing evidence.
6. A record/review interface, including original and overridden decisions with reasons.
7. A held-out evaluation set, independent labels, automated tests and a reproducible evaluation report.
8. An agreed evidence contract and system documentation/demo/deployment artifacts required for submission.

## 11. Potential Risks

- **Security-rule versus MySQL mismatch:** literal mandatory RLS may not be satisfiable with the desired database. This is a pre-implementation decision, not a detail to defer.
- **Image coverage:** the sample contains no images. Vision quality cannot be assessed until representative, consented fixtures are collected and labelled.
- **Visual ambiguity:** SKU identity, subtle variants, colour under different lighting, hidden components and exact counts may not be reliably inferable from ordinary photos. Ask for targeted images or operator counts; abstain when still ambiguous.
- **Visible-only inspection:** photographs cannot establish hidden/internal defects or guarantee product quality. State this limitation in records and UX.
- **False assurance:** bad evidence or confident model errors can create costly supplier disputes. Keep observation and decision separate, preserve provenance, and make uncertainty operationally visible.
- **Synthetic-data contamination:** using the CSV as training/evaluation ground truth would produce misleading results; its values are explicitly dummy labels.
- **Counting scope:** a pallet/carton photo may not show every unit. Reconcile entered physical counts deterministically and identify the source of each count.
- **PO/spec authority:** no PO source or authoritative channel rules are supplied. Avoid treating sample expectations as official business policy.
- **Fail-open semantics:** saving captures on timeout must not accidentally present an incomplete result as a completed PASS/FAIL.
- **Privacy and retention:** receiving photos can contain people, labels or commercially sensitive details. The repository specifies no consent, access, retention or deletion policy; decide these before deployment.
- **Cross-manager integration:** the official evidence contract is not included in the checkout, so schema compatibility cannot yet be verified.
- **Evaluation validity:** a small held-out set can reveal failure modes but may not represent product/catalogue diversity. Report per-check denominators and limitations honestly.

## 12. Recommended Architecture

Use explicit boundaries that match the requested four responsibilities plus durable recording:

```text
Capture/API
  -> Evidence store and receiving record (persist first)
  -> Vision observation (one batched model request per unit)
  -> Evidence coverage (check-specific sufficiency and next-photo guidance)
  -> Deterministic verification (PO/count/spec comparisons)
  -> Decision policy (PASS / FAIL / UNCERTAIN)
  -> Evidence record and review UI
```

1. **Vision observation:** accept the expected PO-line context and all photos for the unit in one model request. Return a strict, schema-validated observation payload, with per-observation photo references, locations when available, confidence/limitations, and no final business verdict.
2. **Evidence coverage:** map required checks to required views/data. Mark each as sufficient, missing or ambiguous. Generate a specific next-photo instruction from the gap, such as a clear label close-up or an opened-carton component layout. Do not ask for a generic retake when a more targeted view is possible.
3. **Deterministic verification:** compare structured observations and operator-entered measurements against the PO line and explicit policies. Derive arithmetic quantities in application logic and flag inconsistent inputs. Use authoritative rules only when provided.
4. **Decision making:** combine check outcomes with a documented policy. Any material unresolved check prevents an unsupported overall PASS; evidence of a mismatch/defect can support FAIL; insufficient or conflicting evidence yields UNCERTAIN. Specify aggregation rules before implementation.
5. **Evidence recording:** persist capture before asynchronous AI work; record source images, hashes, observations, coverage, check results, final verdict, processing state, model metadata and override history. A hash aids integrity checks but is not itself proof of immutable/tamper-evident storage.

Keep model failure independent from the operator's receiving flow. Save the record as `pending`, make retry/review possible, and never substitute a fabricated result.

## 13. Recommended MySQL Data Model

The following is a **proposed logical model**, not an existing schema. Use InnoDB, UTC timestamps, explicit foreign keys, stable IDs, and `org_id` on every tenant-owned row. Enforce tenant-matched references with composite unique keys/foreign keys such as `(org_id, id)` so records cannot reference another tenant's objects.

- `organizations`: tenant identity and lifecycle metadata.
- `operators`: organisation-scoped user/operator identity, linked to the authentication subject.
- `purchase_orders`: organisation-scoped PO header and supplier/reference fields.
- `purchase_order_lines`: PO line, SKU/identifiers, agreed colour/variant/components and expected carton/unit quantities. Store authoritative source/version metadata if connected to an external system.
- `receiving_records`: one receiving workflow/decision record, linked to tenant, PO line, unit identifier and operator; includes received counts, processing state, overall verdict, timestamps and version.
- `evidence_assets`: receiving record, object-storage key, media type/size, capture metadata, content hash, upload/processing status and access metadata. Keep image bytes in private object storage rather than MySQL blobs unless deployment constraints require otherwise.
- `vision_runs`: record, model/provider/version, request status, timing, structured response and error details. Avoid retaining unnecessary sensitive prompt/image copies.
- `observations`: vision observations with attribute, normalized value, confidence, supporting asset(s)/regions and schema/version metadata.
- `check_results`: per-check outcome, expected/observed values, rationale, evidence coverage status and next-photo recommendation.
- `decision_events`: append-only decision changes with verdict, policy version, actor/source and reason.
- `operator_overrides`: original outcome, replacement outcome, operator and mandatory reason; do not overwrite the original decision.
- `evaluation_cases` and `evaluation_labels`: isolated evaluation-only fixtures and independent human labels, separate from production records.

Suggested uniqueness/index patterns include `(org_id, record_id)`, `(org_id, po_number, po_line)`, `(org_id, unit_id)`, and indexes supporting tenant-scoped recent-record queries. Avoid globally guessable image keys; authorize every image read against the owning tenant and record.

**Mandatory security gate:** MySQL has no native PostgreSQL-style row-level security policy mechanism. MySQL tenant scoping can be strengthened with composite foreign keys, restricted DB accounts, tenant-scoped views/procedures, and mandatory authorization in the service, but do not claim these meet the repository's explicit “row-level security enabled and forced” requirement without organiser approval. Prefer a database with enforceable native RLS if the rule is literal; otherwise obtain a written, accepted MySQL-equivalent interpretation before selecting MySQL. In either case, test cross-tenant record and guessed-image-key access.

## 14. Recommended API Structure

Proposed REST shape; exact naming and the external evidence schema remain to be agreed:

- `POST /api/v1/receivings` — create a receiving record for a PO line and operator-confirmed quantities; return the record ID and upload instructions.
- `POST /api/v1/receivings/{id}/evidence` — upload/register one or more photos and metadata, bound to authenticated tenant context.
- `POST /api/v1/receivings/{id}/analyze` — enqueue a single batched analysis for all current unit evidence; return `pending` promptly.
- `GET /api/v1/receivings/{id}` — retrieve expected values, processing state, observations, evidence coverage, checks and decision.
- `POST /api/v1/receivings/{id}/evidence-requests/{requestId}/complete` — attach a requested follow-up image and resume analysis/review.
- `POST /api/v1/receivings/{id}/overrides` — record an authorized human override with original verdict, replacement and reason.
- `GET /api/v1/receivings` — list/search records within the authenticated organisation.
- `GET /api/v1/receivings/{id}/evidence/{assetId}` — authorize then serve a short-lived private image URL or stream.
- `GET /health` — service health, without exposing tenant data or secrets.

Validate payloads and file limits; derive tenant identity from authentication; make create/upload/analyze operations idempotent where practical; return stable error codes. Do not expose public image URLs or accept arbitrary object keys from clients.

## 15. Recommended Frontend Structure

Proposed operator workflow:

- **Receiving queue:** searchable records and clear `pending`, `PASS`, `FAIL`, `UNCERTAIN` states.
- **Start receiving:** select PO/line, confirm expected line details and enter observed carton/unit counts.
- **Evidence capture:** camera/upload flow with view labels (pallet/carton/product/label/components), preview and retake controls.
- **Evidence coverage:** per-check coverage and concise missing-evidence guidance with a concrete next-photo action.
- **Decision record:** expected versus observed facts; per-check statuses; source-photo links; rationale; model processing state; final outcome.
- **Human review:** retry pending cases, capture requested evidence and submit reasoned overrides while retaining original decisions.
- **History/export:** tenant-scoped receiving records and evidence-contract export for downstream consumers.

Keep incomplete processing visibly distinct from a completed UNCERTAIN verdict. Avoid presenting confidence as proof or hiding which observations came from vision versus operator input or deterministic calculation.

## 16. Recommended AI Architecture

- Use the model as a structured visual observer, not the authority for PO arithmetic, rules or final verdicts.
- Send all relevant images and all visual checks for a unit in one batched model request, in line with the repository rule. Include the PO/spec context needed to identify visual mismatches, but require observed attributes to be grounded in a cited image.
- Require structured output validated against a versioned schema. Represent “not visible”, “ambiguous”, “not applicable” and observed defect states explicitly; never translate missing evidence into “none”.
- Keep evidence coverage separate from model confidence. Evaluate whether each required check has the kind of view needed, and request targeted new photos when absent.
- Perform exact quantity arithmetic and structured comparisons in deterministic code. Preserve the source of each expected/observed value.
- Use conservative check-level abstention. Overall PASS requires sufficient support for all required checks under an explicit policy; unresolved material checks produce UNCERTAIN. A well-supported negative finding can produce FAIL.
- Persist captures before calling the model. On timeout/error persist `pending`; permit retry and operator review without blocking the line.
- Version prompts, model identifier, schema and decision policy in trace records. Redact secrets and minimize sensitive image/prompt retention.
- Measure every claimed capability against held-out labeled evidence. Do not train on or validate against the dummy CSV as if its values were truth.

## 17. Recommended Evaluation Architecture

Create a separate, access-controlled image fixture set with unit-level splits and no overlap between development and held-out evaluation. The repository's data README specifies 50 unseen units, each labeled independently by two humans; resolve disagreements with a documented adjudication process and retain both initial labels.

For each check (identity, carton count, units/carton, quantity, carton damage, product damage, colour, variant, components and other defects), report:

- Number of cases and label distribution; annotator agreement and adjudication method.
- PASS/FAIL/UNCERTAIN predictions, confusion matrix, false-positive and false-negative counts/rates with denominators.
- Coverage/abstention rate and performance on cases where the model does make a judgment.
- Failure modes grouped by evidence condition (missing/obstructed/poorly lit/ambiguous) and product/check category.
- End-to-end latency, model calls per unit, failure/pending rate and estimated per-unit model cost.

Evaluate next-photo recommendations separately: whether the requested view targets an actual evidence gap and whether the follow-up photo resolves it. Include model timeout/error cases to verify fail-open persistence, tenant isolation cases for record and image retrieval, deterministic quantity tests, and decision/override audit tests. Freeze the held-out set and methodology before tuning against it. Publish measured results and limitations; do not prestate targets as achieved results.

## Phased Implementation Plan

1. **Resolve constraints and contracts:** confirm the official evidence contract, obtain missing domain/reference documents, report the `pending_review` dataset discrepancy, and get an organiser-approved database/RLS interpretation. Define explicit PASS/FAIL/UNCERTAIN aggregation and authoritative policy sources.
2. **Define evidence and evaluation:** design the versioned record/observation/check schemas; collect representative photo fixtures; define two-labeler protocol, held-out split and privacy/retention approach.
3. **Build secure persistence and capture:** implement authentication/tenant enforcement, PO-line/receiving records, private image storage and durable fail-open `pending` capture. Test cross-tenant record and guessed-image access before feature work proceeds.
4. **Build the headless verification pipeline:** add batched vision observations, evidence coverage and targeted photo requests, deterministic comparisons, decision policy, retries and audit-preserving overrides.
5. **Build the operator interface and contract export:** implement queue, capture, evidence-gap, decision/review and history views; validate downstream evidence-contract compatibility.
6. **Validate and evaluate:** run focused unit/integration/security tests, then the frozen held-out evaluation; report per-check metrics, FP/FN, uncertainty, failure modes, latency/cost and limitations.
7. **Prepare submission:** complete README and `ARCHITECTURE.md`, evaluation report, demo/video, deployment URL where appropriate, mandatory LinkedIn post and final submission checks before the published deadline.