from fastapi import FastAPI, status
from schemas import *
from schemas import convert_raw_to_final
from openai import OpenAI
from services.client import LLMClient, ModelType
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

@app.post("/context", response_model=ContextEnumeration, status_code=status.HTTP_200_OK)
async def context(request: ContextRequest) -> ContextEnumeration:
    """
    Enumerate a context preview.
    The context preview is a list of attackers, entry points, and assets associated with probabilities.
    The human will modify this context preview to generate a ground truth for further analysis.
    """
    start_time = time.time()
    logger.info("Context endpoint called")
    logger.debug(f"Request data: textual_dfd length={len(request.textual_dfd)}, extra_prompt={'present' if request.extra_prompt else 'absent'}")
    
    try:
        # Build the hint section if extra_prompt is provided
        hint_section = f"\n\n### HINT\n{request.extra_prompt}" if request.extra_prompt else ""
        logger.debug(f"Hint section: {'added' if hint_section else 'not added'}")
        
        prompt = f"""### ROLE
You are a senior security-threat-modeling analyst.

### TASK
From the **Data-Flow Diagram (DFD)** and the optional **Hint** provided below, identify every:

1. **Attacker** - any actor that can threaten the system.
2. **EntryPoint** - any interface, channel, or location an attacker could use to gain a foothold.
3. **Asset** - any component or data store whose loss or compromise matters.

### SCHEMA (strict)
class Likert(IntEnum):      # 1 = very_low … 5 = very_high
    very_low = 1
    low = 2
    medium = 3
    high = 4
    very_high = 5

class Attacker:
    description: str        # one concise sentence
    skill_level: Likert     # attacker sophistication
    access_level: Likert    # existing proximity / privileges
    prob_of_attack: float   # 0.0 - 1.0 likelihood this attacker attempts an attack

class EntryPoint:
    name: str               # short label (<6 words)
    description: str        # what this interface is / does
    prob_of_entry: float    # 0.0 - 1.0 likelihood this entry is tried
    difficulty_of_entry: Likert   # ease for attacker (1 = trivial → 5 = nearly impossible)

class Asset:
    name: str               # short component / data name
    description: str        # why it matters
    failure_modes: list[str] # at least 2 distinct ways it can fail or be harmed

### OUTPUT FORMAT (MUST BE VALID JSON)
{{
  "attackers": [Attacker, ...],
  "entry_points": [EntryPoint, ...],
  "assets": [Asset, ...]
}}

CRITICAL: Output ONLY the JSON object. No thinking tags, no comments, no markdown, no explanatory text. Start your response with {{ and end with }}.

### REASONING
Think in two phases:

**Phase 1 - Scratch-pad (do NOT reveal):**
- Parse the DFD -> enumerate possible actors, interfaces, and assets.
- Refine to realistic, distinct items (aim 3-10 of each).
- Assign Likert scores and probabilities that are internally consistent.
- Validate that the final objects conform exactly to the schema.

**Phase 2 - Answer:**
- Output only the final JSON object.

### INPUT
DFD:
{request.textual_dfd}{hint_section}
"""
        
        logger.info("Initializing LLM client")
        llm = LLMClient(ModelType.LOCAL_LM_STUDIO)
        response_schema = ContextEnumerationRaw.model_json_schema()
        messages = [
            {"role": "system", "content": "You are a senior security-threat-modeling analyst."},
            {"role": "user", "content": prompt}
        ]
        
        logger.info("Sending request to LLM")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        json_str = llm.chat_completion_json(
            messages=messages,
            temperature=0.0,
            response_schema=response_schema
        )
        
        logger.info("Received response from LLM, parsing...")
        raw_result = ContextEnumerationRaw.model_validate_json(json_str)
        
        logger.info("Converting raw response to final schema with UUIDs...")
        result = convert_raw_to_final(raw_result)
        
        processing_time = time.time() - start_time
        logger.info(f"Context endpoint completed successfully in {processing_time:.2f}s")
        logger.debug(f"Response contains: {len(result.attackers)} attackers, {len(result.entry_points)} entry points, {len(result.assets)} assets")
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in context endpoint after {processing_time:.2f}s: {str(e)}", exc_info=True)
        raise

@app.post("/generate", response_model=ContextEnumeration, status_code=status.HTTP_200_OK)
async def generate(request: VerifiedContext) -> ContextEnumeration:
    """
    Generate threat chains.
    """
    start_time = time.time()
    logger.info("Generate endpoint called")
    logger.debug(f"Request data: textual_dfd length={len(request.textual_dfd)}, extra_prompt={'present' if request.extra_prompt else 'absent'}")