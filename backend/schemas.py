from enum import Enum, IntEnum
from typing import List, Optional
from uuid import UUID, uuid4
import logging

from pydantic import BaseModel, Field, PositiveFloat, constr

logger = logging.getLogger(__name__)

class PingResponse(BaseModel):
    message: str
class ThreatCategory(str, Enum):
    spoofing = "spoofing"
    tampering = "tampering"
    repudiation = "repudiation"
    information_disclosure = "information_disclosure"
    denial_of_service = "denial_of_service"
    elevation_of_privilege = "elevation_of_privilege"
    other = "other"

class Likert(IntEnum):      # 1-5 scale for "likelihood", "value", etc.
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

class ContextEnumeration(BaseModel):
    """Schema for LLM response"""
    textual_dfd: str
    extra_prompt: Optional[str] = None
    attackers: List[Attacker]
    entry_points: List[EntryPoint]
    assets: List[Asset]
    assumptions: List[str]
    questions: List[str] = []
    answers: List[str] = []

class ThreatChain(BaseModel):
    name: str
    chain: List[str]
    category: ThreatCategory
    description: str
    mitre_atlas: str
    mitre_attack: str
    mitigations: List[str]

class ThreatEnumeration(BaseModel):
    threat_chains: List[ThreatChain]

# ### Supply Chain Questions
# Where's this model coming from?
# What's the model trained on?
# Where's the data that the model is trained on stored?
# ### Context Enumeration
# 