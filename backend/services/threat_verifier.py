from typing import List, Dict, Any, Optional
from schemas import (
    ThreatChain, ContextEnumeration, ThreatVerificationQuestion, 
    ThreatVerificationAnswer, FilteredThreatChain, MultipleChoiceOption
)
from services.client import LLMClient
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class ThreatVerifier:
    """
    Service for generating verification questions for threats and filtering implausible ones.
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def generate_verification_questions(
        self, 
        threat_chains: List[ThreatChain], 
        context: ContextEnumeration
    ) -> List[ThreatVerificationQuestion]:
        """
        Generate verification questions to assess threat plausibility.
        
        Args:
            threat_chains: List of generated threat chains
            context: System context for generating relevant questions
            
        Returns:
            List of verification questions for user to answer
        """
        logger.info(f"Generating verification questions for {len(threat_chains)} threats")
        
        # Generate questions for each threat
        questions = []
        for threat in threat_chains:
            threat_questions = await self._generate_questions_for_threat(threat, context)
            questions.extend(threat_questions)
        
        logger.info(f"Generated {len(questions)} verification questions")
        return questions
    
    async def _generate_questions_for_threat(
        self, 
        threat: ThreatChain, 
        context: ContextEnumeration
    ) -> List[ThreatVerificationQuestion]:
        """Generate 2-3 verification questions for a single threat."""
        
        prompt = self._build_verification_prompt(threat, context)
        
        messages = [
            {
                "role": "system", 
                "content": """You are a security expert generating verification questions to assess threat plausibility. 
Focus on key prerequisites, environmental factors, and feasibility constraints that would make this threat possible or impossible.
Output ONLY valid JSON."""
            },
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.2)
        data = json.loads(response)
        
        questions = []
        for q_data in data.get("questions", []):
            options = [
                MultipleChoiceOption(
                    id=opt["id"],
                    text=opt["text"],
                    is_editable=opt.get("is_editable", True)
                ) for opt in q_data.get("options", [])
            ]
            
            question = ThreatVerificationQuestion(
                id=q_data["id"],
                threat_name=threat.name,
                question=q_data["question"],
                options=options,
                category=q_data.get("category", "feasibility")
            )
            questions.append(question)
        
        return questions
    
    def _build_verification_prompt(self, threat: ThreatChain, context: ContextEnumeration) -> str:
        """Build verification prompt for a specific threat."""
        
        # Build context summary
        context_summary = self._build_context_summary(context)
        
        return f"""### THREAT VERIFICATION ANALYSIS

**THREAT TO VERIFY:**
Name: {threat.name}
Category: {threat.category.value}
Description: {threat.description}

**ATTACK CHAIN:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(threat.chain)])}

**MITRE TECHNIQUES:**
- ATLAS: {threat.mitre_atlas}
- ATT&CK: {threat.mitre_attack}

{context_summary}

### TASK
Generate 2-3 focused verification questions to assess whether this threat is plausible in the given context.
Focus on critical prerequisites, environmental factors, and feasibility constraints.

### QUESTION CATEGORIES
- **feasibility**: Technical feasibility given system architecture
- **context**: Environmental and organizational factors
- **prerequisites**: Required attacker capabilities and access
- **impact**: Realistic impact assessment

### OUTPUT FORMAT
{{
  "questions": [
    {{
      "id": "{threat.name.lower().replace(' ', '_')}_q1",
      "question": "Specific question about threat feasibility or prerequisites",
      "category": "one of: feasibility, context, prerequisites, impact",
      "options": [
        {{"id": "opt1", "text": "Option indicating high plausibility", "is_editable": true}},
        {{"id": "opt2", "text": "Option indicating medium plausibility", "is_editable": true}},
        {{"id": "opt3", "text": "Option indicating low plausibility", "is_editable": true}},
        {{"id": "opt4", "text": "Not applicable / Unknown", "is_editable": true}}
      ]
    }}
  ]
}}

