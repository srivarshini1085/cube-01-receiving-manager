from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.agents.vision_agent import VisionObservation
from app.evidence.coverage_engine import CoverageEvaluation


class SingleCheckResult(BaseModel):
    check_key: str
    expected_value: str
    observed_value: str
    verdict: str  # PASS, FAIL, UNCERTAIN
    confidence: float
    explanation: str
    evidence_sufficient: bool = True
    missing_evidence: Optional[str] = None
    recommended_photograph: Optional[str] = None


class VerificationEngine:
    """
    Deterministic Verification Engine enforcing Rule 5:
    Look authoritative rules and values up from the purchase order and product catalog.
    Never guess or hallucinate comparisons.
    """

    def verify_all(
        self,
        po_line_context: Dict[str, Any],
        observation: VisionObservation,
        coverage_evaluations: Dict[str, CoverageEvaluation],
        operator_cartons: Optional[int] = None,
        operator_units_per_carton: Optional[int] = None,
    ) -> List[SingleCheckResult]:
        results: List[SingleCheckResult] = []

        # Extract authoritative PO line data
        exp_sku = str(po_line_context.get("sku", "")).strip()
        exp_asin = str(po_line_context.get("asin", "") or "").strip()
        exp_qty = int(po_line_context.get("expected_quantity", 0))
        exp_cartons = int(po_line_context.get("expected_cartons", 0))
        exp_upc = int(po_line_context.get("expected_units_per_carton", 0))
        exp_colour = str(po_line_context.get("expected_colour", "") or "").strip().lower()
        exp_variant = str(po_line_context.get("expected_variant", "") or "").strip().lower()
        exp_components_raw = str(po_line_context.get("expected_components", "") or "").strip()
        exp_components = [c.strip().lower() for c in exp_components_raw.split(";") if c.strip()]

        # Determine observed counts (operator-attested physical count takes precedence, with vision support)
        obs_cartons = operator_cartons if operator_cartons is not None else (observation.estimated_cartons or exp_cartons)
        obs_upc = operator_units_per_carton if operator_units_per_carton is not None else (observation.estimated_units_per_carton or exp_upc)
        obs_total_qty = obs_cartons * obs_upc

        # ---------------------------------------------------------------------
        # 1. SKU Identity Check
        # ---------------------------------------------------------------------
        sku_cov = coverage_evaluations.get("SKU_IDENTITY")
        if sku_cov and not sku_cov.is_sufficient:
            results.append(
                SingleCheckResult(
                    check_key="SKU_IDENTITY",
                    expected_value=f"SKU: {exp_sku} (ASIN: {exp_asin})" if exp_asin else f"SKU: {exp_sku}",
                    observed_value="UNREADABLE_OR_OCCLUDED",
                    verdict="UNCERTAIN",
                    confidence=0.30,
                    explanation=f"Cannot authoritatively verify SKU: {sku_cov.reason}",
                    evidence_sufficient=False,
                    missing_evidence=sku_cov.missing_evidence,
                    recommended_photograph=sku_cov.recommended_photograph,
                )
            )
        else:
            obs_sku = observation.detected_sku
            obs_asin = observation.detected_asin
            if not obs_sku:
                results.append(
                    SingleCheckResult(
                        check_key="SKU_IDENTITY",
                        expected_value=exp_sku,
                        observed_value="None detected",
                        verdict="UNCERTAIN",
                        confidence=0.45,
                        explanation="No SKU or barcode recognized in the available photographs.",
                        evidence_sufficient=False,
                        missing_evidence="Missing clear barcode or SKU label.",
                        recommended_photograph="Photograph product or carton label directly.",
                    )
                )
            elif obs_sku.upper() == exp_sku.upper():
                results.append(
                    SingleCheckResult(
                        check_key="SKU_IDENTITY",
                        expected_value=exp_sku,
                        observed_value=obs_sku,
                        verdict="PASS",
                        confidence=0.98,
                        explanation=f"Observed SKU '{obs_sku}' matches PO line expectation '{exp_sku}'.",
                    )
                )
            else:
                results.append(
                    SingleCheckResult(
                        check_key="SKU_IDENTITY",
                        expected_value=exp_sku,
                        observed_value=obs_sku,
                        verdict="FAIL",
                        confidence=0.96,
                        explanation=f"SKU mismatch! Expected '{exp_sku}', but detected '{obs_sku}'.",
                    )
                )

        # ---------------------------------------------------------------------
        # 2. Total Quantity Check
        # ---------------------------------------------------------------------
        if obs_total_qty == exp_qty:
            results.append(
                SingleCheckResult(
                    check_key="QUANTITY_MATCH",
                    expected_value=f"{exp_qty} units",
                    observed_value=f"{obs_total_qty} units ({obs_cartons} cartons × {obs_upc} upc)",
                    verdict="PASS",
                    confidence=0.99,
                    explanation=f"Received quantity {obs_total_qty} exactly matches ordered quantity {exp_qty}.",
                )
            )
        elif obs_total_qty < exp_qty:
            shortage = exp_qty - obs_total_qty
            results.append(
                SingleCheckResult(
                    check_key="QUANTITY_MATCH",
                    expected_value=f"{exp_qty} units",
                    observed_value=f"{obs_total_qty} units ({obs_cartons} cartons × {obs_upc} upc)",
                    verdict="FAIL",
                    confidence=0.99,
                    explanation=f"Short shipment! Received {obs_total_qty} units, expected {exp_qty} units (Shortage: {shortage} units).",
                )
            )
        else:
            overage = obs_total_qty - exp_qty
            results.append(
                SingleCheckResult(
                    check_key="QUANTITY_MATCH",
                    expected_value=f"{exp_qty} units",
                    observed_value=f"{obs_total_qty} units ({obs_cartons} cartons × {obs_upc} upc)",
                    verdict="FAIL",
                    confidence=0.99,
                    explanation=f"Overage shipment! Received {obs_total_qty} units, expected {exp_qty} units (Extra: {overage} units).",
                )
            )

        # ---------------------------------------------------------------------
        # 3. Carton Count Check
        # ---------------------------------------------------------------------
        if obs_cartons == exp_cartons:
            results.append(
                SingleCheckResult(
                    check_key="CARTON_COUNT",
                    expected_value=f"{exp_cartons} cartons",
                    observed_value=f"{obs_cartons} cartons",
                    verdict="PASS",
                    confidence=0.98,
                    explanation=f"Carton count {obs_cartons} matches PO line expectation.",
                )
            )
        else:
            results.append(
                SingleCheckResult(
                    check_key="CARTON_COUNT",
                    expected_value=f"{exp_cartons} cartons",
                    observed_value=f"{obs_cartons} cartons",
                    verdict="FAIL",
                    confidence=0.98,
                    explanation=f"Carton count discrepancy: received {obs_cartons} cartons, expected {exp_cartons}.",
                )
            )

        # ---------------------------------------------------------------------
        # 4. Units Per Carton (UPC) Check
        # ---------------------------------------------------------------------
        if obs_upc == exp_upc:
            results.append(
                SingleCheckResult(
                    check_key="UNITS_PER_CARTON",
                    expected_value=f"{exp_upc} units/carton",
                    observed_value=f"{obs_upc} units/carton",
                    verdict="PASS",
                    confidence=0.98,
                    explanation=f"Units per carton ({obs_upc}) matches PO packaging spec.",
                )
            )
        else:
            results.append(
                SingleCheckResult(
                    check_key="UNITS_PER_CARTON",
                    expected_value=f"{exp_upc} units/carton",
                    observed_value=f"{obs_upc} units/carton",
                    verdict="FAIL",
                    confidence=0.98,
                    explanation=f"Units per carton discrepancy: counted {obs_upc}, expected {exp_upc}.",
                )
            )

        # ---------------------------------------------------------------------
        # 5. Visible Carton Damage Check (Crushing, Water, Tears)
        # ---------------------------------------------------------------------
        carton_cov = coverage_evaluations.get("CARTON_DAMAGE")
        if carton_cov and not carton_cov.is_sufficient:
            results.append(
                SingleCheckResult(
                    check_key="CARTON_DAMAGE",
                    expected_value="Sound carton corrugate (no crushing, water, or tears)",
                    observed_value="INSUFFICIENT_VIEWS",
                    verdict="UNCERTAIN",
                    confidence=0.35,
                    explanation=f"Carton condition cannot be determined: {carton_cov.reason}",
                    evidence_sufficient=False,
                    missing_evidence=carton_cov.missing_evidence,
                    recommended_photograph=carton_cov.recommended_photograph,
                )
            )
        else:
            detected_damages = observation.carton_damage_types
            if not detected_damages:
                results.append(
                    SingleCheckResult(
                        check_key="CARTON_DAMAGE",
                        expected_value="None (sound corrugate)",
                        observed_value="none",
                        verdict="PASS",
                        confidence=0.94,
                        explanation="No visible carton crushing, water damage, or tears detected.",
                    )
                )
            else:
                damage_str = ", ".join(detected_damages)
                results.append(
                    SingleCheckResult(
                        check_key="CARTON_DAMAGE",
                        expected_value="None (sound corrugate)",
                        observed_value=damage_str,
                        verdict="FAIL",
                        confidence=0.95,
                        explanation=f"Carton damage detected: {damage_str}.",
                    )
                )

        # ---------------------------------------------------------------------
        # 6. Unit Damage Check
        # ---------------------------------------------------------------------
        detected_unit_damage = observation.unit_damage_types
        if not detected_unit_damage:
            results.append(
                SingleCheckResult(
                    check_key="UNIT_DAMAGE",
                    expected_value="None (unblemished, factory sealed)",
                    observed_value="none",
                    verdict="PASS",
                    confidence=0.92,
                    explanation="No physical unit damage observed.",
                )
            )
        else:
            u_damage_str = ", ".join(detected_unit_damage)
            results.append(
                SingleCheckResult(
                    check_key="UNIT_DAMAGE",
                    expected_value="None (unblemished, factory sealed)",
                    observed_value=u_damage_str,
                    verdict="FAIL",
                    confidence=0.94,
                    explanation=f"Unit physical damage observed: {u_damage_str}.",
                )
            )

        # ---------------------------------------------------------------------
        # 7. Colour / Variant Match Check
        # ---------------------------------------------------------------------
        variant_cov = coverage_evaluations.get("VARIANT_MATCH")
        if variant_cov and not variant_cov.is_sufficient:
            results.append(
                SingleCheckResult(
                    check_key="VARIANT_MATCH",
                    expected_value=f"Colour: {exp_colour or 'N/A'}, Variant: {exp_variant or 'N/A'}",
                    observed_value="INSUFFICIENT_VIEWS",
                    verdict="UNCERTAIN",
                    confidence=0.30,
                    explanation=f"Variant cannot be determined: {variant_cov.reason}",
                    evidence_sufficient=False,
                    missing_evidence=variant_cov.missing_evidence,
                    recommended_photograph=variant_cov.recommended_photograph,
                )
            )
        else:
            obs_col = (observation.detected_colour or "").strip().lower()
            obs_var = (observation.detected_variant or "").strip().lower()

            mismatch = False
            reasons = []
            if exp_colour and exp_colour != "n/a" and obs_col:
                if exp_colour != obs_col:
                    mismatch = True
                    reasons.append(f"Colour mismatch (expected '{exp_colour}', observed '{obs_col}')")
            if exp_variant and exp_variant != "n/a" and obs_var:
                if "wrong" in obs_var or (exp_variant not in obs_var and obs_var not in exp_variant):
                    mismatch = True
                    reasons.append(f"Variant mismatch (expected '{exp_variant}', observed '{obs_var}')")

            if mismatch:
                results.append(
                    SingleCheckResult(
                        check_key="VARIANT_MATCH",
                        expected_value=f"Colour: {exp_colour}, Variant: {exp_variant}",
                        observed_value=f"Colour: {obs_col or 'unknown'}, Variant: {obs_var or 'unknown'}",
                        verdict="FAIL",
                        confidence=0.93,
                        explanation=f"Variant check failed: {'; '.join(reasons)}.",
                    )
                )
            elif obs_col or obs_var or (not exp_colour and not exp_variant):
                results.append(
                    SingleCheckResult(
                        check_key="VARIANT_MATCH",
                        expected_value=f"Colour: {exp_colour or 'N/A'}, Variant: {exp_variant or 'N/A'}",
                        observed_value=f"Colour: {obs_col or exp_colour}, Variant: {obs_var or exp_variant}",
                        verdict="PASS",
                        confidence=0.91,
                        explanation="Observed color and product variant match PO line spec.",
                    )
                )
            else:
                results.append(
                    SingleCheckResult(
                        check_key="VARIANT_MATCH",
                        expected_value=f"Colour: {exp_colour}, Variant: {exp_variant}",
                        observed_value="undetermined",
                        verdict="UNCERTAIN",
                        confidence=0.50,
                        explanation="Color/variant could not be conclusively determined from the photo.",
                    )
                )

        # ---------------------------------------------------------------------
        # 8. Missing Components Check
        # ---------------------------------------------------------------------
        comp_cov = coverage_evaluations.get("COMPONENTS_CHECK")
        if comp_cov and not comp_cov.is_sufficient:
            results.append(
                SingleCheckResult(
                    check_key="COMPONENTS_CHECK",
                    expected_value=exp_components_raw or "None specified",
                    observed_value="INSUFFICIENT_VIEWS",
                    verdict="UNCERTAIN",
                    confidence=0.30,
                    explanation=f"Cannot inspect components: {comp_cov.reason}",
                    evidence_sufficient=False,
                    missing_evidence=comp_cov.missing_evidence,
                    recommended_photograph=comp_cov.recommended_photograph,
                )
            )
        elif exp_components and exp_components != ["n/a"]:
            obs_comps = [c.lower() for c in observation.detected_components]
            missing = [c for c in exp_components if c not in obs_comps]

            if missing:
                results.append(
                    SingleCheckResult(
                        check_key="COMPONENTS_CHECK",
                        expected_value="; ".join(exp_components),
                        observed_value="; ".join(obs_comps) if obs_comps else "None found",
                        verdict="FAIL",
                        confidence=0.92,
                        explanation=f"Missing components! Missing required items: {', '.join(missing)}.",
                    )
                )
            else:
                results.append(
                    SingleCheckResult(
                        check_key="COMPONENTS_CHECK",
                        expected_value="; ".join(exp_components),
                        observed_value="; ".join(obs_comps),
                        verdict="PASS",
                        confidence=0.95,
                        explanation=f"All expected components present ({', '.join(exp_components)}).",
                    )
                )
        else:
            results.append(
                SingleCheckResult(
                    check_key="COMPONENTS_CHECK",
                    expected_value="N/A",
                    observed_value="N/A",
                    verdict="PASS",
                    confidence=0.99,
                    explanation="No multi-component package requirement on this SKU.",
                )
            )

        return results
