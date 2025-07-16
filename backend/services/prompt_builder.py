from schemas import ContextEnumeration, ChatRefinementRequest, ChatMessage
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum
import json

class AttackType(Enum):
    """Enumeration of different ML attack categories for modular question generation"""
    MODEL_POISONING = "model_poisoning"
    EVASION_ATTACKS = "evasion_attacks"
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_CAPABILITY = "resource_capability"
    SUPPLY_CHAIN = "supply_chain"
    INITIAL_ACCESS = "initial_access"
    DATA_EXTRACTION = "data_extraction"
    SERVICE_DISRUPTION = "service_disruption"

class ModularQuestionGenerator:
    """
    Service class for generating attack-specific questions using a modular approach.
    Each attack type has its own specialized prompt and the results are combined.
    """
    
    def __init__(self, prompt_builder: 'PromptBuilder'):
        self.prompt_builder = prompt_builder
        
    async def generate_modular_questions(
        self, 
        textual_dfd: str, 
        llm_client,
        attack_types: Optional[List[AttackType]] = None,
        context: Optional[ContextEnumeration] = None
    ) -> Dict[str, Any]:
        """
        Generate questions for multiple attack types and combine results.
        Uses parallel processing for improved performance.
        
        Args:
            textual_dfd: The data flow diagram to analyze
            llm_client: LLM client for making API calls
            attack_types: List of attack types to generate questions for
            context: Existing security context (optional)
            
        Returns:
            Combined question data from all attack types
        """
        import time
        start_time = time.time()
        
        if attack_types is None:
            # Default to the two primary implemented attack types
            attack_types = [AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS]
        
        generation_metadata = {
            "attack_types_analyzed": [],
            "generation_method": "modular_attack_specific_parallel",
            "total_questions": 0,
            "questions_per_attack": {},
            "parallel_execution": True,
            "performance": {
                "start_time": start_time,
                "attack_types_count": len(attack_types)
            }
        }
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Starting parallel question generation for {len(attack_types)} attack types")
        
        # Create tasks for parallel execution
        tasks = []
        for attack_type in attack_types:
            task = self._generate_questions_for_attack_type(
                attack_type, textual_dfd, llm_client, context
            )
            tasks.append(task)
        
        # Execute all attack type generations in parallel
        import asyncio
        parallel_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        parallel_end = time.time()
        
        # Aggregate results
        all_questions = []
        for i, result in enumerate(results):
            attack_type = attack_types[i]
            
            if isinstance(result, Exception):
                logger.error(f"Failed to generate questions for {attack_type.value}: {str(result)}")
                generation_metadata["questions_per_attack"][attack_type.value] = 0
            else:
                attack_questions = result.get("questions", [])
                attack_metadata = result.get("metadata", {})
                
                # Add attack type metadata to each question
                for question in attack_questions:
                    question["attack_type"] = attack_type.value
                    question["attack_focus"] = attack_metadata.get("focus_area", attack_type.value)
                
                all_questions.extend(attack_questions)
                generation_metadata["attack_types_analyzed"].append(attack_type.value)
                generation_metadata["questions_per_attack"][attack_type.value] = len(attack_questions)
                
                logger.info(f"✅ Generated {len(attack_questions)} questions for {attack_type.value}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        parallel_duration = parallel_end - parallel_start
        
        generation_metadata["total_questions"] = len(all_questions)
        generation_metadata["performance"].update({
            "total_duration_seconds": round(total_duration, 2),
            "parallel_llm_duration_seconds": round(parallel_duration, 2),
            "questions_per_second": round(len(all_questions) / total_duration, 2) if total_duration > 0 else 0,
            "end_time": end_time
        })
        
        logger.info(f"Parallel generation completed in {total_duration:.2f}s: {generation_metadata['total_questions']} total questions from {len(generation_metadata['attack_types_analyzed'])} attack types (LLM calls: {parallel_duration:.2f}s)")
        
        return {
            "questions_with_options": all_questions,
            "generation_metadata": generation_metadata,
            "modular_approach": True
        }
    
    async def _generate_questions_for_attack_type(
        self,
        attack_type: AttackType,
        textual_dfd: str,
        llm_client,
        context: Optional[ContextEnumeration] = None
    ) -> Dict[str, Any]:
        """
        Generate questions for a single attack type.
        Used internally for parallel processing.
        """
        system_prompt = """You are an ML security expert generating targeted questions to identify vulnerabilities. Output ONLY valid JSON."""
        
        attack_prompt = self.prompt_builder.build_attack_specific_prompt(
            attack_type, textual_dfd, context
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": attack_prompt}
        ]
        
        response = await llm_client.chat_completion_json(
            messages=messages, 
            temperature=0.2
        )
        
        attack_data = json.loads(response)
        attack_questions = attack_data.get("questions_with_options", [])
        
        return {
            "questions": attack_questions,
            "metadata": {
                "attack_type": attack_type.value,
                "focus_area": attack_data.get("focus_area", attack_type.value),
                "generation_timestamp": __import__('time').time()
            }
        }
    
    def get_supported_attack_types(self) -> List[AttackType]:
        """Return list of currently supported attack types."""
        return [AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS]
    
    def get_attack_type_info(self, attack_type: AttackType) -> Dict[str, Any]:
        """Get information about a specific attack type."""
        attack_info = {
            AttackType.MODEL_POISONING: {
                "name": "Model Poisoning",
                "description": "Attacks that compromise model integrity through malicious training data or pipeline manipulation",
                "focus_areas": ["training_data", "model_updates", "pipeline_security", "access_control", "validation", "supply_chain"]
            },
            AttackType.EVASION_ATTACKS: {
                "name": "Evasion Attacks", 
                "description": "Attacks that craft adversarial inputs to cause misclassification",
                "focus_areas": ["input_validation", "model_robustness", "detection_systems", "input_sources", "architecture", "response_mechanisms"]
            }
        }
        return attack_info.get(attack_type, {"name": attack_type.value, "description": "Unknown attack type"})

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
        return f"""### Generate Questions with Multiple Choice Answers
Let's think step by step. To generate information elicitation questions with potential answers. Focus on questions that
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
For each question, provide exactly 3 plausible answer options that are specific and realistic for the ML system domain:

{{
  "questions_with_options": [
    {{
      "id": "q1",
      "question": "question text here",
      "options": [
        {{
          "id": "q1_opt1",
          "text": "specific realistic answer option 1"
        }},
        {{
          "id": "q1_opt2",
          "text": "specific realistic answer option 2"
        }},
        ...
        {{
          "id": "q1_optn",
          "text": "specific realistic answer option n"
        }},
      ]
    }}
  ]
}}

<never>ask specific questions about encryption, authentication flows, or other security-control questions.</never>
<always>Ask questions that are architecturally focused and meant to elicit information about the system's architecture, training data, and model origin.</always>
<always>Make answer options specific, realistic, and diverse - avoid generic options like "Yes/No/Maybe".</always>
<always>Output ONLY valid JSON.</always>"""

    def build_attack_specific_prompt(self, attack_type: AttackType, textual_dfd: str, context: Optional[ContextEnumeration] = None) -> str:
        """Generate attack-specific questions for modular threat modeling"""

        context_section = self._build_attack_context_section(context)

        attack_focuses = {
            AttackType.MODEL_POISONING: {
                "name": "Model Poisoning",
                "description": "malicious manipulation of training data, model parameters, or training pipeline to compromise model integrity",
                "focus_areas": [
                    "Training Data Sources - origin, collection methods, validation processes, and data provenance",
                    "Model Update Mechanisms - how models are retrained, updated, fine-tuned, or versioned",
                    "Data Pipeline Security - sanitization, filtering, integrity checks, and validation stages",
                    "Access Controls - who can modify training data, model parameters, or training infrastructure",
                    "Model Validation - testing procedures, performance monitoring, and anomaly detection for compromised models",
                    "Supply Chain Security - third-party datasets, pre-trained models, training services, and dependency management"
                ],
                "example_questions": [
                    "What is the source and validation process for your training data?",
                    "How do you handle model updates and retraining procedures?",
                    "What access controls exist for the training pipeline and data?"
                ]
            },
            AttackType.EVASION_ATTACKS: {
                "name": "Evasion Attacks", 
                "description": "crafting adversarial inputs that cause misclassification while appearing normal to humans",
                "focus_areas": [
                    "Input Validation - preprocessing, sanitization, format checking, and boundary validation",
                    "Model Robustness - adversarial training, input perturbation tolerance, and defensive mechanisms",
                    "Detection Systems - anomaly detection, input monitoring, and suspicious pattern recognition",
                    "Input Sources - attack surface, user input channels, API endpoints, and trust boundaries",
                    "Model Architecture - ensemble methods, confidence scoring, uncertainty quantification, and output interpretation",
                    "Response Mechanisms - how the system handles uncertain predictions or detected adversarial inputs"
                ],
                "example_questions": [
                    "How does your system validate and preprocess input data?",
                    "What mechanisms detect or prevent adversarial inputs?",
                    "How does the model handle uncertain or suspicious predictions?"
                ]
            }
        }

        if attack_type not in attack_focuses:
            return self.build_question_generation_prompt(
                detected_areas=[attack_type.value],
                reasoning=f"Falling back to legacy approach for {attack_type.value}",
                textual_dfd=textual_dfd
            )

        focus = attack_focuses[attack_type]

        return f"""### {focus['name'].upper()} SECURITY ANALYSIS
You are an expert ML security analyst specializing in **{focus['name'].lower()}**. Your mission is to identify vulnerabilities related to {focus['description']}.

### SYSTEM TO ANALYZE
{textual_dfd}

{context_section}

### VULNERABILITY FOCUS AREAS
Generate questions that probe for weaknesses in:
{chr(10).join([f"{i+1}. **{area.split(' - ')[0]}** - {area.split(' - ')[1]}" for i, area in enumerate(focus['focus_areas'])])}

### OUTPUT FORMAT
Generate 3-4 targeted questions with realistic multiple-choice answers. Each option should represent a different architectural approach or security posture:

{{
  "attack_type": "{attack_type.value}",
  "focus_area": "{focus['name']}",
  "questions_with_options": [
    {{
      "id": "{attack_type.value}_q1",
      "question": "Specific question about {focus['name'].lower()} vulnerabilities",
      "category": "one of: data_sources, pipeline_security, access_control, validation, detection, architecture",
      "options": [
        {{"id": "{attack_type.value}_q1_opt1", "text": "Specific realistic architectural option 1"}},
        {{"id": "{attack_type.value}_q1_opt2", "text": "Specific realistic architectural option 2"}},
        {{"id": "{attack_type.value}_q1_opt3", "text": "Specific realistic architectural option 3"}}
      ]
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Questions must be specific to {focus['name'].lower()} attack vectors
- Options should represent different security postures or architectural choices
- Focus on eliciting architectural and procedural information
- Output ONLY valid JSON
- Each question should target a different aspect of {focus['name'].lower()} prevention"""

    def _build_attack_context_section(self, context: Optional[ContextEnumeration]) -> str:
        """Build context section for attack-specific prompts"""
        if not context:
            return ""

        sections = []

        if context.attackers:
            attackers_str = "\n".join([
                f"- {a.description} (Skill: {a.skill_level.name}, Access: {a.access_level.name})"
                for a in context.attackers
            ])
            sections.append(f"**Known Attackers:**\\n{attackers_str}")

        if context.entry_points:
            entry_points_str = "\n".join([
                f"- {e.name}: {e.description} (Difficulty: {e.difficulty_of_entry.name})"
                for e in context.entry_points
            ])
            sections.append(f"**Identified Entry Points:**\\n{entry_points_str}")

        if context.assets:
            assets_str = "\n".join([f"- {a.name}: {a.description}" for a in context.assets])
            sections.append(f"**Protected Assets:**\\n{assets_str}")

        if context.assumptions:
            assumptions_str = "\n".join([f"- {s}" for s in context.assumptions])
            sections.append(f"**Current Assumptions:**\\n{assumptions_str}")

        return "### EXISTING SECURITY CONTEXT\\n" + "\\n\\n".join(sections) if sections else ""

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

    def build_modular_question_set(self, textual_dfd: str, attack_types: List[AttackType], context: Optional[ContextEnumeration] = None) -> Dict[str, Any]:
        """Generate attack-specific questions for multiple attack types"""

        prompts = {}
        for attack_type in attack_types:
            prompts[attack_type.value] = self.build_attack_specific_prompt(attack_type, textual_dfd, context)

        return {
            "modular_prompts": prompts,
            "attack_types": [at.value for at in attack_types],
            "generation_method": "modular_attack_specific"
        }

    def build_followup_prompt(self, missing_information: str, textual_dfd: str, conversation_history: List[ChatMessage]) -> str:
        conversation_text = ""
        for msg in conversation_history:
            role_label = "Assistant" if msg.role == "assistant" else "User"
            conversation_text += f"\n\n{role_label}: {msg.content}"

        return f"""### TASK
Based on the conversation so far and the analysis of missing information, generate follow-up questions with multiple choice answers to learn more about this system.

### MISSING INFORMATION
{missing_information}

### SYSTEM CONTEXT
{textual_dfd}

### CONVERSATION SO FAR
{conversation_text}

### OUTPUT FORMAT
For each follow-up question, provide exactly 3 plausible answer options that are specific and realistic:

{{
  "questions_with_options": [
    {{
      "id": "f1",
      "question": "follow-up question text here",
      "options": [
        {{
          "id": "f1_opt1",
          "text": "specific realistic answer option 1"
        }},
        {{
          "id": "f1_opt2",
          "text": "specific realistic answer option 2"
        }},
        {{
          "id": "f1_opt3",
          "text": "specific realistic answer option 3"
        }}
      ]
    }}
  ]
}}

CRITICAL: Output ONLY valid JSON. Make answer options specific and realistic, avoid generic options."""

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
