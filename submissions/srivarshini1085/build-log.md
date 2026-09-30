# INBOUNDSHIELD AI — Engineering Build Log

**Author:** srivarshini1085  
**Repository:** `https://github.com/srivarshini1085/cube-01-receiving-manager`  
**Branch:** `srivarshini1085`  
**Build Window:** 25 September 2026 (9:00 AM IST) – 1 October 2026 (6:00 PM IST)

---

### Entry 1: 25 September 2026 · 10:30 AM IST
**Milestone:** Repository Setup, Domain Briefing & Finding Discovery
- Forked official repository `Cube-Build-A-Thon/cube-01-receiving-manager` to `srivarshini1085/cube-01-receiving-manager`.
- Created dedicated development branch `srivarshini1085`.
- Inspected starter structure: `backend/`, `data/receiving_sample.csv`, `RULES.md`, `README.md`.
- **Finding Identified (Rule Honesty):** `data/README.md` states that the values `uncertain` and `pending_review` appear intentionally in `receiving_sample.csv`. However, structural analysis of all 100 rows in `receiving_sample.csv` confirmed that `pending_review` never appears in the CSV header or row values. Logged finding: the application requires `pending_review` as a runtime operational state for model timeouts (Rule 3), which is decoupled from the reference dataset.
- Verified placeholder photo paths in `data/receiving_sample.csv`: 300 missing image targets. Confirmed requirement to synthesize real image fixtures for the evaluation set.

---

### Entry 2: 26 September 2026 · 3:15 PM IST
**Milestone:** Tenancy Architecture & Database Layer
- Examined Rule 1 (Tenancy Isolation) against the MySQL 8 target. Noted that MySQL 8 lacks PostgreSQL's native `FORCE ROW LEVEL SECURITY`. Designed defense-in-depth architecture:
  1. Every database model explicitly carries foreign key `organization_id`;
  2. Every API route enforces `X-Organization-Id` tenant context dependency;
  3. Every repository query binds `Model.organization_id == current_tenant_id`;
  4. Asset streaming endpoints verify tenant ownership before returning bytes.
- Configured flexible database engine in `app/core/database.py` with automatic SQLite fallback (`sqlite:///./inboundshield.db`) for zero-friction standalone execution, alongside enterprise MySQL support.
- Configured SQLAlchemy 2.0 declarative models: `Organization`, `Product`, `PurchaseOrder`, `PurchaseOrderLine`, `ReceivingInspection`, `ReceivingImage`, `InspectionCheck`, `EvidenceItem`, `EvidenceRequest`, and `OperatorOverride`.

---

### Entry 3: 27 September 2026 · 11:45 AM IST
**Milestone:** Vision Agent & Single-Call Batched Perception (Rule 2)
- Analyzed unit economics of inbound receiving at scale (10,000 units/day). Sequential LLM calls per check (8 calls per unit) would cost $36,000/month.
- Designed `VisionAgent.analyze_unit_batch()`: aggregates all available unit photographs and executes exactly **one** multimodal perception call per unit.
- Implemented perceptual extraction for corrugate crushing (contour irregularity), water damage (low-frequency dark saturation tide marks), packaging tears (Laplacian edge discontinuities), and barcode/label token decoding.

---

### Entry 4: 28 September 2026 · 4:20 PM IST
**Milestone:** Evidence Coverage Engine & Rule 4 Uncertain Handling
- Implemented `EvidenceCoverageEngine` to assess photographic sufficiency prior to decision synthesis.
- Implemented Rule 4: If an image has severe flash glare, blur, or missing required angles (e.g., unopened carton attempting to verify kit components), the engine refuses to guess. It sets the check to `UNCERTAIN` and creates a high-priority `EvidenceRequest` with concrete re-take guidance.
- Implemented Rule 3 (Fail-Open): Wrapped inspection analysis in resilient exception handling. If a model times out or errors, the capture is preserved with status `pending_review` and overall decision `UNCERTAIN`. Dock workers are never blocked.
- Implemented Rule 6 (Overrides as Data): Created `OperatorOverride` model. Overrides never delete or overwrite AI verdicts; they append to an immutable audit ledger with mandatory operator justification.

---

### Entry 5: 29 September 2026 · 6:00 PM IST
**Milestone:** Synthetic Fixture Generation & 10-Scenario Benchmark Runner
- Built `app/services/fixture_generator.py` using Pillow (PIL) to generate real, rendered photographic fixtures for all 10 problem-statement scenarios:
  1. Correct shipment (clean corrugate + valid label)
  2. Short shipment (qty 20 vs 24)
  3. Extra units (qty 30 vs 24)
  4. Wrong SKU (`SKU-WRONG-999`)
  5. Wrong variant (red towel vs blue towel)
  6. Crushed carton (collapsed corner crease)
  7. Water-damaged carton (moisture tide marks)
  8. Torn packaging (ruptured tape puncture)
  9. Missing components (whey protein tub missing scoop)
  10. Ambiguous case (severe flash glare over barcode)
- Built `ScenarioRunner` to execute all 10 scenarios and compute confusion matrices.
- *Iterative Fix:* In initial benchmark run, Scenario 5 was flagged `UNCERTAIN` because `wrong_variant_red.jpg` was typed as `other` rather than `product`. Updated image typing logic. Re-ran benchmark: **10 / 10 scenarios passed with 100% ground-truth accuracy, 0 false positives, and 0 false negatives.**

---

### Entry 6: 30 September 2026 · 5:30 PM IST
**Milestone:** Frontend Dashboard, Cross-Pod Contract & Full Test Suite
- Built modern React 19 + Vite 8 + Tailwind CSS + Lucide Icons web dashboard:
  - Live Inbound Dock Scanner with real-time PO selection, physical count attestation, and photo capture;
  - Interactive Granular Check Inspector with Expected vs. Observed comparisons;
  - Live 10-Scenario Benchmark runner displaying dynamic confusion matrices;
  - Multi-tenant switcher demonstrating live isolation between `org_demo_alpha` and `org_demo_bravo`;
  - Supervisor Override Modal recording immutable audit logs;
  - Cross-Pod Evidence Certificate viewer & JSON export.
- Resolved Pytest fixture scope and static pool configuration. Achieved **14 / 14 passing automated tests** in 1.49 seconds.
- Compiled final Round 2 submission documentation in `submissions/srivarshini1085/`.
