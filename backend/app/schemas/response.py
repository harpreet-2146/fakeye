from pydantic import BaseModel
from typing import List, Optional

class EvidenceItem(BaseModel):
    url: str
    publisher: Optional[str]
    snippet: str
    stance: str  # support | contradict | neutral
    stance_conf: float
    semantic_sim: float

class ClaimResponse(BaseModel):
    verdict: str  # True | False | Mixture | Unverifiable
    confidence: int
    summary: str
    evidence: List[EvidenceItem]
