from enum import Enum, IntEnum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PositiveFloat, constr

class PingResponse(BaseModel):
    message: str

class ReviewStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class Likert(IntEnum):      # 1-5 scale for “likelihood”, “value”, etc.
    very_low = 1
    low = 2
    medium = 3
    high = 4
    very_high = 5

class Attacker(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    skill_level: Likert
    access_level: Likert
    prob_of_attack: PositiveFloat = Field(..., ge=0.0, le=1.0)

class EntryPoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    prob_of_entry: PositiveFloat = Field(..., ge=0.0, le=1.0)
    difficulty_of_entry: Likert

class Asset(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    failure_modes: List[str]

class EntryPointRanking(BaseModel):
    entry_id: UUID
    likelihood: Likert
    reviewer: str
    status: ReviewStatus = ReviewStatus.pending
    comments: Optional[str] = None

class AssetValueRanking(BaseModel):
    asset_id: UUID
    value: Likert
    reviewer: str
    status: ReviewStatus = ReviewStatus.pending
    comments: Optional[str] = None

class AttackerProfileRanking(BaseModel):
    attacker_id: UUID
    threat_level: Likert
    reviewer: str
    status: ReviewStatus = ReviewStatus.pending
    comments: Optional[str] = None

class ContextRequest(BaseModel):
    textual_dfd: str
    extra_prompt: Optional[str] = None
    supply_chain_answers: List[str]

class ContextEnumeration(BaseModel):
    attackers: List[Attacker]
    entry_points: List[EntryPoint]
    assets: List[Asset]

class VerifiedContext(BaseModel):
    attackers: List[AttackerProfileRanking]
    entry_points: List[EntryPointRanking]
    assets: List[AssetValueRanking]

# ### Supply Chain Questions
# Where's this model coming from?
# What's the model trained on?
# Where's the data that the model is trained on stored?