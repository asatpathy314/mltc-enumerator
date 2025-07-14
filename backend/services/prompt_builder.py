from schemas import ContextEnumeration, ChatRefinementRequest, ChatMessage
from typing import List, Tuple

class PromptBuilder:
    """
    A service class dedicated to constructing complex LLM prompts.
    """
    
    def _build_hint_section(self, extra_prompt: str) -> str:
        return f"\n\n### HINT\n{extra_prompt}" if extra_prompt else ""

    def _build_qa_section(self, qa_pairs: List[Tuple[str, str]]) -> str:
        if not qa_pairs:
            return ""
        
        formatted_pairs = [
            f"Q{i+1}: {q}\nA{i+1}: {a}"
            for i, (q, a) in enumerate(qa_pairs)
            if a and a.strip()
        ]
        return ("\n\n### CONTEXTUAL Q&A\n" + "\n\n".join(formatted_pairs)) if formatted_pairs else ""

    def build_context_enumeration_prompt(self, request: ContextEnumeration) -> str:
        """
        Builds the prompt for either initial or refinement context enumeration
        based on the content of the request.
        """
        is_initial = not (request.attackers or request.entry_points or request.assets)
        
        qa_pairs = list(zip(request.questions, request.answers))
        hint_section = self._build_hint_section(request.extra_prompt)
        qa_section = self._build_qa_section(qa_pairs)

        if is_initial:
            return self._build_initial_context_prompt(request.textual_dfd, hint_section, qa_section)
        else:
            return self._build_refinement_context_prompt(request, hint_section, qa_section)

    def _build_initial_context_prompt(self, textual_dfd: str, hint_section: str, qa_section: str) -> str:
        return f"""### ROLE
You are a senior security-threat-modeling analyst.

### TASK
From the **Data-Flow Diagram (DFD)**, optional **Hint**, and **Contextual Q&A** provided below, identify every:

1. **Attacker** - any actor that can threaten the system.
2. **EntryPoint** - any interface, channel, or location an attacker could use to gain a foothold.
3. **Asset** - any component or data store whose loss or compromise matters.
4. **Assumptions** - key assumptions you are making about the system, users, environment, or security controls.
5. **Questions** - additional questions you want to ask the human to help you understand the system better.

### SCHEMA (strict)
class Likert(IntEnum):      # 1 = very_low ... 5 = very_high
    very_low = 1
    low = 2
    medium = 3
    high = 4
    very_high = 5

class Attacker:
    description: str
    skill_level: int  # Likert scale [1, 5]
    access_level: int  # Likert scale [1, 5]
    prob_of_attack: float

class EntryPoint:
    name: str
    description: str
    prob_of_entry: float
    difficulty_of_entry: int  # Likert scale [1, 5]

class Asset:
    name: str
    description: str
    failure_modes: list[str]

### OUTPUT FORMAT (MUST BE VALID JSON)
{{
  "attackers": [Attacker, ...],
  "entry_points": [EntryPoint, ...],
  "assets": [Asset, ...],
  "assumptions": [string, ...],
  "questions": [string, ...],
  "answers": [string, ...]
}}

CRITICAL: Output ONLY the JSON object. ENSURE THAT THE FORMAT IS FOLLOWED EXACTLY. Use empty lists where appropriate.

### INPUT
DFD:
{textual_dfd}{hint_section}{qa_section}
"""

    def _build_refinement_context_prompt(self, request: ContextEnumeration, hint_section: str, qa_section: str) -> str:
        attackers_str = "\n".join([
            f"- {a.description} (Skill: {a.skill_level.name}, Access: {a.access_level.name})" for a in request.attackers
        ])
        entry_points_str = "\n".join([f"- {e.name}: {e.description}" for e in request.entry_points])
        assets_str = "\n".join([f"- {a.name}: {a.description}" for a in request.assets])
        assumptions_str = "\n".join([f"- {s}" for s in request.assumptions])

        return f"""### ROLE
### TASK
Your task is to **review and refine** the provided security context. 
You may add, remove, or modify Attackers, Entry Points, and Assets to improve quality, accuracy, and completeness.
You MAY NOT remove questions, answers, or assumptions.
You can add any ADDITIONAL assumptions you might make.
You can add any ADDITIONAL questions you might ask.

### PREVIOUS CONTEXT
**Attackers:**
{attackers_str}

**Entry Points:**
{entry_points_str}

**Assets:**
{assets_str}

**Assumptions:**
{assumptions_str}

### ORIGINAL DFD
{request.textual_dfd}

### SCHEMA (strict)
class Likert(IntEnum):      # 1 = very_low … 5 = very_high
    very_low = 1
    low = 2
    medium = 3
    high = 4
    very_high = 5

class Attacker:
    description: str
    skill_level: int  # Likert scale [1, 5]
    access_level: int  # Likert scale [1, 5]
    prob_of_attack: float

class EntryPoint:
    name: str
    description: str
    prob_of_entry: float
    difficulty_of_entry: int  # Likert scale [1, 5]

class Asset:
    name: str
    description: str
    failure_modes: list[str]

### OUTPUT FORMAT (MUST BE VALID JSON)
{{
  "attackers": [Attacker, ...],
  "entry_points": [EntryPoint, ...],
  "assets": [Asset, ...],
  "assumptions": [string, ...],
  "questions": [string, ...],
  "answers": [string, ...]
}}

CRITICAL: Output ONLY the JSON object.
### INPUT
DFD:
{request.textual_dfd}{hint_section}{qa_section}
"""
    def build_question_generation_prompt(self, detected_areas: List[str], reasoning: str, textual_dfd: str) -> str:
        return f"""### Generate Questions
Let's think step by step. To generate information elicitation questions. Focus on questions that
could generate information about the system's architecture, training data, and model origin. Focus
on questions that might provide information useful to the following categories of ML security:

### ML ATTACK CATEGORIES
1. **Reconnaissance/Discovery** - Information gathering about ML system architecture, datasets, and public exposure
2. **Resource Capability Development** - Attacker staging and capability development using available resources
3. **Supply Chain Dependency Poisoning** - Comprehensive supply chain security including dependencies, containers, and provenance
4. **Initial Ongoing Access Vectors** - Authentication bypass, API security, social engineering, and persistent access
5. **Model Data Extraction Privacy** - Model parameter extraction, training data recovery, and privacy attacks
6. **Model Manipulation Persistence** - Model integrity attacks, backdoors, and persistent manipulation
7. **Adversarial Service Disruption** - Input-based attacks causing misclassification or service degradation

### SYSTEM ANALYZED
{textual_dfd}

### OUTPUT FORMAT
{{
  "specific_questions": [
    "question 1",
    "question 2",
    ...
  ]
}}

<never>ask specific questions about encryption, authentication flows, or other security-control questions.</never>
<always>Ask questions that are architecturally focused and meant to elicit information about the system's architecture, training data, and model origin.</always>
<always>Output ONLY valid JSON.</always>"""

    def build_extraction_prompt(self, latest_chat_message: str, latest_user_response: str, textual_dfd: str) -> str:
        return f"""### TASK
Analyze the user's response about their ML system and extract specific security-relevant information. 

### MODEL QUESTIONS
{latest_chat_message}

### USER'S RESPONSE
"{latest_user_response}"

### ORIGINAL DFD CONTEXT
{textual_dfd}

### EXTRACTION SCHEMA
For each piece of security-relevant information, output:
{{
  "extractions": [
    {{
      "question": "specific question matching to the answer",
      "extracted_answer": "specific factual answer",
    }}
  ],
  "coverage_assessment": {{
    "confidence_level": 0.0-1.0,
    "needs_followup": true/false,
    "missing_information": "questions you feel need more clarification in natural language"
  }}
}}

CRITICAL: Output ONLY valid JSON."""

    def build_followup_prompt(self, missing_information: str, textual_dfd: str, conversation_history: List[ChatMessage]) -> str:
        conversation_text = ""
        for msg in conversation_history:
            role_label = "Assistant" if msg.role == "assistant" else "User"
            conversation_text += f"\n\n{role_label}: {msg.content}"

        return f"""### TASK
Based on the conversation so far and the analysis of missing information, generate follow-up questions to learn more about this system.

### MISSING INFORMATION
{missing_information}

### SYSTEM CONTEXT
{textual_dfd}

### CONVERSATION SO FAR
{conversation_text}

### OUTPUT FORMAT
{{
  "followup_questions": [list of followup questions as strings]
}}

CRITICAL: Output ONLY valid JSON. Do NOT add any additional formatting."""

    def build_qa_extraction_prompt(self, conversation_history: List[ChatMessage]) -> str:
        conversation_text = ""
        for msg in conversation_history:
            role_label = "Assistant" if msg.role == "assistant" else "User"
            conversation_text += f"\n\n{role_label}: {msg.content}"
            
        return f"""### ROLE
You are an expert at extracting structured Q&A pairs from conversations.

### TASK
Extract individual questions and their corresponding answers from this ML security conversation. 
Each question should be paired with its specific answer, not the entire user response.

### CONVERSATION
{conversation_text}

### EXTRACTION RULES
1. Extract only the security-relevant questions asked by the Assistant
2. Extract only the specific answers that respond to each question
3. If a user provides multiple numbered answers, pair each with the corresponding question
4. Clean up questions to remove conversational fluff
5. Keep answers concise but complete

### OUTPUT FORMAT
{{
  "qa_pairs": [
    {{
      "question": "Clean, specific question text",
      "answer": "Specific answer to this question only"
    }}
  ]
}}

CRITICAL: Output ONLY valid JSON. Extract actual Q&A pairs, not entire messages."""
