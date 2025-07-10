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
            "data_poisoning": {
                "keywords": ["training data", "dataset", "data source", "training pipeline"],
                "questions": [
                    "Where does your training data come from and how is it validated?",
                    "What controls prevent malicious data from entering your training pipeline?",
                    "How do you verify the integrity of your training datasets?"
                ]
            },
            "model_stealing": {
                "keywords": ["model access", "api", "inference", "model weights"],
                "questions": [
                    "Who has access to your model weights or architecture details?",
                    "How is access to your model inference API controlled?",
                    "What information is returned by your model's prediction endpoints?"
                ]
            },
            "adversarial_examples": {
                "keywords": ["input validation", "preprocessing", "robustness"],
                "questions": [
                    "What input validation and preprocessing is performed on inference requests?",
                    "How do you handle potentially malicious or malformed input data?",
                    "Has your model been tested against adversarial examples?"
                ]
            },
            "supply_chain": {
                "keywords": ["model source", "pretrained", "dependencies", "third-party"],
                "questions": [
                    "Are you using any pre-trained models or third-party ML components?",
                    "How do you verify the integrity and security of your ML dependencies?",
                    "What is the provenance of your model weights and training code?"
                ]
            },
            "prompt_injection": {
                "keywords": ["prompt", "llm", "language model", "user input"],
                "questions": [
                    "If using language models, how do you sanitize user prompts?",
                    "What controls prevent prompt injection or jailbreaking attempts?",
                    "How do you separate system prompts from user input?"
                ]
            },
            "inference_time_attacks": {
                "keywords": ["prediction", "inference", "runtime", "model serving"],
                "questions": [
                    "How is your model served and what security controls exist at inference time?",
                    "What monitoring exists for unusual prediction patterns or model behavior?",
                    "How do you handle concurrent inference requests and resource limits?"
                ]
            }
        }
        
        # Determine if this is the first interaction or a follow-up
        is_initial = len(request.conversation_history) == 0
        
        if is_initial:
            # Initial analysis: scan DFD for ML attack indicators
            logger.debug("Initial chat analysis of DFD")
            
            # Analyze DFD content for ML-related keywords
            dfd_lower = request.textual_dfd.lower()
            detected_areas = []
            
            for area, info in ml_attack_knowledge.items():
                if any(keyword in dfd_lower for keyword in info["keywords"]):
                    detected_areas.append(area)
            
            # If no ML-specific keywords found, add general ML security areas
            if not detected_areas:
                detected_areas = ["supply_chain", "adversarial_examples", "model_stealing"]
            
            logger.info(f"Detected ML attack areas: {detected_areas}")
            
            # Generate initial questions based on detected areas
            initial_questions = []
            for area in detected_areas[:2]:  # Start with top 2 areas
                initial_questions.extend(ml_attack_knowledge[area]["questions"][:1])
            
            assistant_response = f"""I'm analyzing your data-flow diagram for ML security concerns. I've identified some areas that need clarification to properly assess ML-specific threats.

Let me start with a few key questions:

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
            
            # Get the user's latest response
            user_messages = [msg for msg in request.conversation_history if msg.role == "user"]
            if not user_messages:
                raise ValueError("No user messages found in conversation history")
            
            latest_user_response = user_messages[-1].content
            
            # Extract structured information from user response
            extraction_prompt = f"""### ROLE
You are an ML security analyst extracting structured information from user responses.

### TASK
Analyze the user's response about their ML system and extract specific security-relevant information. 

### USER'S RESPONSE
"{latest_user_response}"

### ORIGINAL DFD CONTEXT
{request.textual_dfd}

### EXTRACTION SCHEMA
For each piece of security-relevant information, output:
{{
  "extractions": [
    {{
      "question_id": "auto-generated-id",
      "attack_area": "one of: data_poisoning|model_stealing|adversarial_examples|supply_chain|prompt_injection|inference_time_attacks",
      "confidence_score": 0.0-1.0,
      "extracted_answer": "specific factual answer",
      "raw_user_response": "original user text"
    }}
  ],
  "coverage_assessment": {{
    "areas_covered": ["list of ML attack areas addressed"],
    "confidence_level": 0.0-1.0,
    "needs_followup": true/false,
    "next_priority_areas": ["areas needing more info"]
  }}
}}

CRITICAL: Output ONLY valid JSON. Focus on ML security specifics."""
            
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
                        question_id=ext["question_id"],
                        attack_area=ext["attack_area"],
                        confidence_score=ext["confidence_score"],
                        extracted_answer=ext["extracted_answer"],
                        raw_user_response=ext["raw_user_response"]
                    )
                    new_structured_answers.append(structured_answer)
                except Exception as e:
                    logger.warning(f"Failed to create StructuredAnswer: {e}")
            
            # Combine with previous structured answers
            all_structured_answers = request.structured_answers + new_structured_answers
            
            coverage = extraction_data.get("coverage_assessment", {})
            needs_followup = coverage.get("needs_followup", True)
            
            if needs_followup and coverage.get("confidence_level", 0) < 0.8:
                # Generate follow-up questions
                priority_areas = coverage.get("next_priority_areas", ["supply_chain"])
                
                followup_questions = []
                for area in priority_areas[:2]:
                    if area in ml_attack_knowledge:
                        followup_questions.extend(ml_attack_knowledge[area]["questions"][:1])
                
                assistant_response = f"""Thank you for that information. I have a few more questions to ensure comprehensive ML security coverage:

{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(followup_questions))}

This will help me identify potential ML-specific threat vectors."""
                
                return ChatRefinementResponse(
                    message="need_more_info",
                    status="need_more_info", 
                    assistant_response=assistant_response,
                    refined_dfd="",
                    structured_answers=all_structured_answers,
                    coverage_analysis={
                        "covered_areas": coverage.get("areas_covered", []),
                        "priority_areas": priority_areas,
                        "confidence": coverage.get("confidence_level", 0)
                    }
                )
            
            else:
                # Sufficient information gathered - prepare Q&A for context enumeration
                logger.info("Sufficient information gathered, preparing Q&A for context enumeration")
                
                # Extract questions and answers from the conversation
                questions = []
                answers = []
                
                # Get all assistant questions and user responses from conversation
                conversation = request.conversation_history
                for i in range(0, len(conversation) - 1, 2):
                    if (i < len(conversation) and 
                        conversation[i].role == "assistant" and 
                        i + 1 < len(conversation) and 
                        conversation[i + 1].role == "user"):
                        
                        # Extract questions from assistant message
                        assistant_msg = conversation[i].content
                        user_response = conversation[i + 1].content
                        
                        # Simple question extraction (look for numbered questions)
                        import re
                        question_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', assistant_msg, re.DOTALL)
                        if question_matches:
                            for question in question_matches:
                                questions.append(question.strip())
                                answers.append(user_response.strip())
                        else:
                            # If no numbered questions, treat whole assistant message as one question
                            questions.append(assistant_msg.strip())
                            answers.append(user_response.strip())
                
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
