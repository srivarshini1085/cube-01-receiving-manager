# INBOUNDSHIELD AI — Official Judge Demo Guide

This document outlines the step-by-step demonstration flow for CUBE hackathon judges.

---

## 1. Quick 5-Scenario Walkthrough

### Scenario 1: Clean Shipment (Ideal Path)
* **Goal:** Verify compliant delivery advances cleanly to Pod 02 (Prep).
* **Steps:**
  1. Go to **Operational Dashboard** or **New Inbound Inspection**.
  2. Select **Canonical Scenario 1 (Clean Shipment)**.
  3. System runs batched verification in ~1.4s.
  4. Banner turns **EMERALD PASS**; all 8 checks show `PASS` with $>90\%$ confidence.
  5. Click **View Sealed Contract** to inspect the SHA-256 evidence certificate.

### Scenario 2: Short Shipment (Dispute Recovery)
* **Goal:** Catch physical shortage before signing Bill of Lading.
* **Steps:**
  1. Click **Scenario 2 (Short Shipment)**.
  2. Expected quantity = 24; Operator counted = 20.
  3. Result: **EXCEPTION — EXCEPTION_SHORTAGE**.
  4. Shows discrepancy units: `-4 units`. Evidence certificate is ready for Pod 05 Recovery.

### Scenario 3: Physical Corrugate Damage (Crushing / Moisture)
* **Goal:** Detect transit damage at point of unloading.
* **Steps:**
  1. Click **Scenario 6 (Crushed Master Carton)** or **Scenario 7 (Water Stained)**.
  2. Vision agent detects edge contour crushing / moisture tide lines.
  3. Result: **EXCEPTION — EXCEPTION_DAMAGE**.
  4. Click on the check to view the highlighted damage photograph and SHA-256 seal.

### Scenario 4: The Round 3 Differentiator — UNCERTAIN & Next-Best-Evidence
* **Goal:** Demonstrate that the agent refuses to hallucinate when evidence is degraded, and guides the operator on the exact follow-up photo needed.
* **Steps:**
  1. Click **Scenario 10 (Ambiguous Glared Barcode)**.
  2. Banner turns **AMBER UNCERTAIN**.
  3. The **Next-Best-Evidence Card** appears:
     * *Why?* "Extreme specular glare washes out barcode lines."
     * *Missing Evidence:* "Legible barcode or shipping label."
     * *Recommended Next Photo:* "Capture label with diffused lighting to avoid flash reflections."
  4. Click **Upload Recommended Photo** and attach a clear label.
  5. Click **Run Receiving Analysis** to complete the re-inspection loop. Check transitions to `PASS`!

### Scenario 5: Supervisor Override (Rule 6 Compliance)
* **Goal:** Show that human overrides append to the audit ledger without overwriting history.
* **Steps:**
  1. On any completed inspection, click **Supervisor Override**.
  2. Select a replacement verdict (e.g. `PASS`).
  3. Enter mandatory reason: *"Supplier commercial credit pre-arranged for crushed corrugate"*.
  4. Submit. The override record is appended to the ledger with the supervisor's ID and timestamp.
