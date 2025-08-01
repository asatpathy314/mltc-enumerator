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

# --------- New: Chat-based ML-aware Refinement ----------
class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[str] = None

class MLAttackArea(str, Enum):
    """Known ML attack categories to guide questioning."""
    reconnaissance_discovery = "reconnaissance_discovery"
    resource_capability_development = "resource_capability_development"
    supply_chain_dependency_poisoning = "supply_chain_dependency_poisoning"
    initial_ongoing_access_vectors = "initial_ongoing_access_vectors"
    model_data_extraction_privacy = "model_data_extraction_privacy"
    model_manipulation_persistence = "model_manipulation_persistence"
    adversarial_service_disruption = "adversarial_service_disruption"

class StructuredAnswer(BaseModel):
    """Structured extraction from natural language user response."""
    question: str
    extracted_answer: str

class MultipleChoiceOption(BaseModel):
    """A single option in a multiple choice question."""
    id: str
    text: str
    is_editable: bool = True

class MultipleChoiceQuestion(BaseModel):
    """A question with multiple choice options and support for custom answers."""
    id: str
    question: str
    options: List[MultipleChoiceOption]
    allow_other: bool = True
    allow_edit_options: bool = True

class UserAnswer(BaseModel):
    """User's answer to a multiple choice question."""
    question_id: str
    selected_option_id: Optional[str] = None  # None if "other" was chosen
    custom_answer: Optional[str] = None  # Set if "other" was chosen or option was edited
    edited_options: List[MultipleChoiceOption] = []  # If user edited any options

class ChatRefinementRequest(BaseModel):
    """Client -> server payload for chat-based DFD refinement."""
    textual_dfd: str
    conversation_history: List[ChatMessage] = []
    # Optional: previous structured answers from earlier rounds
    structured_answers: List[StructuredAnswer] = []
    # Optional: answers to multiple choice questions
    multiple_choice_answers: List[UserAnswer] = []

class ChatRefinementResponse(BaseModel):
    """Server -> client payload for chat conversation.
    
    Contains the assistant's natural language response plus structured data
    about what information has been gathered and next steps.
    """
    message: str  # Natural language response to user
    status: str   # "need_more_info" | "success" 
    
    # When status = "need_more_info":
    assistant_response: str  # Natural language question/response
    multiple_choice_questions: List[MultipleChoiceQuestion] = []  # New: structured questions
    
    # When status = "success":
    questions: List[str] = []  # Collected questions for context enumeration
    answers: List[str] = []    # Collected answers for context enumeration
    structured_answers: List[StructuredAnswer]  # All gathered structured data
    coverage_analysis: dict  # Which ML attack areas were covered 