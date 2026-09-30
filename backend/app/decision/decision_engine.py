import hashlib
import json
from typing import Any, Dict, List
from pydantic import BaseModel

from app.verification.verification_engine import SingleCheckResult


class DecisionOutput(BaseModel):
    overall_decision: str  # PASS, FAIL, UNCERTAIN
    disposition: str      # ACCEPTED, EXCEPTION_SHORTAGE, EXCEPTION_DAMAGE, EXCEPTION_MISMATCH, etc.
    summary_rationale: str
    aggregate_confidence: float
    evidence_hash: str
    failed_checks: List[str]
    uncertain_checks: List[str]


class DecisionEngine:
    """
    Deterministic Decision Engine enforcing consistent, evidence-backed verdicts.
    Computes cryptographic tamper-evident evidence digests.
    """

    def decide(
        self,
        checks: List[SingleCheckResult],
        po_context: Dict[str, Any],
        image_checksums: List[str],
    ) -> DecisionOutput:
        failed_checks: List[str] = []
        uncertain_checks: List[str] = []
        passed_checks: List[str] = []

        total_conf = 0.0
        for c in checks:
            total_conf += c.confidence
            if c.verdict == "FAIL":
                failed_checks.append(c.check_key)
            elif c.verdict == "UNCERTAIN":
                uncertain_checks.append(c.check_key)
            else:
                passed_checks.append(c.check_key)

        avg_confidence = round(total_conf / max(1, len(checks)), 4)

        # Determine overall decision and business disposition
        if failed_checks:
            overall_decision = "FAIL"
            # Categorize primary exception
            if "SKU_IDENTITY" in failed_checks or "VARIANT_MATCH" in failed_checks:
                disposition = "EXCEPTION_MISMATCH"
                summary_rationale = f"Shipment rejected due to product identity mismatch: {', '.join(failed_checks)}."
            elif "QUANTITY_MATCH" in failed_checks or "CARTON_COUNT" in failed_checks or "UNITS_PER_CARTON" in failed_checks:
                # Check if shortage or overage
                qty_check = next((c for c in checks if c.check_key == "QUANTITY_MATCH"), None)
                if qty_check and "Overage" in qty_check.explanation:
                    disposition = "EXCEPTION_OVERAGE"
                    summary_rationale = "Shipment contains extra units/overage discrepancy."
                else:
                    disposition = "EXCEPTION_SHORTAGE"
                    summary_rationale = "Shipment short of purchase-order quantities."
            elif "CARTON_DAMAGE" in failed_checks or "UNIT_DAMAGE" in failed_checks:
                disposition = "EXCEPTION_DAMAGE"
                summary_rationale = f"Physical damage detected upon arrival: {', '.join(failed_checks)}."
            elif "COMPONENTS_CHECK" in failed_checks:
                disposition = "EXCEPTION_DEFECT"
                summary_rationale = "Shipment defective: required kit components missing."
            else:
                disposition = "EXCEPTION_OTHER"
                summary_rationale = f"Exceptions detected: {', '.join(failed_checks)}."
        elif uncertain_checks:
            overall_decision = "UNCERTAIN"
            disposition = "UNCERTAIN_PENDING_EVIDENCE"
            summary_rationale = f"Insufficient evidence to conclude authoritative decision. Open evidence requests on: {', '.join(uncertain_checks)}."
        else:
            overall_decision = "PASS"
            disposition = "ACCEPTED"
            summary_rationale = "All incoming checks verified and matched purchase order specification."

        # Compute cryptographic tamper-evident evidence hash (SHA-256)
        hash_payload = {
            "po_number": po_context.get("po_number"),
            "po_line": po_context.get("po_line"),
            "sku": po_context.get("sku"),
            "overall_decision": overall_decision,
            "disposition": disposition,
            "checks": [
                {"key": c.check_key, "verdict": c.verdict, "obs": c.observed_value}
                for c in checks
            ],
            "image_checksums": sorted(image_checksums),
        }
        canonical_json = json.dumps(hash_payload, sort_keys=True).encode("utf-8")
        evidence_hash = hashlib.sha256(canonical_json).hexdigest()

        return DecisionOutput(
            overall_decision=overall_decision,
            disposition=disposition,
            summary_rationale=summary_rationale,
            aggregate_confidence=avg_confidence,
            evidence_hash=evidence_hash,
            failed_checks=failed_checks,
            uncertain_checks=uncertain_checks,
        )
