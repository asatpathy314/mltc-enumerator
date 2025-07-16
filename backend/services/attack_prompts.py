from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from schemas import ContextEnumeration, ChatRefinementRequest, ChatMessage


class AttackType(Enum):
    """Enumeration of different ML attack categories"""
    MODEL_POISONING = "model_poisoning"
    EVASION_ATTACKS = "evasion_attacks"
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_CAPABILITY = "resource_capability"
    SUPPLY_CHAIN = "supply_chain"
    INITIAL_ACCESS = "initial_access"
    DATA_EXTRACTION = "data_extraction"
    SERVICE_DISRUPTION = "service_disruption"


@dataclass
class AttackPromptResult:
    """Result from attack-specific question generation"""
    attack_type: AttackType
    questions_with_options: List[Dict[str, Any]]
    reasoning: str
    confidence_score: float = 0.8


class AttackSpecificPromptBuilder:
    """Modular system for generating attack-specific questions"""

    def __init__(self):
        self.attack_templates = {
            AttackType.MODEL_POISONING: self._build_model_poisoning_prompt,
            AttackType.EVASION_ATTACKS: self._build_evasion_attacks_prompt,
            # Future attack types can be added here
        }

    def generate_attack_specific_questions(
        self,
        attack_type: AttackType,
        textual_dfd: str,
        context: Optional[ContextEnumeration] = None
    ) -> str:
        """Generate questions specific to a given attack type"""

        if attack_type not in self.attack_templates:
            raise ValueError(f"No prompt template for attack type: {attack_type}")

        return self.attack_templates[attack_type](textual_dfd, context)

    def _build_model_poisoning_prompt(self, textual_dfd: str, context: Optional[ContextEnumeration] = None) -> str:
        """Generate questions specifically for model poisoning attacks"""

        context_section = ""
        if context and (context.attackers or context.assets):
            attackers_str = "\n".join([
                f"- {a.description} (Skill: {a.skill_level.name}, Access: {a.access_level.name})"
                for a in context.attackers
            ]) if context.attackers else "None identified yet"

            assets_str = "\n".join([
                f"- {a.name}: {a.description}"
                for a in context.assets
            ]) if context.assets else "None identified yet"

            context_section = f"""
### CURRENT CONTEXT
**Known Attackers:**
{attackers_str}

**Identified Assets:**
{assets_str}
"""

        return f"""### MODEL POISONING ATTACK ANALYSIS
You are an expert ML security analyst specializing in **model poisoning attacks**. Your task is to generate targeted questions that reveal vulnerabilities specific to training data poisoning, backdoor insertion, and model integrity compromise.

### ATTACK FOCUS: Model Poisoning
Model poisoning involves malicious manipulation of training data, model parameters, or the training pipeline to compromise model behavior, insert backdoors, or degrade performance.

### SYSTEM TO ANALYZE
{textual_dfd}

{context_section}

### QUESTION STRATEGY
Focus on eliciting information about:
1. **Training Data Sources** - origin, collection methods, validation processes
2. **Model Update Mechanisms** - how models are retrained, updated, or fine-tuned
3. **Data Pipeline Security** - sanitization, filtering, and integrity checks
4. **Access Controls** - who can modify training data or model parameters
5. **Model Validation** - testing procedures for detecting compromised models
6. **Supply Chain** - third-party datasets, pre-trained models, or training services

### OUTPUT FORMAT
Generate 3-4 specific questions with realistic multiple-choice answers:

{{
  "questions_with_options": [
    {{
      "id": "mp_q1",
      "question": "specific question about training data sources",
      "options": [
        {{"id": "mp_q1_opt1", "text": "specific realistic option 1"}},
        {{"id": "mp_q1_opt2", "text": "specific realistic option 2"}},
        {{"id": "mp_q1_opt3", "text": "specific realistic option 3"}}
      ]
    }}
  ]
}}

### REQUIREMENTS
- Questions must be specific to model poisoning vulnerabilities
- Answer options should be concrete and system-specific
- Avoid generic security questions
- Focus on architectural and procedural aspects
- Output ONLY valid JSON
"""

    def _build_evasion_attacks_prompt(self, textual_dfd: str, context: Optional[ContextEnumeration] = None) -> str:
        """Generate questions specifically for evasion attacks"""

        context_section = ""
        if context and (context.entry_points or context.assets):
            entry_points_str = "\n".join([
                f"- {e.name}: {e.description} (Difficulty: {e.difficulty_of_entry.name})"
                for e in context.entry_points
            ]) if context.entry_points else "None identified yet"

            assets_str = "\n".join([
                f"- {a.name}: {a.description}"
                for a in context.assets
            ]) if context.assets else "None identified yet"

            context_section = f"""
### CURRENT CONTEXT
**Identified Entry Points:**
{entry_points_str}

**Protected Assets:**
{assets_str}
"""

        return f"""### EVASION ATTACK ANALYSIS
You are an expert ML security analyst specializing in **evasion attacks**. Your task is to generate targeted questions that reveal vulnerabilities specific to adversarial examples, input manipulation, and model bypass techniques.

### ATTACK FOCUS: Evasion Attacks
Evasion attacks involve crafting malicious inputs that are misclassified by the model while appearing normal to humans, bypassing the model's intended behavior.

### SYSTEM TO ANALYZE
{textual_dfd}

{context_section}

### QUESTION STRATEGY
Focus on eliciting information about:
1. **Input Validation** - how inputs are preprocessed, validated, or sanitized
2. **Model Robustness** - adversarial training, input perturbation tolerance
3. **Detection Mechanisms** - systems for identifying suspicious inputs
4. **Input Sources** - where inputs come from and trust levels
5. **Model Architecture** - types of models, ensemble methods, confidence scoring
6. **Output Interpretation** - how model outputs are used in downstream decisions

### OUTPUT FORMAT
Generate 3-4 specific questions with realistic multiple-choice answers:

{{
  "questions_with_options": [
    {{
      "id": "ev_q1",
      "question": "specific question about input validation",
      "options": [
        {{"id": "ev_q1_opt1", "text": "specific realistic option 1"}},
        {{"id": "ev_q1_opt2", "text": "specific realistic option 2"}},
        {{"id": "ev_q1_opt3", "text": "specific realistic option 3"}}
      ]
    }}
  ]
}}

### REQUIREMENTS
- Questions must be specific to evasion attack vulnerabilities
- Answer options should be concrete and system-specific
- Focus on input processing and model robustness
- Avoid generic security questions
- Output ONLY valid JSON
"""

    def combine_attack_results(self, results: List[AttackPromptResult]) -> Dict[str, Any]:
        """Combine results from multiple attack-specific question generations"""

        all_questions = []
        attack_reasoning = {}

        for result in results:
            # Prefix question IDs with attack type to avoid conflicts
            for question in result.questions_with_options:
                question['id'] = f"{result.attack_type.value}_{question['id']}"
                for option in question['options']:
                    option['id'] = f"{result.attack_type.value}_{option['id']}"

            all_questions.extend(result.questions_with_options)
            attack_reasoning[result.attack_type.value] = {
                'reasoning': result.reasoning,
                'confidence': result.confidence_score
            }

        return {
            "questions_with_options": all_questions,
            "attack_reasoning": attack_reasoning,
            "total_questions": len(all_questions),
            "attack_types_analyzed": [r.attack_type.value for r in results]
        }

    def get_supported_attacks(self) -> List[AttackType]:
        """Return list of currently supported attack types"""
        return list(self.attack_templates.keys())


