# CLAUDE.md — Durable Engineering Constraints & Operational Rules

**Repository:** `https://github.com/srivarshini1085/cube-01-receiving-manager`  
**System:** INBOUNDSHIELD AI (Step 1: Receiving Manager)  
**Author:** srivarshini1085  

This document defines the non-negotiable engineering rules, operational invariants, and linguistic standards governing the development, testing, and operation of INBOUNDSHIELD AI.

---

## 1. Non-Negotiable Engineering Rules (Enforced & Tested)

### Rule 1: Tenancy Isolation Before Any Feature
- **Constraint:** Every database table must carry an indexed `organization_id` foreign key.
- **Enforcement:** Every API request must resolve and enforce `X-Organization-Id`. No endpoint may return rows across tenant boundaries.
- **Asset Protection:** Image assets in object storage cannot be accessed via guessable keys or sequential IDs. Image downloads require tenant-authorized routes verifying that the requesting tenant owns the parent inspection.
- **Testing:** Automated tests must verify that Tenant B (`org_demo_bravo`) sees 0 rows when Tenant A (`org_demo_alpha`) has records, and returns HTTP 404 when requesting Tenant A's image UUIDs.

### Rule 2: Batch Your Model Calls
- **Constraint:** Make exactly **ONE** multimodal model call per unit carrying all eight checks. Never make one call per check.
- **Enforcement:** The Vision Agent aggregates all available photographs for a unit and submits a single unified perception request.
- **Economic Invariant:** Operating cost per inbound unit must remain strictly below $0.010 USD.

### Rule 3: Fail Open
- **Constraint:** A model error, network timeout, or downstream API degradation must never block the receiving dock line.
- **Enforcement:** If inference fails or times out, the system immediately persists the raw photographs, creates an inspection record marked `pending_review`, sets overall decision to `UNCERTAIN`, and queues an asynchronous background re-try.
- **Operational Invariant:** Forklift operators and dock workers are never forced to wait on cloud AI.

### Rule 4: UNCERTAIN is a Valid Verdict
- **Constraint:** `UNCERTAIN` is an intentional, first-class outcome—not a low-confidence `PASS`.
- **Enforcement:** When an image is degraded by glare, blur, occlusion, or missing angles, the engine declines to guess. It flags the check as `UNCERTAIN` and generates a structured `EvidenceRequest` containing:
  - `reason`: The exact degradation cause (e.g. flash glare over barcode).
  - `missing_evidence`: What specific angle or detail is missing.
  - `recommended_photograph`: Concrete instructions for the operator.

### Rule 5: Look Authoritative Rules Up
- **Constraint:** The model must never guess or recall purchase order specifications, carton counts, or catalog attributes from memory.
- **Enforcement:** Authoritative expectations (SKU, ASIN, ordered quantity, cartons, units per carton, expected color, variant, and kit components) must be retrieved directly from the tenant's database records.

### Rule 6: Overrides Are Data
- **Constraint:** When a human supervisor disagrees with an AI verdict, the original verdict must never be overwritten or discarded.
- **Enforcement:** An override appends an immutable record to the `operator_overrides` ledger containing:
  - `original_verdict`
  - `new_verdict`
  - `reason` (mandatory, minimum 5 characters)
  - `operator_id`
  - `timestamp` (UTC)

---

## 2. Forbidden Language & Honesty Rules

To maintain absolute credibility with operations executives, logistics engineers, and hackathon evaluators, the following linguistic rules are strictly enforced across code, documentation, and user interfaces:

| Forbidden Claim | Why It Is Prohibited | Required Replacement |
|---|---|---|
| *"100% Autonomous"* | Deceitful. Humans unload, count, and override edge cases. | *"Semi-autonomous with human-in-the-loop auditability"* |
| *"Hallucination-free AI"* | Statistically untrue for any probabilistic vision model. | *"Deterministic verification engine checking grounded observations"* |
| *"The AI counted all units inside the box"* | Physically impossible through opaque corrugate. | *"Operator-attested count verified against carton packaging rules"* |
| *"Blockchain-secured"* | It is a SHA-256 cryptographic digest, not a blockchain. | *"SHA-256 tamper-evident evidence digest"* |
| *"It works well"* | Vague and subjective. | *"100% accuracy on 10 canonical scenarios with 0 false positives"* |

---

## 3. Cryptographic & Evidence Invariants

1. **SHA-256 Chained Integrity:** Every inspection record produces a tamper-evident digest computed over:
   $$\text{SHA256}(\text{PO Number} \parallel \text{SKU} \parallel \text{Overall Verdict} \parallel \text{Sorted Checks} \parallel \text{Sorted Image Hashes})$$
2. **Canonical Contract Interoperability:** All exports must match the agreed cross-pod evidence schema consumed by Pod 02 (Prep) and Pod 05 (Recovery).
3. **UTC Timestamps:** All database timestamps are explicitly recorded in ISO-8601 UTC.
