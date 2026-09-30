from typing import Dict, List, Optional
from pydantic import BaseModel


class CoverageEvaluation(BaseModel):
    check_key: str
    is_sufficient: bool
    missing_evidence: Optional[str] = None
    recommended_photograph: Optional[str] = None
    priority: int = 1
    reason: Optional[str] = None


class EvidenceCoverageEngine:
    """
    Evidence Coverage Engine enforcing Rule 4:
    Evaluates whether available photographic evidence is sufficient to make an authoritative determination.
    Missing evidence is NEVER converted into a guess or a low-confidence PASS.
    """

    def evaluate_coverage(
        self,
        available_image_types: List[str],
        image_quality_issues: List[str],
        checks_to_perform: List[str],
        observations: Optional[Dict[str, any]] = None,
    ) -> Dict[str, CoverageEvaluation]:
        evaluations: Dict[str, CoverageEvaluation] = {}

        types_set = set(available_image_types)
        quality_set = set(image_quality_issues)

        has_carton_view = bool(types_set.intersection({"carton_exterior", "other"}))
        has_label_view = "carton_label" in types_set or "product_label" in types_set
        has_product_view = bool(types_set.intersection({"product", "components"}))

        # Check: SKU_IDENTITY
        if "SKU_IDENTITY" in checks_to_perform:
            if not has_label_view and not has_carton_view:
                evaluations["SKU_IDENTITY"] = CoverageEvaluation(
                    check_key="SKU_IDENTITY",
                    is_sufficient=False,
                    missing_evidence="Missing carton shipping label or product barcode photograph.",
                    recommended_photograph="Capture a clear, well-lit photograph of the carton label or product barcode.",
                    priority=1,
                    reason="SKU cannot be verified without a visible barcode or shipping label.",
                )
            elif "occluded_label" in quality_set or "blurry_image" in quality_set:
                evaluations["SKU_IDENTITY"] = CoverageEvaluation(
                    check_key="SKU_IDENTITY",
                    is_sufficient=False,
                    missing_evidence="Label is blurry, occluded, or unreadable.",
                    recommended_photograph="Re-take a non-blurry close-up photograph of the barcode label without glare.",
                    priority=1,
                    reason="Label text is illegible due to blur or occlusion.",
                )
            elif "extreme_glare" in quality_set:
                evaluations["SKU_IDENTITY"] = CoverageEvaluation(
                    check_key="SKU_IDENTITY",
                    is_sufficient=False,
                    missing_evidence="Severe glare obscuring label markings.",
                    recommended_photograph="Capture label with diffused lighting to avoid flash reflections.",
                    priority=1,
                    reason="Barcode cannot be decoded due to glare.",
                )
            else:
                evaluations["SKU_IDENTITY"] = CoverageEvaluation(
                    check_key="SKU_IDENTITY",
                    is_sufficient=True,
                )

        # Check: CARTON_DAMAGE
        if "CARTON_DAMAGE" in checks_to_perform:
            if not has_carton_view:
                evaluations["CARTON_DAMAGE"] = CoverageEvaluation(
                    check_key="CARTON_DAMAGE",
                    is_sufficient=False,
                    missing_evidence="Missing carton exterior overview photograph.",
                    recommended_photograph="Capture wide-angle photographs showing all 4 sides and top of master cartons.",
                    priority=2,
                    reason="Carton structural integrity cannot be evaluated without exterior carton shots.",
                )
            else:
                evaluations["CARTON_DAMAGE"] = CoverageEvaluation(
                    check_key="CARTON_DAMAGE",
                    is_sufficient=True,
                )

        # Check: VARIANT_MATCH
        if "VARIANT_MATCH" in checks_to_perform:
            if not has_product_view and not has_label_view:
                evaluations["VARIANT_MATCH"] = CoverageEvaluation(
                    check_key="VARIANT_MATCH",
                    is_sufficient=False,
                    missing_evidence="Missing product photograph displaying color and variant attributes.",
                    recommended_photograph="Open one master carton and photograph a single unpacked product unit.",
                    priority=2,
                    reason="Color and variant require visible product inspection.",
                )
            elif "blurry_image" in quality_set or "extreme_underexposure" in quality_set:
                evaluations["VARIANT_MATCH"] = CoverageEvaluation(
                    check_key="VARIANT_MATCH",
                    is_sufficient=False,
                    missing_evidence="Product view is poorly lit or blurry, masking true color.",
                    recommended_photograph="Capture product under standard warehouse task lighting.",
                    priority=2,
                    reason="Color fidelity cannot be verified in poor lighting.",
                )
            else:
                evaluations["VARIANT_MATCH"] = CoverageEvaluation(
                    check_key="VARIANT_MATCH",
                    is_sufficient=True,
                )

        # Check: COMPONENTS_CHECK
        if "COMPONENTS_CHECK" in checks_to_perform:
            if "components" not in types_set and not has_product_view:
                evaluations["COMPONENTS_CHECK"] = CoverageEvaluation(
                    check_key="COMPONENTS_CHECK",
                    is_sufficient=False,
                    missing_evidence="Missing opened unit contents photograph.",
                    recommended_photograph="Display all packaged items/accessories side-by-side and photograph them.",
                    priority=2,
                    reason="Included accessories cannot be verified without an opened unit view.",
                )
            else:
                evaluations["COMPONENTS_CHECK"] = CoverageEvaluation(
                    check_key="COMPONENTS_CHECK",
                    is_sufficient=True,
                )

        # Quantity checks are operator attested with carton photographic support
        for q_check in ["QUANTITY_MATCH", "CARTON_COUNT", "UNITS_PER_CARTON"]:
            if q_check in checks_to_perform:
                evaluations[q_check] = CoverageEvaluation(
                    check_key=q_check,
                    is_sufficient=True,
                )

        return evaluations
