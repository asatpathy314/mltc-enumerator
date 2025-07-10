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

@app.post("/dfd/refine", response_model=DFDRefinementResponse, status_code=status.HTTP_200_OK)
async def refine_dfd(request: DFDRefinementRequest) -> DFDRefinementResponse:
    """Interactive refinement loop for a textual Data-Flow Diagram (DFD).

    Workflow:
    1. Client sends the initial DFD with *no* answers ⇒ the LLM returns clarifying questions.
    2. Client answers and re-posts ⇒ LLM either asks follow-up questions (message="need_more_info")
       or returns an improved DFD with message="success" and an empty question list.
    """
    start_time = time.time()
    logger.info("DFD refinement endpoint called")

    try:
        llm = LLMClient(ModelType.LOCAL_LM_STUDIO)

        first_round = not request.answers  # no answers yet

        if first_round:
            # models aren't good at knowing what they dont know
            # more principled questions over open questions
            # better prompting for more principled questions
            prompt = f"""You are a senior security-threat-modeling analyst.
We have the following data-flow diagram description (possibly incomplete or ambiguous):

{request.textual_dfd}

Your task: ask concise *clarifying questions* (1-5) that will help you fully understand and improve the DFD. Use the following JSON format only:
{{
  "questions": ["...", "...", ...]
}}
CRITICAL: Output ONLY the JSON object. ENSURE THAT THE FORMAT IS FOLLOWED EXACTLY. Use empty lists where appropriate."""
            response_schema = {"type": "object", "properties": {"questions": {"type": "array", "items": {"type": "string"}}}}
            messages = [{"role": "user", "content": prompt}]
            json_str = llm.chat_completion_json(messages=messages, temperature=0.0, response_schema=response_schema)
            data = json.loads(json_str)
            questions = data.get("questions", [])
            result = DFDRefinementResponse(
                textual_dfd=request.textual_dfd,
                questions=questions,
                message="need_more_info",
            )
            return result

        # ========= answer refinement =========
        qa_pairs = "\n".join([f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(zip(request.questions, request.answers))])
        prompt = f"""You are a senior security-threat-modeling analyst.
Below is the current DFD description and the user's answers to your previous questions. If you still need information, ask new questions. Otherwise, return an improved *textual DFD* in the required JSON format.

CURRENT DFD:
{request.textual_dfd}

USER Q&A:
{qa_pairs}

### OUTPUT OPTIONS (choose one)
1. Needs more info ⇒
{{
  "questions": ["...", "..."],
  "message": "need_more_info"
}}
2. Satisfied ⇒
{{
  "textual_dfd": "<refined DFD string in YAML format>",
  "questions": [],
  "message": "success"
}}
CRITICAL: Output ONLY the JSON object. ENSURE THAT THE FORMAT IS FOLLOWED EXACTLY. Use empty lists where appropriate."""
        response_schema = DFDRefinementResponse.model_json_schema()
        messages = [{"role": "user", "content": prompt}]
        json_str = llm.chat_completion_json(messages=messages, temperature=0.0, response_schema=response_schema)
        result = DFDRefinementResponse.model_validate_json(json_str)
        processing_time = time.time() - start_time
        logger.info(f"DFD refinement completed in {processing_time:.2f}s with message={result.message}")
        return result

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in refine_dfd after {processing_time:.2f}s: {str(e)}", exc_info=True)
        raise