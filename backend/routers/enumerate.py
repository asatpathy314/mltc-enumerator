from fastapi import APIRouter, status, Depends
from schemas import ContextEnumeration
from services.client import LLMClient
from services.prompt_builder import PromptBuilder
from dependencies import get_llm_client, get_prompt_builder
from decorators import with_logging
import json
import logging

router = APIRouter(tags=["Context Enumeration"])
logger = logging.getLogger(__name__)
SYSTEM_PROMPT = """
You are an ML-security analyst. Obey JSON schema, never ask direct security-control questions, focus on architecture, training and data provenance.
"""

@router.post("/enumerate", response_model=ContextEnumeration, status_code=status.HTTP_200_OK)
@with_logging
async def enumerate_context(
    request: ContextEnumeration,
    llm: LLMClient = Depends(get_llm_client),
    builder: PromptBuilder = Depends(get_prompt_builder),
) -> ContextEnumeration:
    """
    Unified endpoint that either generates a brand-new context enumeration or refines a provided one.
    """
    is_initial = not (request.attackers or request.entry_points or request.assets)
    logger.debug(f"Request classified as {'initial' if is_initial else 'regeneration'} enumeration")

    prompt = builder.build_context_enumeration_prompt(request)
    
    logger.info(f"Prompt length: {len(prompt)} characters")
    logger.debug(f"Prompt: {prompt}")

    response_schema = ContextEnumeration.model_json_schema()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    json_str = await llm.chat_completion_json(
        messages=messages,
        temperature=0.0 if is_initial else 0.2,
        response_schema=response_schema,
    )

    logger.info(f"Raw response: {json_str}")

    data = json.loads(json_str)
    data["textual_dfd"] = request.textual_dfd
    if request.extra_prompt is not None:
        data["extra_prompt"] = request.extra_prompt

    result = ContextEnumeration.model_validate(data)
    
    logger.debug(
        f"Response contains: {len(result.attackers)} attackers, {len(result.entry_points)} entry points, "
        f"{len(result.assets)} assets, {len(result.assumptions)} assumptions"
    )

    return result
