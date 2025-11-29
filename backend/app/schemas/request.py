from pydantic import BaseModel

class ClaimRequest(BaseModel):
    claim: str
    refresh: bool = False
