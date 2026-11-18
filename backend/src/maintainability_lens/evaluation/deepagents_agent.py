from pathlib import Path

from maintainability_lens.evaluation.approach_error import ApproachError
from maintainability_lens.evaluation.recorded_findings import FileFindings
from maintainability_lens.schemas import Characteristic

EVALUATION_SESSION_ID = "evaluation-set"


def decide_with_deepagents_agent(checkout: Path, file: str) -> FileFindings:
    # Why: the LLM stack is the `agent` dependency group, absent when installed with uvx.
    try:
        from maintainability_lens import agent
        from maintainability_lens.config import get_settings
        from maintainability_lens.observability import new_run_id
    except ImportError as error:
        raise ApproachError("the agent needs the agent dependency group") from error
    findings = []
    for characteristic in Characteristic:
        try:
            findings.append(
                agent.evaluate_characteristic(
                    checkout,
                    characteristic,
                    run_id=new_run_id(),
                    session_id=EVALUATION_SESSION_ID,
                    file=file,
                )
            )
        # Why: provider and network errors surface as many exception types; one file's failure
        # must not end a run over the whole Evaluation set.
        except Exception as error:
            raise ApproachError(f"{characteristic}: {type(error).__name__}: {error}") from error
    return FileFindings(findings=findings, model=get_settings().llm_model)
