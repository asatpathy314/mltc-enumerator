from typing import List, Dict, Any, Optional
from schemas import ContextEnumeration, ThreatChain, ThreatCategory, Likert
from services.client import LLMClient
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ThreatChainGenerator:
    """
    Advanced threat chain generator that creates sophisticated ML-specific threat scenarios
    using comprehensive context analysis.
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    async def generate_threat_chains(self, context: ContextEnumeration) -> List[ThreatChain]:
        """
        Generate comprehensive threat chains using all available context.
        
        Args:
            context: Full context enumeration with attackers, entry points, assets, etc.
            
        Returns:
            List of detailed threat chains with mitigation strategies
        """
        logger.info(f"Generating threat chains for {len(context.attackers)} attackers, {len(context.entry_points)} entry points, {len(context.assets)} assets")
        
        # Generate multiple types of threat chains in parallel
        tasks = [
            self._generate_ml_specific_threats(context),
            self._generate_traditional_security_threats(context),
            self._generate_supply_chain_threats(context),
            self._generate_data_pipeline_threats(context)
        ]
        
        threat_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all threats
        all_threats = []
        for result in threat_results:
            if isinstance(result, Exception):
                logger.error(f"Threat generation task failed: {str(result)}")
                continue
            if isinstance(result, list):
                all_threats.extend(result)
        
        # Remove duplicates and ensure quality
        unique_threats = self._deduplicate_threats(all_threats)
        
        # Prioritize most critical threats (limit to top 15 for UI)
        prioritized_threats = self._prioritize_threats(unique_threats, context)[:15]
        
        logger.info(f"Generated {len(prioritized_threats)} high-quality threat chains")
        return prioritized_threats
    
    async def _generate_ml_specific_threats(self, context: ContextEnumeration) -> List[ThreatChain]:
        """Generate ML-specific threats like model poisoning, evasion attacks, etc."""
        
        prompt = self._build_ml_threat_prompt(context)
        
        messages = [
            {"role": "system", "content": """You are an expert ML security analyst specializing in machine learning threat modeling. 
Generate realistic, sophisticated threat chains that are specific to ML systems. Focus on unique ML attack vectors 
like model poisoning, adversarial examples, data extraction, and supply chain attacks on ML pipelines.
Output ONLY valid JSON."""},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.3)
        threat_data = json.loads(response)
        
        return [ThreatChain(**threat) for threat in threat_data.get("threat_chains", [])]
    
    async def _generate_traditional_security_threats(self, context: ContextEnumeration) -> List[ThreatChain]:
        """Generate traditional cybersecurity threats adapted for ML systems."""
        
        prompt = self._build_traditional_threat_prompt(context)
        
        messages = [
            {"role": "system", "content": """You are a cybersecurity expert analyzing traditional security threats in ML system contexts.
Generate threat chains that combine traditional attack vectors (like unauthorized access, privilege escalation) 
with ML system components. Focus on how classic attacks can be adapted to compromise ML systems.
Output ONLY valid JSON."""},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.3)
        threat_data = json.loads(response)
        
        return [ThreatChain(**threat) for threat in threat_data.get("threat_chains", [])]
    
    async def _generate_supply_chain_threats(self, context: ContextEnumeration) -> List[ThreatChain]:
        """Generate supply chain and dependency-related threats."""
        
        prompt = self._build_supply_chain_threat_prompt(context)
        
        messages = [
            {"role": "system", "content": """You are a supply chain security expert analyzing ML system dependencies.
Generate threat chains that exploit vulnerabilities in ML supply chains including: third-party models, datasets, 
training frameworks, containers, package dependencies, and cloud ML services.
Output ONLY valid JSON."""},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.3)
        threat_data = json.loads(response)
        
        return [ThreatChain(**threat) for threat in threat_data.get("threat_chains", [])]
    
    async def _generate_data_pipeline_threats(self, context: ContextEnumeration) -> List[ThreatChain]:
        """Generate threats specific to data collection and processing pipelines."""
        
        prompt = self._build_data_pipeline_threat_prompt(context)
        
        messages = [
            {"role": "system", "content": """You are a data security expert analyzing ML data pipelines.
Generate threat chains that target data collection, processing, storage, and governance in ML systems.
Focus on data poisoning, privacy attacks, unauthorized data access, and pipeline manipulation.
Output ONLY valid JSON."""},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.chat_completion_json(messages=messages, temperature=0.3)
        threat_data = json.loads(response)
        
        return [ThreatChain(**threat) for threat in threat_data.get("threat_chains", [])]

    def _build_ml_threat_prompt(self, context: ContextEnumeration) -> str:
        """Build prompt for ML-specific threat generation."""
        
        context_summary = self._build_context_summary(context)
        
        return f"""### ML SECURITY THREAT ANALYSIS

{context_summary}

### TASK
Generate 3-4 sophisticated ML-specific threat chains that exploit unique ML vulnerabilities. Focus on:

**ML Attack Categories:**
- Model Poisoning: Malicious training data or model parameter manipulation
- Adversarial Attacks: Crafted inputs to cause misclassification  
- Model Extraction: Stealing model parameters or architecture
- Data Extraction: Recovering training data from models
- Membership Inference: Determining if data was used in training
- Supply Chain: Compromised ML libraries, pre-trained models, or datasets

