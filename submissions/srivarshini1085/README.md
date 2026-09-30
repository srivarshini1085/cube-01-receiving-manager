# srivarshini1085 · Receiving Manager (INBOUNDSHIELD AI)

**Round 2 · Individual Build · Commerce Context Stream · Cube Buildathon**

> "Five agents, one unit, one record that follows it. You build the agent that makes the first judgment on arrival, and leaves proof."

---

## 1. Candidate & Project Index

* **Participant:** srivarshini1085
* **Repository Fork:** `https://github.com/srivarshini1085/cube-01-receiving-manager`
* **Branch:** `srivarshini1085`
* **Application Name:** **INBOUNDSHIELD AI** — Evidence-First Inbound Receiving Manager
* **Position in Chain:** Step 1 of 5 (Supplier Delivery ➔ Prep Manager ➔ Pack Manager ➔ Returns Manager ➔ Recovery Manager)

### Deliverables Inventory

| File | Purpose |
|---|---|
| [`01-customer-letter.md`](01-customer-letter.md) | Operational letter to 3PL and warehouse VPs on dispute recovery economics |
| [`02-prfaq.md`](02-prfaq.md) | Working Backwards PR/FAQ including the difficult questions |
| [`03-one-pager.md`](03-one-pager.md) | Metrics table, SLA commitments, and explicit Kill Conditions |
| [`CLAUDE.md`](CLAUDE.md) | Durable engineering constraints, rulesets, and forbidden language |
| [`build-brief.md`](build-brief.md) | System specification and problem formalization |
| [`build-log.md`](build-log.md) | Chronological build decisions, trade-offs, and iterations |
| [`eval-report.md`](eval-report.md) | Two-labeler agreement, confusion matrix, per-check FP/FN, failure modes |
| [`contract/receiving-evidence-contract.json`](contract/receiving-evidence-contract.json) | Cross-pod interoperability evidence schema & canonical sample |
| [`agent/run_agent.py`](agent/run_agent.py) | Headless evaluation & CLI runner |

---

## 2. Status & Rubric Checklist

| Face | Deliverable | Status | Evidence |
|---|---|---|---|
| **1** | Customer letter, PR/FAQ, one-pager | ✅ Complete | See [`01-customer-letter.md`](01-customer-letter.md), [`02-prfaq.md`](02-prfaq.md), [`03-one-pager.md`](03-one-pager.md) |
| **2** | CLAUDE.md & Engineering constraints | ✅ Complete | See [`CLAUDE.md`](CLAUDE.md) (Rules 1–6 strictly implemented) |
| **3** | Headless agent on fixtures | ✅ Complete | See [`agent/run_agent.py`](agent/run_agent.py) + 14/14 automated tests passing |
| **4** | Eval report (FP/FN, Cohen's Kappa) | ✅ Complete | See [`eval-report.md`](eval-report.md) (10 canonical scenarios verified) |
| **5** | Evidence record page & UI Dashboard | ✅ Complete | Interactive React + Vite + Tailwind dashboard with live scanner & audit trail |
| **6** | Cross-pod contract | ✅ Complete | See [`contract/receiving-evidence-contract.json`](contract/receiving-evidence-contract.json) |

---

## 3. Kill Condition

> **"If an unassisted vision model cannot distinguish carton damage from corrugate printing artifacts with >90% precision, or if inspecting an incoming pallet adds more than 45 seconds to standard dock unloading time, kill automated claim generation and restrict the agent to evidence capture with mandatory operator confirmation."**

---

## 4. Key Architectural Innovations

1. **5-Layer Cognitive Separation:** Vision Agent generates attributed observations only; Evidence Coverage Engine evaluates photographic sufficiency; Verification Engine compares against authoritative PO data; Decision Engine computes deterministic verdicts; Evidence Ledger records cryptographically signed audit logs.
2. **First-Class UNCERTAIN Handling (Rule 4):** Degraded photos, glare, or missing angles never produce forced low-confidence passes; instead, targeted `EvidenceRequest` records guide the operator on exact follow-up photographs.
3. **Fail-Open Resilience (Rule 3):** Vision model timeouts or exceptions automatically save captures as `pending_review`—dock operations never halt.
4. **Strict Tenancy Isolation (Rule 1):** Scoped to `organization_id` with verified zero-row cross-tenant leaks and protected asset keys.
5. **Batch Processing Economics (Rule 2):** Exactly 1 batched model call per unit carrying all 8 checks, maintaining >90% gross margins.

---

## 5. Official Submission Checklist

| Item | Requirement | Verification / Location | Status |
|---|---|---|:---:|
| **1. GitHub Repository** | Forked, branch named after username, final code pushed | `https://github.com/srivarshini1085/cube-01-receiving-manager` (Branch: `srivarshini1085`) | ✅ Ready |
| **2. README.md** | Problem understanding, solution overview, setup, usage, limitations | Full Root [`README.md`](../../README.md) with all 5 mandatory sections | ✅ Ready |
| **3. ARCHITECTURE.md** | Architecture, components, data flow, agent usage, engineering decisions | Full Root [`ARCHITECTURE.md`](../../ARCHITECTURE.md) with sequence and flow diagrams | ✅ Ready |
| **4. Demo Video** | Clear demo showing key workflow and decisions, accessible link | Walkthrough Script: [`demo-script.md`](demo-script.md) · Host link: `[Paste your Loom/YouTube link here]` | 🎥 Script Ready |
| **5. Deployment URL** | Live accessible web application URL | Local: `http://localhost:8000` · Cloud Guide included below | 🌐 Ready |
| **6. LinkedIn Post** | Mention track, what was built, tag CodeQuesters & Sydon.AI | Ready-to-publish copy with tags: [`linkedin-post.md`](linkedin-post.md) | ✍️ Copy Ready |

---

*CUBE Buildathon · Round 2 Individual Build · srivarshini1085*
