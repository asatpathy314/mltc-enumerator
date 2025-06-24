from enum import Enum, IntEnum
from typing import List, Optional
from uuid import UUID, uuid4
import logging

from pydantic import BaseModel, Field, PositiveFloat, constr

logger = logging.getLogger(__name__)

class PingResponse(BaseModel):
    message: str

class ReviewStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class Likert(IntEnum):      # 1-5 scale for "likelihood", "value", etc.
    very_low = 1
    low = 2
    medium = 3
    high = 4
    very_high = 5

# LLM Response schemas (without UUIDs)
class AttackerRaw(BaseModel):
    """Schema for LLM response - no UUIDs required"""
    description: str
    skill_level: Likert
    access_level: Likert
    prob_of_attack: PositiveFloat = Field(..., ge=0.0, le=1.0)

class EntryPointRaw(BaseModel):
    """Schema for LLM response - no UUIDs required"""
    name: str
    description: str
    prob_of_entry: PositiveFloat = Field(..., ge=0.0, le=1.0)
    difficulty_of_entry: Likert

class AssetRaw(BaseModel):
    """Schema for LLM response - no UUIDs required"""
    name: str
    description: str
    failure_modes: List[str]

class ContextEnumerationRaw(BaseModel):
    """Schema for LLM response - no UUIDs required"""
    attackers: List[AttackerRaw]
    entry_points: List[EntryPointRaw]
    assets: List[AssetRaw]

# Final schemas (with UUIDs)
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

def convert_raw_to_final(raw_context: ContextEnumerationRaw) -> ContextEnumeration:
    """Convert the raw LLM response to the final schema with UUIDs."""
    logger.info("Converting raw LLM response to final schema with UUIDs")
    
    # Convert attackers
    attackers = []
    for raw_attacker in raw_context.attackers:
        attacker = Attacker(
            description=raw_attacker.description,
            skill_level=raw_attacker.skill_level,
            access_level=raw_attacker.access_level,
            prob_of_attack=raw_attacker.prob_of_attack
        )
        attackers.append(attacker)
        logger.debug(f"Generated attacker with UUID: {attacker.id}")
    
    # Convert entry points
    entry_points = []
    for raw_entry in raw_context.entry_points:
        entry_point = EntryPoint(
            name=raw_entry.name,
            description=raw_entry.description,
            prob_of_entry=raw_entry.prob_of_entry,
            difficulty_of_entry=raw_entry.difficulty_of_entry
        )
        entry_points.append(entry_point)
        logger.debug(f"Generated entry point with UUID: {entry_point.id}")
    
    # Convert assets
    assets = []
    for raw_asset in raw_context.assets:
        asset = Asset(
            name=raw_asset.name,
            description=raw_asset.description,
            failure_modes=raw_asset.failure_modes
        )
        assets.append(asset)
        logger.debug(f"Generated asset with UUID: {asset.id}")
    
    return ContextEnumeration(
        attackers=attackers,
        entry_points=entry_points,
        assets=assets
    )

# ### Supply Chain Questions
# Where's this model coming from?
# What's the model trained on?
# Where's the data that the model is trained on stored?