### OUTPUT FORMAT
{{
  "threat_chains": [
    {{
      "name": "Descriptive threat name",
      "chain": ["Step 1: Initial access", "Step 2: Reconnaissance", "Step 3: Attack execution", "Step 4: Impact"],
      "category": "one of: spoofing, tampering, repudiation, information_disclosure, denial_of_service, elevation_of_privilege, other",
      "description": "Detailed technical description of the attack and its impact on the ML system",
      "mitre_atlas": "Relevant MITRE ATLAS technique (e.g., AML.T0043 - Craft Adversarial Data)",
      "mitre_attack": "Relevant MITRE ATT&CK technique (e.g., T1190 - Exploit Public-Facing Application)",
      "mitigations": ["Specific mitigation 1", "Specific mitigation 2", "Specific mitigation 3"]
    }}
  ]
}}

CRITICAL: Generate realistic, technically accurate threat chains specific to ML systems. Each chain should be 4-6 steps showing progression from initial access to final impact."""

    def _build_traditional_threat_prompt(self, context: ContextEnumeration) -> str:
        """Build prompt for traditional security threats in ML context."""
        
        context_summary = self._build_context_summary(context)
        
        return f"""### TRADITIONAL SECURITY THREATS IN ML SYSTEMS

{context_summary}

### TASK
Generate 2-3 traditional cybersecurity threat chains adapted for ML system environments. Focus on:

**Traditional Attack Vectors Applied to ML:**
- Unauthorized Access: Gaining access to ML training infrastructure or model endpoints
- Privilege Escalation: Escalating from limited access to full ML pipeline control
- Data Breaches: Stealing sensitive training data or model artifacts
- Service Disruption: DDoS attacks on ML inference endpoints
- Man-in-the-Middle: Intercepting ML API communications
- Credential Attacks: Compromising ML engineer or service accounts

### OUTPUT FORMAT
{{
  "threat_chains": [
    {{
      "name": "Descriptive threat name",
      "chain": ["Step 1: Initial compromise", "Step 2: Lateral movement", "Step 3: Privilege escalation", "Step 4: ML system compromise"],
      "category": "one of: spoofing, tampering, repudiation, information_disclosure, denial_of_service, elevation_of_privilege, other",
      "description": "How traditional attacks are adapted to target ML system components",
      "mitre_atlas": "Relevant MITRE ATLAS technique if applicable",
      "mitre_attack": "Primary MITRE ATT&CK technique (e.g., T1078 - Valid Accounts)",
      "mitigations": ["Security control 1", "Security control 2", "Security control 3"]
    }}
  ]
}}

Generate chains showing how attackers use traditional methods to compromise ML systems."""

    def _build_supply_chain_threat_prompt(self, context: ContextEnumeration) -> str:
        """Build prompt for supply chain threats."""
        
        context_summary = self._build_context_summary(context)
        
        return f"""### ML SUPPLY CHAIN THREAT ANALYSIS

{context_summary}

### TASK
Generate 2-3 supply chain threat chains targeting ML system dependencies. Focus on:

**ML Supply Chain Vectors:**
- Malicious Pre-trained Models: Backdoored models from model hubs
- Compromised Datasets: Poisoned public datasets or data sources
- Dependency Attacks: Malicious packages in ML libraries (PyPI, conda)
- Container Attacks: Compromised ML training or inference containers
- Cloud Service Attacks: Compromised ML platform services (AWS SageMaker, etc.)
- Third-party Integration Attacks: Compromised ML APIs or services

### OUTPUT FORMAT
{{
  "threat_chains": [
    {{
      "name": "Supply chain attack name",
      "chain": ["Step 1: Supply chain compromise", "Step 2: Distribution", "Step 3: Integration", "Step 4: Activation/Impact"],
      "category": "one of: spoofing, tampering, repudiation, information_disclosure, denial_of_service, elevation_of_privilege, other",
      "description": "How supply chain compromise leads to ML system compromise",
      "mitre_atlas": "Relevant MITRE ATLAS technique",
      "mitre_attack": "Relevant MITRE ATT&CK technique (e.g., T1195 - Supply Chain Compromise)",
      "mitigations": ["Supply chain security control 1", "Verification method 2", "Monitoring approach 3"]
    }}
  ]
}}

Focus on realistic supply chain attacks that could compromise ML systems through their dependencies."""

    def _build_data_pipeline_threat_prompt(self, context: ContextEnumeration) -> str:
        """Build prompt for data pipeline threats."""
        
        context_summary = self._build_context_summary(context)
        
        return f"""### ML DATA PIPELINE THREAT ANALYSIS

{context_summary}

### TASK
Generate 2-3 threat chains targeting ML data collection and processing pipelines. Focus on:

**Data Pipeline Attack Vectors:**
- Data Source Compromise: Poisoning data at collection points
- Pipeline Injection: Injecting malicious data into processing streams
- Data Exfiltration: Stealing sensitive training or inference data
- Privacy Attacks: De-anonymizing or linking sensitive data
- Data Governance Bypass: Circumventing data protection controls
- Stream Manipulation: Real-time data stream tampering

