from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from services.client import LLMClient, ModelType
import logging
import sys
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mltc_api.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MLTC API",
    version="0.1.0",
    docs_url="/",           # swagger on root
    redoc_url=None          # disable ReDoc because it's not needed
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://frontend:3000",   # Docker internal network
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

logger.info("MLTC API starting up...")

@app.get("/ping", response_model=PingResponse, status_code=status.HTTP_200_OK)
async def ping() -> PingResponse:
    """
    Health-check style endpoint.
    Returns JSON: {"message": "pong"}.
    """
    logger.info("Ping endpoint called")
    response = PingResponse(message="pong")
    logger.debug(f"Ping response: {response}")
    return response

@app.post("/enumerate", response_model=ContextEnumeration, status_code=status.HTTP_200_OK)
async def enumerate_context(request: ContextEnumeration) -> ContextEnumeration:
    """
    Unified endpoint that either generates a brand-new context enumeration (when no attackers/entry_points/assets
    are supplied) **or** refines the provided context (when those lists are non-empty).
    """
    start_time = time.time()
    logger.info("Enumerate endpoint called")

    try:
        # Instantiate LLM client once per request
        llm = LLMClient(ModelType.LOCAL_LM_STUDIO)

        # Decide whether this is an initial enumeration or a refinement request
        is_initial = not (request.attackers or request.entry_points or request.assets)
        logger.debug(f"Request classified as {'initial' if is_initial else 'regeneration'} enumeration")

        # ---------------------------
        # Prompt construction helpers
        # ---------------------------
        def _build_hint_section() -> str:
            return f"\n\n### HINT\n{request.extra_prompt}" if request.extra_prompt else ""

        def _build_qa_section() -> str:
            if not (request.questions and request.answers):
                return ""
            qa_pairs = [
                f"Q{i+1}: {q}\nA{i+1}: {a}"
                for i, (q, a) in enumerate(zip(request.questions, request.answers))
                if a and a.strip()
            ]
            return ("\n\n### CONTEXTUAL Q&A\n" + "\n\n".join(qa_pairs)) if qa_pairs else ""

        # ---------------
        # Build the prompt
        # ---------------
        if is_initial:
            prompt = f"""### ROLE
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
{request.textual_dfd}{_build_hint_section()}{_build_qa_section()}
"""
        else:
            attackers_str = "\n".join([
                f"- {a.description} (Skill: {a.skill_level.name}, Access: {a.access_level.name})" for a in request.attackers
            ])
            entry_points_str = "\n".join([f"- {e.name}: {e.description}" for e in request.entry_points])
            assets_str = "\n".join([f"- {a.name}: {a.description}" for a in request.assets])
            assumptions_str = "\n".join([f"- {s}" for s in request.assumptions])

            prompt = f"""### ROLE
You are a senior security-threat-modeling analyst.

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

CRITICAL: Output ONLY the JSON object. ENSURE THAT THE FORMAT IS FOLLOWED EXACTLY. Use empty lists where appropriate.

### INPUT
DFD:
{request.textual_dfd}{_build_hint_section()}{_build_qa_section()}
"""

        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.debug(f"Prompt: {prompt}")

        # ----------------
        # Call the LLM
        # ----------------
        response_schema = ContextEnumeration.model_json_schema()
        messages = [
            {"role": "system", "content": "You are a senior security-threat-modeling analyst."},
            {"role": "user", "content": prompt},
        ]

        json_str = llm.chat_completion_json(
            messages=messages,
            temperature=0.0 if is_initial else 0.2,
            response_schema=response_schema,
        )

        logger.info(f"Raw response: {json_str}")

        # Ensure required fields exist before validation
        data = json.loads(json_str)
        data["textual_dfd"] = request.textual_dfd
        # Only include extra_prompt if provided by the caller
        if request.extra_prompt is not None:
            data["extra_prompt"] = request.extra_prompt

        result = ContextEnumeration.model_validate(data)

        # Preserve Q&A arrays in case LLM dropped them
        # result.questions = request.questions or []
        # result.answers = request.answers or []

        processing_time = time.time() - start_time
        logger.info(f"Enumerate endpoint completed successfully in {processing_time:.2f}s")
        logger.debug(
            f"Response contains: {len(result.attackers)} attackers, {len(result.entry_points)} entry points, "
            f"{len(result.assets)} assets, {len(result.assumptions)} assumptions"
        )

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in enumerate endpoint after {processing_time:.2f}s: {str(e)}", exc_info=True)
        raise

