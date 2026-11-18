from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from maintainability_lens.schemas import Characteristic, Verdict


class RaterVerdict(BaseModel):
    rater: str
    file_id: str
    characteristic: Characteristic
    verdict: Verdict


def load_rater_verdicts(rater_verdicts_file: Path) -> list[RaterVerdict]:
    return TypeAdapter(list[RaterVerdict]).validate_json(rater_verdicts_file.read_bytes())