### OUTPUT FORMAT
{{
  "threat_chains": [
    {{
      "name": "Data pipeline attack name",
      "chain": ["Step 1: Data source access", "Step 2: Pipeline infiltration", "Step 3: Data manipulation", "Step 4: ML system impact"],
      "category": "one of: spoofing, tampering, repudiation, information_disclosure, denial_of_service, elevation_of_privilege, other",
      "description": "How data pipeline compromise affects ML system integrity and privacy",
      "mitre_atlas": "Relevant MITRE ATLAS technique",
      "mitre_attack": "Relevant MITRE ATT&CK technique",
      "mitigations": ["Data protection control 1", "Pipeline security measure 2", "Monitoring approach 3"]
    }}
  ]
}}

Generate realistic data pipeline attacks that leverage the specific context provided."""

    def _build_context_summary(self, context: ContextEnumeration) -> str:
        """Build a comprehensive context summary for threat prompts."""
        
        sections = []
        
        # System overview
        sections.append(f"**SYSTEM OVERVIEW:**\n{context.textual_dfd}")
        
        # Attackers
        if context.attackers:
            attacker_list = []
            for attacker in context.attackers:
                skill = Likert(attacker.skill_level).name.replace('_', ' ').title()
                access = Likert(attacker.access_level).name.replace('_', ' ').title()
                attacker_list.append(f"- {attacker.description} (Skill: {skill}, Access: {access}, Attack Probability: {attacker.prob_of_attack:.2f})")
            sections.append(f"**THREAT ACTORS:**\n" + "\n".join(attacker_list))
        
        # Entry points
        if context.entry_points:
            entry_list = []
            for entry in context.entry_points:
                difficulty = Likert(entry.difficulty_of_entry).name.replace('_', ' ').title()
                entry_list.append(f"- {entry.name}: {entry.description} (Entry Probability: {entry.prob_of_entry:.2f}, Difficulty: {difficulty})")
            sections.append(f"**ATTACK ENTRY POINTS:**\n" + "\n".join(entry_list))
        
        # Assets
        if context.assets:
            asset_list = []
            for asset in context.assets:
                failure_modes = ", ".join(asset.failure_modes) if asset.failure_modes else "Not specified"
                asset_list.append(f"- {asset.name}: {asset.description} (Failure modes: {failure_modes})")
            sections.append(f"**CRITICAL ASSETS:**\n" + "\n".join(asset_list))
        
        # Assumptions
        if context.assumptions:
            assumptions_list = "\n".join([f"- {assumption}" for assumption in context.assumptions])
            sections.append(f"**SECURITY ASSUMPTIONS:**\n{assumptions_list}")
        
        # Q&A insights
        if context.questions and context.answers:
            qa_pairs = []
            for q, a in zip(context.questions, context.answers):
                if q.strip() and a.strip():
                    qa_pairs.append(f"Q: {q}\nA: {a}")
            if qa_pairs:
                sections.append(f"**ADDITIONAL CONTEXT:**\n" + "\n\n".join(qa_pairs))
        
        return "\n\n".join(sections)

    def _deduplicate_threats(self, threats: List[ThreatChain]) -> List[ThreatChain]:
        """Remove duplicate or very similar threats."""
        
        seen_names = set()
        unique_threats = []
        
        for threat in threats:
            # Create a key based on name and first few chain steps
            key = threat.name.lower().strip()
            
            if key not in seen_names:
                seen_names.add(key)
                unique_threats.append(threat)
        
        return unique_threats

    def _prioritize_threats(self, threats: List[ThreatChain], context: ContextEnumeration) -> List[ThreatChain]:
        """Prioritize threats based on context and threat characteristics."""
        
        def threat_score(threat: ThreatChain) -> float:
            score = 0.0
            
            # Prioritize by category
            category_weights = {
                ThreatCategory.information_disclosure: 1.0,
                ThreatCategory.tampering: 0.9,
                ThreatCategory.elevation_of_privilege: 0.8,
                ThreatCategory.denial_of_service: 0.7,
                ThreatCategory.spoofing: 0.6,
                ThreatCategory.repudiation: 0.5,
                ThreatCategory.other: 0.4
            }
            score += category_weights.get(threat.category, 0.4)
            
            # Prioritize threats with more detailed chains
            score += min(len(threat.chain) * 0.1, 0.5)
            
            # Prioritize threats with specific mitigations
            score += min(len(threat.mitigations) * 0.05, 0.3)
            
            # Prioritize ML-specific threats
            ml_keywords = ['model', 'training', 'adversarial', 'poisoning', 'inference', 'data', 'ml', 'ai']
            threat_text = (threat.name + " " + threat.description).lower()
            ml_relevance = sum(1 for keyword in ml_keywords if keyword in threat_text)
            score += min(ml_relevance * 0.1, 0.4)
            
            return score
        
        # Sort by score (descending)
        sorted_threats = sorted(threats, key=threat_score, reverse=True)
        
        return sorted_threats 