import os
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.models import ReceivingInspection
from app.repositories.receiving_repository import ReceivingRepository
from app.agents.vision_agent import VisionAgent, VisionObservation
from app.evidence.coverage_engine import EvidenceCoverageEngine
from app.verification.verification_engine import VerificationEngine, SingleCheckResult
from app.decision.decision_engine import DecisionEngine, DecisionOutput
from app.schemas.evidence_contract import (
    CrossPodEvidenceContract,
    ContractCheckRecord,
    ContractEvidenceHash,
    ContractOverride,
)

logger = logging.getLogger(__name__)


class InspectionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReceivingRepository(db)
        self.vision_agent = VisionAgent()
        self.coverage_engine = EvidenceCoverageEngine()
        self.verification_engine = VerificationEngine()
        self.decision_engine = DecisionEngine()

    def run_inspection_analysis(
        self,
        org_id: str,
        inspection_id: str,
        operator_cartons: Optional[int] = None,
        operator_upc: Optional[int] = None,
        simulate_failure: bool = False,
    ) -> ReceivingInspection:
        """
        Executes end-to-end receiving inspection analysis.
        Implements Rule 2 (Batched model call), Rule 3 (Fail-open), and Rule 4 (Uncertain handling).
        """
        inspection = self.repo.get_inspection(org_id, inspection_id)
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found for org {org_id}")

        # Update status to processing
        inspection.inspection_status = "processing"
        self.db.commit()

        # Rule 3: Fail Open - If model times out or errors, persist capture as pending_review
        if simulate_failure:
            logger.warning(f"Simulating vision model failure for inspection {inspection_id}")
            self.repo.update_inspection_status_and_decision(
                org_id=org_id,
                inspection_id=inspection_id,
                status="pending_review",
                overall_decision="UNCERTAIN",
                disposition="PENDING_OPERATOR_REVIEW",
            )
            # Add an evidence request for manual review
            self.repo.add_evidence_request(
                org_id=org_id,
                inspection_id=inspection_id,
                reason="Vision provider service timeout or communication error.",
                missing_evidence="Manual operator physical verification required.",
                recommended_photograph="Inspect physical labels and verify carton counts manually.",
                priority=1,
            )
            return inspection

        try:
            start_time = time.time()

            # Retrieve authoritative PO Line and Product
            po_line = self.repo.get_po_line(org_id, inspection.po_line_id)
            if not po_line:
                raise ValueError("Associated Purchase Order Line not found.")

            po = po_line.purchase_order
            product = po_line.product

            po_context = {
                "po_number": po.po_number if po else "UNKNOWN_PO",
                "po_line": 1,
                "supplier": po.supplier if po else None,
                "sku": po_line.sku,
                "asin": product.asin if product else None,
                "expected_quantity": po_line.expected_quantity,
                "expected_cartons": po_line.expected_cartons,
                "expected_units_per_carton": po_line.expected_units_per_carton,
                "expected_colour": po_line.expected_colour,
                "expected_variant": po_line.expected_variant,
                "expected_components": po_line.expected_components,
            }

            # Gather associated images
            images = inspection.images
            image_paths = [img.file_reference for img in images if os.path.exists(img.file_reference)]
            image_types = [img.image_type for img in images]
            image_checksums = [img.checksum or "" for img in images]

            # -----------------------------------------------------------------
            # 1. Batched Vision Perception (Rule 2: ONE single batched call)
            # -----------------------------------------------------------------
            observation: VisionObservation = self.vision_agent.analyze_unit_batch(
                image_paths=image_paths,
                unit_id=inspection.unit_id,
                expected_context=po_context,
            )

            # Record visual evidence items
            for img in images:
                if observation.carton_damage_types:
                    self.repo.add_evidence_item(
                        org_id=org_id,
                        inspection_id=inspection_id,
                        evidence_type="damage_record",
                        image_id=img.id,
                        description=f"Detected damage: {', '.join(observation.carton_damage_types)}",
                    )
                if observation.detected_sku:
                    self.repo.add_evidence_item(
                        org_id=org_id,
                        inspection_id=inspection_id,
                        evidence_type="label_reading",
                        image_id=img.id,
                        description=f"Decoded SKU label: {observation.detected_sku}",
                    )

            # -----------------------------------------------------------------
            # 2. Evidence Coverage Evaluation (Rule 4: Uncertain Handling)
            # -----------------------------------------------------------------
            checks_to_run = [
                "SKU_IDENTITY",
                "QUANTITY_MATCH",
                "CARTON_COUNT",
                "UNITS_PER_CARTON",
                "CARTON_DAMAGE",
                "UNIT_DAMAGE",
                "VARIANT_MATCH",
                "COMPONENTS_CHECK",
            ]
            coverage_evals = self.coverage_engine.evaluate_coverage(
                available_image_types=image_types,
                image_quality_issues=observation.image_quality_issues,
                checks_to_perform=checks_to_run,
            )

            # -----------------------------------------------------------------
            # 3. Deterministic Verification (Rule 5: Authoritative comparison)
            # -----------------------------------------------------------------
            check_results: List[SingleCheckResult] = self.verification_engine.verify_all(
                po_line_context=po_context,
                observation=observation,
                coverage_evaluations=coverage_evals,
                operator_cartons=operator_cartons,
                operator_units_per_carton=operator_upc,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Save individual check results & evidence requests for uncertain checks
            for res in check_results:
                saved_check = self.repo.save_or_update_check(
                    org_id=org_id,
                    inspection_id=inspection_id,
                    check_key=res.check_key,
                    expected_value=res.expected_value,
                    observed_value=res.observed_value,
                    verdict=res.verdict,
                    confidence=res.confidence,
                    explanation=res.explanation,
                    model_version="INBOUNDSHIELD_HYBRID_V2",
                    latency_ms=latency_ms,
                )

                if res.verdict == "UNCERTAIN" and res.missing_evidence:
                    self.repo.add_evidence_request(
                        org_id=org_id,
                        inspection_id=inspection_id,
                        check_id=saved_check.id,
                        reason=res.explanation,
                        missing_evidence=res.missing_evidence,
                        recommended_photograph=res.recommended_photograph,
                        priority=1 if res.check_key == "SKU_IDENTITY" else 2,
                    )

            # -----------------------------------------------------------------
            # 4. Deterministic Decision Engine
            # -----------------------------------------------------------------
            decision: DecisionOutput = self.decision_engine.decide(
                checks=check_results,
                po_context=po_context,
                image_checksums=image_checksums,
            )

            final_status = "completed" if decision.overall_decision in ("PASS", "FAIL") else "pending_review"

            # -----------------------------------------------------------------
            # 5. Persist Decision & Cryptographic Evidence Hash
            # -----------------------------------------------------------------
            updated_inspection = self.repo.update_inspection_status_and_decision(
                org_id=org_id,
                inspection_id=inspection_id,
                status=final_status,
                overall_decision=decision.overall_decision,
                disposition=decision.disposition,
                evidence_hash=decision.evidence_hash,
            )

            return updated_inspection

        except Exception as e:
            logger.exception(f"Unexpected error during inspection {inspection_id}: {e}")
            # Fail-open: save capture as pending_review without failing dock flow
            self.repo.update_inspection_status_and_decision(
                org_id=org_id,
                inspection_id=inspection_id,
                status="pending_review",
                overall_decision="UNCERTAIN",
                disposition="SYSTEM_EXCEPTION_PENDING_REVIEW",
            )
            return inspection

    def export_evidence_contract(
        self, org_id: str, inspection_id: str
    ) -> CrossPodEvidenceContract:
        """
        Produces the exportable cross-pod evidence contract for Pod 02 (Prep) and Pod 05 (Recovery).
        """
        inspection = self.repo.get_inspection(org_id, inspection_id)
        if not inspection:
            raise ValueError("Inspection not found")

        po_line = inspection.po_line
        po = inspection.purchase_order
        product = po_line.product if po_line else None

        # Build contract checks
        contract_checks = [
            ContractCheckRecord(
                check_key=c.check_key,
                expected=c.expected_value,
                observed=c.observed_value,
                verdict=c.verdict,
                confidence=c.confidence,
                explanation=c.explanation,
            )
            for c in inspection.checks
        ]

        # Evidence hashes
        evidence_hashes = [
            ContractEvidenceHash(
                image_type=img.image_type,
                filename=os.path.basename(img.file_reference),
                sha256=img.checksum or "unknown",
            )
            for img in inspection.images
        ]

        # Overrides
        contract_overrides = [
            ContractOverride(
                check_key=o.check.check_key if o.check else None,
                original_verdict=o.original_verdict,
                new_verdict=o.new_verdict,
                reason=o.reason,
                operator_id=o.operator_id,
                timestamp=o.created_at.isoformat(),
            )
            for o in inspection.overrides
        ]

        # Calculate quantities
        qty_check = next((c for c in inspection.checks if c.check_key == "QUANTITY_MATCH"), None)
        carton_check = next((c for c in inspection.checks if c.check_key == "CARTON_COUNT"), None)
        upc_check = next((c for c in inspection.checks if c.check_key == "UNITS_PER_CARTON"), None)

        cartons_rcvd = po_line.expected_cartons
        if carton_check and carton_check.observed_value:
            try:
                cartons_rcvd = int(carton_check.observed_value.split()[0])
            except Exception:
                pass

        upc_rcvd = po_line.expected_units_per_carton
        if upc_check and upc_check.observed_value:
            try:
                upc_rcvd = int(upc_check.observed_value.split()[0])
            except Exception:
                pass

        qty_rcvd = cartons_rcvd * upc_rcvd

        return CrossPodEvidenceContract(
            record_id=f"RCV-{inspection.id[:8].upper()}",
            unit_id=inspection.unit_id or f"UNIT-{inspection.id[:6].upper()}",
            org_id=org_id,
            operator_id=inspection.operator_id or "op_dock_01",
            captured_at=inspection.created_at.isoformat(),
            completed_at=(inspection.completed_at or datetime.now(timezone.utc)).isoformat(),
            po_number=po.po_number if po else "UNKNOWN",
            po_line=1,
            supplier=po.supplier if po else None,
            sku=po_line.sku if po_line else inspection.sku,
            asin=product.asin if product else None,
            product_title=product.name if product else None,
            spec_colour=po_line.expected_colour if po_line else None,
            spec_variant=po_line.expected_variant if po_line else None,
            spec_components=po_line.expected_components if po_line else None,
            cartons_ordered=po_line.expected_cartons if po_line else 1,
            cartons_received=cartons_rcvd,
            units_per_carton_ordered=po_line.expected_units_per_carton if po_line else 1,
            units_per_carton_counted=upc_rcvd,
            qty_ordered=po_line.expected_quantity if po_line else 1,
            qty_received=qty_rcvd,
            overall_verdict=inspection.overall_decision or "UNCERTAIN",
            disposition=inspection.disposition or "PENDING",
            checks=contract_checks,
            evidence_hashes=evidence_hashes,
            overrides=contract_overrides,
            certificate_sha256=inspection.evidence_hash or "unsealed",
        )