REQUIREMENTS:
- Generate exactly 2-3 questions per threat
- Questions must be specific to the threat and context
- Options should clearly differentiate plausibility levels
- Focus on factors that could make the threat impossible or unlikely
- Output ONLY valid JSON"""
    
    def _build_context_summary(self, context: ContextEnumeration) -> str:
        """Build a context summary for threat verification."""
        
        sections = []
        
        if context.textual_dfd:
            sections.append(f"**SYSTEM OVERVIEW:**\n{context.textual_dfd}")
        
        if context.attackers:
            attacker_list = []
            for attacker in context.attackers:
                attacker_list.append(f"- {attacker.description}")
            sections.append(f"**THREAT ACTORS:**\n" + "\n".join(attacker_list))
        
        if context.entry_points:
            entry_list = []
            for entry in context.entry_points:
                entry_list.append(f"- {entry.name}: {entry.description}")
            sections.append(f"**ENTRY POINTS:**\n" + "\n".join(entry_list))
        
        if context.assets:
            asset_list = []
            for asset in context.assets:
                asset_list.append(f"- {asset.name}: {asset.description}")
            sections.append(f"**CRITICAL ASSETS:**\n" + "\n".join(asset_list))
        
        if context.assumptions:
            assumptions_list = "\n".join([f"- {assumption}" for assumption in context.assumptions])
            sections.append(f"**SECURITY ASSUMPTIONS:**\n{assumptions_list}")
        
        return "\n\n".join(sections)
    
    async def filter_threats_by_verification(
        self,
        threat_chains: List[ThreatChain],
        verification_answers: List[ThreatVerificationAnswer],
        context: ContextEnumeration
    ) -> List[FilteredThreatChain]:
        """
        Filter threats based on verification answers using AI analysis.
        
        Args:
            threat_chains: Original threat chains
            verification_answers: User's verification responses
            context: System context
            
        Returns:
            List of filtered threats with plausibility scores and reasoning
        """
        logger.info(f"Filtering {len(threat_chains)} threats based on {len(verification_answers)} verification answers")
        
        # Group answers by threat
        answers_by_threat = {}
        for answer in verification_answers:
            if answer.threat_name not in answers_by_threat:
                answers_by_threat[answer.threat_name] = []
            answers_by_threat[answer.threat_name].append(answer)
        
        # Analyze each threat
        filtered_threats = []
        for threat in threat_chains:
            threat_answers = answers_by_threat.get(threat.name, [])
            filtered_threat = await self._analyze_threat_plausibility(threat, threat_answers, context)
            filtered_threats.append(filtered_threat)
        
        # Sort by plausibility score (highest first)
        filtered_threats.sort(key=lambda x: x.plausibility_score, reverse=True)
        
        kept_count = sum(1 for ft in filtered_threats if ft.kept)
        removed_count = len(filtered_threats) - kept_count
        
        logger.info(f"Filtering complete: {kept_count} threats kept, {removed_count} removed")
        return filtered_threats
    
    async def _analyze_threat_plausibility(
        self,
        threat: ThreatChain,
        answers: List[ThreatVerificationAnswer],
        context: ContextEnumeration
    ) -> FilteredThreatChain:
        """Analyze a single threat's plausibility based on verification answers."""
        
        if not answers:
            # No verification answers - keep with medium score
            return FilteredThreatChain(
                threat_chain=threat,
                plausibility_score=0.5,
                reasoning="No verification answers provided - kept with medium confidence",
                kept=True
            )
        
        prompt = self._build_analysis_prompt(threat, answers, context)
        
        messages = [
            {
                "role": "system",
                "content": """You are a security expert analyzing threat plausibility based on verification answers.
Provide objective analysis considering technical feasibility, environmental constraints, and realistic attack scenarios.
Output ONLY valid JSON."""
            },
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.1)
        data = json.loads(response)
        
        plausibility_score = float(data.get("plausibility_score", 0.5))
        reasoning = data.get("reasoning", "Analysis unavailable")
        
        # Determine if threat should be kept (threshold: 0.3)
        kept = plausibility_score >= 0.3
        
        return FilteredThreatChain(
            threat_chain=threat,
            plausibility_score=plausibility_score,
            reasoning=reasoning,
            kept=kept
        )
    
    def _build_analysis_prompt(
        self,
        threat: ThreatChain,
        answers: List[ThreatVerificationAnswer],
        context: ContextEnumeration
    ) -> str:
        """Build analysis prompt for threat plausibility assessment."""
        
        # Format verification answers
        answers_text = []
        for answer in answers:
            if answer.custom_answer:
                answers_text.append(f"Q: {answer.question_id}\nA: {answer.custom_answer} (Confidence: {answer.confidence_level}/5)")
            elif answer.selected_option_id:
                answers_text.append(f"Q: {answer.question_id}\nA: {answer.selected_option_id} (Confidence: {answer.confidence_level}/5)")
        
        answers_summary = "\n\n".join(answers_text) if answers_text else "No answers provided"
        
        context_summary = self._build_context_summary(context)
        
        return f"""### THREAT PLAUSIBILITY ANALYSIS

**THREAT TO ANALYZE:**
Name: {threat.name}
Category: {threat.category.value}
Description: {threat.description}

**ATTACK CHAIN:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(threat.chain)])}

{context_summary}

**VERIFICATION ANSWERS:**
{answers_summary}

### TASK
Analyze the plausibility of this threat given the system context and verification answers.
Consider:
- Technical feasibility in the described environment
- Realistic attacker capabilities and motivations
- Environmental and organizational constraints
- Logical consistency of the attack chain

### OUTPUT FORMAT
{{
  "plausibility_score": 0.0-1.0,
  "reasoning": "Detailed explanation of why this threat is/isn't plausible given the context and answers. Consider technical feasibility, environmental factors, and realistic constraints.",
  "key_factors": [
    "Factor 1 affecting plausibility",
    "Factor 2 affecting plausibility"
  ]
}}

SCORING GUIDELINES:
- 0.8-1.0: Highly plausible, all prerequisites likely met
- 0.6-0.8: Plausible with some conditions
- 0.4-0.6: Moderately plausible, some constraints
- 0.2-0.4: Low plausibility, significant constraints
- 0.0-0.2: Implausible given the context

Output ONLY valid JSON.""" 