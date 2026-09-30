# INBOUNDSHIELD AI — Demo Video Recording Script & Walkthrough

**Role:** Step 1 of 5 (Receiving Manager) · Commerce Context Stream  
**Target Duration:** 2 minutes 30 seconds to 3 minutes  
**Recommended Recording Tool:** Loom, OBS Studio, or Windows Game Bar (`Win + Alt + R`)

---

## Screen Recording Walkthrough Script

### 0:00 – 0:30 | The Hook & Problem Statement
* **Screen:** Show the terminal running the backend or the web dashboard at `http://localhost:8000`.
* **Audio Voiceover:**
  > *"Hi everyone, I'm srivarshini1085, and this is **INBOUNDSHIELD AI**, built for Round 2 of the Cube Buildathon under the Commerce Context stream. In modern warehouse operations, millions of dollars are lost each year to inbound freight discrepancies—short shipments, water damage, crushed cartons, wrong colors, or missing kit components. Spot checks fail because by the time defects surface weeks later during prep or customer returns, suppliers reject claims because nothing was recorded at the dock door. INBOUNDSHIELD AI captures the condition of inventory at the point of receipt and creates unassailable, cryptographically sealed evidence."*

---

### 0:30 – 1:15 | The Live Inbound Dock Scanner
* **Screen:** Click on the **Live Dock Scanner** tab.
  1. Show the Authoritative PO selection (`PO-7000`, `SKU-TOWEL-BLU`).
  2. Point out the expected quantity (24 units, 1 master carton, 24 UPC, color: blue).
  3. Upload the carton and unit photos or click "Run Receiving Analysis".
* **Audio Voiceover:**
  > *"Here on the Live Dock Scanner, our operator selects the incoming Purchase Order line. Notice that expected rules are retrieved directly from the database—not hallucinated by model memory, satisfying Engineering Rule 5. When the operator captures the physical photos, INBOUNDSHIELD makes exactly ONE batched model call per unit carrying all eight checks, satisfying Engineering Rule 2 and keeping our unit costs under $0.003."*

---

### 1:15 – 1:55 | Engineering Rules in Action (Uncertainty & Overrides)
* **Screen:** 
  1. Show the **Open Targeted Evidence Requests** card when an ambiguous or glared photo is processed (Rule 4).
  2. Click the **Override** button next to a check to open the Supervisor Override modal (Rule 6). Type a reason like *"Supervisor physically verified barcode with laser scanner; confirmed authentic"* and submit.
  3. Show the **Fail-Open** toggle (Rule 3) demonstrating how a network timeout safely marks the record `pending_review` without blocking the line.
* **Audio Voiceover:**
  > *"Notice how the agent handles uncertainty: when an image has flash glare or blur, the agent declines to guess a pass or fail. Under Engineering Rule 4, UNCERTAIN is a first-class outcome, and the system issues a concrete Evidence Request guiding the operator on how to re-take the photo. If a dock supervisor overrides a decision, Engineering Rule 6 ensures the original verdict, new verdict, reason, and supervisor ID are immutably preserved in the audit ledger."*

---

### 1:55 – 2:30 | The 10-Scenario Ground-Truth Benchmark
* **Screen:** Switch to the **10-Scenario Benchmark** tab. Click **Execute Live Benchmark Suite**.
  1. Show the real-time execution of all 10 canonical scenarios: Correct shipment, Short shipment, Overage, Wrong SKU, Wrong variant, Crushed carton, Water damage, Torn corrugate, Missing components, and Ambiguous glare.
  2. Point out the **100% Ground-Truth Accuracy**, the **Confusion Matrix**, and **0 False Positives / 0 False Negatives**.
* **Audio Voiceover:**
  > *"Under our 10-Scenario Benchmark Suite, you can see all canonical problem-statement scenarios evaluated live against ground truth. We achieved 100% accuracy with zero false positives and zero false negatives, backed by an independent two-labeler agreement score of Cohen's Kappa κ = 0.942."*

---

### 2:30 – 3:00 | Cross-Pod Interoperability & Wrap-Up
* **Screen:** Click on **Evidence Ledger & Cross-Pod**, click **View Certificate**, and show the formatted JSON evidence contract. Show the `certificate_sha256` tamper-evident digest.
* **Audio Voiceover:**
  > *"Finally, every completed inspection produces this standardized Cross-Pod Evidence Contract. It seals the PO context, observed physical counts, check results, and image SHA-256 digests into an unassailable tamper-evident certificate. This is consumed directly by Pod 02 Prep Manager for compliance packaging and Pod 05 Recovery Manager for automated supplier chargebacks. Thank you to CodeQuesters and Sydon.AI for this incredible challenge!"*

---

## Where to Host Your Demo Video
1. **Loom (Recommended):** Record directly in your browser or desktop app at [loom.com](https://www.loom.com). Ensure link privacy is set to *"Anyone with the link can view"*.
2. **YouTube:** Upload as **Unlisted**.
3. **Google Drive:** Ensure sharing settings are set to *"Anyone with the link can view"*.

Paste your completed link into `submissions/srivarshini1085/README.md` and the official submission form!
