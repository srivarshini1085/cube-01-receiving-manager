from fastapi import APIRouter
from app.services.scenario_runner import ScenarioRunner, BenchmarkReport

router = APIRouter(prefix="/api/v1/scenarios", tags=["evaluation_and_scenarios"])


@router.post("/run-all", response_model=BenchmarkReport)
def run_all_scenarios():
    runner = ScenarioRunner()
    return runner.run_all_scenarios()


@router.post("/run/{scenario_id}")
def run_single_scenario(scenario_id: int):
    """
    Runs a single scenario (1-10) with defect bounding boxes, image fixtures, and certificates.
    Used for 1-click evaluator demo presets on the Live Dock Scanner.
    """
    runner = ScenarioRunner()
    return runner.run_single_scenario(scenario_id=scenario_id)