class ModularPromptBuilder:
    """Enhanced prompt builder that supports both modular and legacy approaches"""

    def __init__(self):
        self.legacy_builder = PromptBuilder()  # Existing system
        self.attack_builder = AttackSpecificPromptBuilder()  # New modular system

    def generate_modular_questions(
        self,
        textual_dfd: str,
        attack_types: Optional[List[AttackType]] = None,
        context: Optional[ContextEnumeration] = None
    ) -> Dict[str, Any]:
        """Generate questions using the modular attack-specific approach"""

        if attack_types is None:
            attack_types = [AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS]

        # Filter to only supported attack types
        supported_attacks = self.attack_builder.get_supported_attacks()
        attack_types = [at for at in attack_types if at in supported_attacks]

        if not attack_types:
            # Fallback to legacy approach
            legacy_prompt = self.legacy_builder.build_question_generation_prompt(
                detected_areas=[],
                reasoning="Fallback to legacy approach",
                textual_dfd=textual_dfd
            )
            return {"legacy_prompt": legacy_prompt, "attack_types": []}

        # Generate questions for each attack type
        results = []
        for attack_type in attack_types:
            prompt = self.attack_builder.generate_attack_specific_questions(
                attack_type, textual_dfd, context
            )
            results.append({
                'attack_type': attack_type,
                'prompt': prompt
            })

        return {
            "attack_specific_prompts": results,
            "attack_types": [at.value for at in attack_types]
        }

    def generate_legacy_questions(self, textual_dfd: str) -> str:
        """Generate questions using the legacy zero-shot approach"""
        return self.legacy_builder.build_question_generation_prompt(
            detected_areas=["all_categories"],
            reasoning="Legacy comprehensive approach",
            textual_dfd=textual_dfd
        )