@app.post("/generate", response_model=ThreatEnumeration, status_code=status.HTTP_200_OK)
async def generate(request: ContextEnumeration) -> ThreatEnumeration:
    """
    Generate threat chains.
    """
    start_time = time.time()
    logger.info("Generate endpoint called")
    logger.debug(f"Request data: textual_dfd length={len(request.textual_dfd)}, attackers={len(request.attackers)}, entry_points={len(request.entry_points)}, assets={len(request.assets)}")
    
    try:
        # For now, return a placeholder - this endpoint needs full implementation
        # TODO: Implement threat chain generation
        placeholder_result = ThreatEnumeration(threat_chains=[])
        
        processing_time = time.time() - start_time
        logger.info(f"Generate endpoint completed in {processing_time:.2f}s")
        return placeholder_result
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in generate endpoint after {processing_time:.2f}s: {str(e)}", exc_info=True)
        raise
@app.post("/refine", response_model=ChatRefinementResponse, status_code=status.HTTP_200_OK)
async def refine_with_chat(request: ChatRefinementRequest) -> ChatRefinementResponse:
    """
    ML-aware chat interface for DFD refinement.
    
    This endpoint replaces /dfd/refine with an intelligent conversation that:
    1. Analyzes the DFD for potential ML attack vectors
    2. Asks targeted questions about specific ML security concerns
    3. Extracts structured answers from natural language responses
    4. Determines when enough information has been gathered
    """
    start_time = time.time()
    logger.info("Chat refinement endpoint called")
    logger.debug(f"DFD length: {len(request.textual_dfd)}, conversation history: {len(request.conversation_history)} messages")
    
    try:
        llm = LLMClient(ModelType.LOCAL_LM_STUDIO)
        
        # ML Attack Knowledge Base - areas to investigate
        ml_attack_knowledge = {
            "reconnaissance_discovery": {
                "keywords": ["documentation", "public", "research", "architecture", "dataset"],
            },
            "resource_capability_development": {
                "keywords": ["training environment", "gpu", "compute", "staging", "development"],
            },
            "supply_chain_dependency_poisoning": {
                "keywords": ["dependencies", "packages", "containers", "provenance", "integrity"],
            },
            "initial_ongoing_access_vectors": {
                "keywords": ["authentication", "api access", "plugins", "social engineering", "credentials"],
            },
            "model_data_extraction_privacy": {
                "keywords": ["inference api", "embeddings", "training data", "privacy", "extraction"],
            },
            "model_manipulation_persistence": {
                "keywords": ["model weights", "fine-tuning", "deserialization", "integrity", "backdoors"],
            },
            "adversarial_service_disruption": {
                "keywords": ["adversarial inputs", "denial of service", "performance", "monitoring", "validation"],
            }
        }
        
        # Determine if this is the first interaction or a follow-up
        is_initial = len(request.conversation_history) == 0
        
        if is_initial:
            # Initial analysis: use LLM to analyze DFD for ML attack indicators
            logger.debug("Initial LLM-based analysis of DFD")
            
            # Use LLM to analyze the DFD and determine relevant ML attack areas
            analysis_prompt = f"""### TASK
Analyze the provided DFD and determine which ML attack categories are relevant to the system.

### ML ATTACK CATEGORIES

1. **Reconnaissance/Discovery** - Information gathering about ML system architecture, datasets, and public exposure
2. **Resource Capability Development** - Attacker staging and capability development using available resources
3. **Supply Chain Dependency Poisoning** - Comprehensive supply chain security including dependencies, containers, and provenance
4. **Initial Ongoing Access Vectors** - Authentication bypass, API security, social engineering, and persistent access
5. **Model Data Extraction Privacy** - Model parameter extraction, training data recovery, and privacy attacks
6. **Model Manipulation Persistence** - Model integrity attacks, backdoors, and persistent manipulation
7. **Adversarial Service Disruption** - Input-based attacks causing misclassification or service degradation

### DFD TO ANALYZE
{request.textual_dfd}

### OUTPUT FORMAT
{{
  "analysis": {{
    "relevant_areas": ["list of the relevant categories"],
    "reasoning": "brief explanation of why these areas are relevant",
    "ml_system_type": "description of what type of ML system this appears to be"
  }}
}}

CRITICAL: Output ONLY valid JSON. Do NOT add any additional formatting. Do NOT add backticks. Focus on ML security questions."""
            
            messages = [
                {"role": "system", "content": "You are a machine learning expert analyzing a data-flow diagram."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis_response = llm.chat_completion_json(
                messages=messages,
                temperature=0.0,
                response_schema={}
            )
            
            analysis_data = json.loads(analysis_response)
            logger.debug(f"LLM analysis result: {analysis_data}")
            
            analysis = analysis_data.get("analysis", {})
            detected_areas = analysis.get("relevant_areas", ["supply_chain_dependency_poisoning", "reconnaissance_discovery"])
            reasoning = analysis.get("reasoning", "General ML security assessment")
            
            logger.info(f"LLM detected relevant ML attack areas: {detected_areas}")
            
            # Generate system-specific questions using template questions as examples
            question_generation_prompt = f"""### TASK
Let's think step by step.

Based on the DFD analysis and the priority ML attack areas identified, generate up to 10 specific, tailored elicitation questions to learn more about this system.

### PRIORITY ATTACK AREAS
{', '.join(detected_areas[:2])}

Reasoning: {reasoning}

### SYSTEM BEING ANALYZED
{request.textual_dfd}

### OUTPUT FORMAT
{{
  "specific_questions": [
    "question 1",
    "question 2",
    ...
    "question n",
  ]
}}

CRITICAL: OUTPUT ONLY VALID JSON WITH NO ADDITIONAL FORMATTING."""
            
            messages = [
                {"role": "system", "content": "You are an ML expert generating specific, targeted questions to elicit valuable information for this particular system."},
                {"role": "user", "content": question_generation_prompt}
            ]
            
            question_response = llm.chat_completion_json(
                messages=messages,
                temperature=0.3,
                response_schema={}
            )
            
            question_data = json.loads(question_response)
            initial_questions = question_data.get("specific_questions")
            
            logger.debug(f"Generated specific questions: {initial_questions}")
            
            assistant_response = f"""I'm analyzing your data-flow diagram for ML security concerns. Based on my analysis, this appears to be {analysis.get("ml_system_type", "an ML system")}.

{reasoning}

Let me start with some specific security questions about your system:

{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(initial_questions))}

Please provide as much detail as you can about these aspects of your ML system."""
            
            return ChatRefinementResponse(
                message="need_more_info",
                status="need_more_info",
                assistant_response=assistant_response,
                refined_dfd="",
                structured_answers=[],
                coverage_analysis={"detected_areas": detected_areas, "covered_areas": []}
            )
        
        else:
            # Follow-up: extract structured info and decide next steps
            logger.debug("Processing follow-up conversation")
            
            # extract messages

            chat_messages = [msg for msg in request.conversation_history if msg.role == "assistant"]
            user_messages = [msg for msg in request.conversation_history if msg.role == "user"]

            if not user_messages:
                raise ValueError("No user messages found in conversation history")
            
            latest_chat_message = chat_messages[-1].content
            latest_user_response = user_messages[-1].content
            
            # Extract structured information from user response
            extraction_prompt = f"""### TASK
Analyze the user's response about their ML system and extract specific security-relevant information. 

### MODEL QUESTIONS
{latest_chat_message}

### USER'S RESPONSE
"{latest_user_response}"

### ORIGINAL DFD CONTEXT
{request.textual_dfd}

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
            
            messages = [
                {"role": "system", "content": "You are an ML security analyst."},
                {"role": "user", "content": extraction_prompt}
            ]
            
            extraction_response = llm.chat_completion_json(
                messages=messages,
                temperature=0.0,
                response_schema={}  # Allow flexible JSON response
            )
            
            extraction_data = json.loads(extraction_response)
            logger.debug(f"Extraction result: {extraction_data}")
            
            # Convert extractions to StructuredAnswer objects
            new_structured_answers = []
            for ext in extraction_data.get("extractions", []):
                try:
                    structured_answer = StructuredAnswer(
                        question=ext["question"],
                        extracted_answer=ext["extracted_answer"],
                    )
                    new_structured_answers.append(structured_answer)
                except Exception as e:
                    logger.warning(f"Failed to create StructuredAnswer: {e}")
            
            # Combine with previous structured answers
            all_structured_answers = request.structured_answers + new_structured_answers
            
            # Build conversation context for use in follow-up and final extraction
            conversation_text = ""
            for msg in request.conversation_history:
                role_label = "Assistant" if msg.role == "assistant" else "User"
                conversation_text += f"\n\n{role_label}: {msg.content}"
            
            coverage = extraction_data.get("coverage_assessment", {})
            needs_followup = coverage.get("needs_followup", True)
            
            if needs_followup:
                # Generate system-specific follow-up questions
                missing_information = coverage.get("missing_information", "")
                
                # Generate specific follow-up questions using templates as examples
                followup_prompt = f"""### TASK
Based on the conversation so far and the analysis of missing information, generate follow-up questions to learn more about this system.

### MISSING INFORMATION
{missing_information}

### SYSTEM CONTEXT
{request.textual_dfd}

### CONVERSATION SO FAR
{conversation_text[-1000:]}  # Last 1000 chars to provide context

### OUTPUT FORMAT
{{
  "followup_questions": [list of followup questions as strings]
}}

CRITICAL: Output ONLY valid JSON. Do NOT add any additional formatting."""
                
                messages = [
                    {"role": "system", "content": "You are a machine learning expert generating follow-up questions to learn more about this system."},
                    {"role": "user", "content": followup_prompt}
                ]
                
                try:
                    followup_response = llm.chat_completion_json(
                        messages=messages,
                        temperature=0.3,
                        response_schema={}
                    )
                    
                    followup_data = json.loads(followup_response)
                    followup_questions = followup_data.get("followup_questions")
                    
                except Exception as e:
                    logger.error(f"Error in followup question generation: {str(e)}")
                    logger.error(f"Raw followup response: {followup_response}")
                    raise
                
                logger.debug(f"Generated specific follow-up questions: {followup_questions}")
                
                assistant_response = f"""Thank you for that information. I have a few more specific questions to ensure comprehensive ML security coverage:

{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(followup_questions))}

This will help me identify potential ML-specific threat vectors for your system."""
                
                return ChatRefinementResponse(
                    message="need_more_info",
                    status="need_more_info", 
                    assistant_response=assistant_response,
                    refined_dfd="",
                    structured_answers=all_structured_answers,
                    coverage_analysis={
                        "confidence": coverage.get("confidence_level", 0),
                        "needs_followup": needs_followup,
                        "missing_information": missing_information
                    }
                )
            
            else:
                # Sufficient information gathered - prepare Q&A for context enumeration
                logger.info("Sufficient information gathered, preparing Q&A for context enumeration")
                
                # Use LLM to extract proper Q&A pairs from the conversation
                questions = []
                answers = []
                
                # LLM-powered Q&A extraction
                qa_extraction_prompt = f"""### ROLE
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
                
                messages = [
                    {"role": "system", "content": "You are an expert at extracting structured information."},
                    {"role": "user", "content": qa_extraction_prompt}
                ]
                
                try:
                    qa_extraction_response = llm.chat_completion_json(
                        messages=messages,
                        temperature=0.0,
                        response_schema={}
                    )
                    
                    qa_data = json.loads(qa_extraction_response)
                    logger.debug(f"Q&A extraction result: {qa_data}")
                    
                    # Extract questions and answers from LLM response
                    for qa_pair in qa_data.get("qa_pairs", []):
                        if "question" in qa_pair and "answer" in qa_pair:
                            questions.append(qa_pair["question"].strip())
                            answers.append(qa_pair["answer"].strip())
                            
                except Exception as e:
                    logger.warning(f"Failed to extract Q&A pairs with LLM: {e}")
                    # Fallback: just use the raw conversation as single Q&A
                    questions.append("Security assessment conversation")
                    answers.append(conversation_text.strip())
                
                return ChatRefinementResponse(
                    message="success",
                    status="success",
                    assistant_response="I have enough information. You can now proceed to context enumeration with this Q&A data.",
                    questions=questions,
                    answers=answers,
                    structured_answers=all_structured_answers,
                    coverage_analysis={
                        "covered_areas": coverage.get("areas_covered", []),
                        "total_insights": len(all_structured_answers),
                        "final_confidence": coverage.get("confidence_level", 0.8)
                    }
                )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in chat refinement endpoint after {processing_time:.2f}s: {str(e)}", exc_info=True)
        raise
    
    finally:
        processing_time = time.time() - start_time
        logger.info(f"Chat refinement endpoint completed in {processing_time:.2f}s")
