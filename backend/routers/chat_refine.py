from fastapi import APIRouter, status, Depends, HTTPException
from schemas import ChatRefinementRequest, ChatRefinementResponse, StructuredAnswer, MultipleChoiceQuestion, MultipleChoiceOption, UserAnswer
from services.client import LLMClient
from services.prompt_builder import PromptBuilder, ModularQuestionGenerator, AttackType
from dependencies import get_llm_client, get_prompt_builder, get_modular_question_generator
from decorators import with_logging
from typing import List, Optional
from pydantic import BaseModel
import json
import logging

router = APIRouter(tags=["Chat Refinement"])
logger = logging.getLogger(__name__)
SYSTEM_PROMPT = """
You are an ML-security analyst. Obey JSON schema, never ask direct security-control questions, focus on architecture, training and data provenance.
"""

# Global state to track last sent questions for answer processing
# In a production system, this should be stored in a database or session store
_last_questions_by_dfd = {}

class ModularQuestionRequest(BaseModel):
    """Request for modular attack-specific question generation"""
    textual_dfd: str
    attack_types: Optional[List[str]] = None  # List of attack type strings
    include_context: bool = False

class ModularQuestionResponse(BaseModel):
    """Response for modular question generation"""
    questions_with_options: List[dict]
    generation_metadata: dict
    supported_attack_types: List[str]

@router.post("/refine", response_model=ChatRefinementResponse, status_code=status.HTTP_200_OK)
@with_logging
async def refine_with_chat(
    request: ChatRefinementRequest,
    llm: LLMClient = Depends(get_llm_client),
    builder: PromptBuilder = Depends(get_prompt_builder),
    modular_generator: ModularQuestionGenerator = Depends(get_modular_question_generator),
) -> ChatRefinementResponse:
    """
    ML-aware chat interface for DFD refinement.
    """
    is_initial = len(request.conversation_history) == 0
    
    if is_initial:
        return await _handle_initial_chat(request, llm, builder, modular_generator)
    else:
        return await _handle_followup_chat(request, llm, builder)

@router.post("/modular-questions", response_model=ModularQuestionResponse, status_code=status.HTTP_200_OK)
@with_logging
async def generate_modular_questions(
    request: ModularQuestionRequest,
    llm: LLMClient = Depends(get_llm_client),
    modular_generator: ModularQuestionGenerator = Depends(get_modular_question_generator),
) -> ModularQuestionResponse:
    """
    Generate attack-specific questions using the modular approach.
    Allows explicit selection of attack types to analyze.
    """
    logger.info(f"Generating modular questions for attack types: {request.attack_types}")
    
    # Convert string attack types to enum values
    supported_types = modular_generator.get_supported_attack_types()
    attack_type_map = {at.value: at for at in supported_types}
    
    if request.attack_types:
        selected_attack_types = []
        for attack_type_str in request.attack_types:
            if attack_type_str in attack_type_map:
                selected_attack_types.append(attack_type_map[attack_type_str])
            else:
                logger.warning(f"Unsupported attack type: {attack_type_str}")
        
        if not selected_attack_types:
            selected_attack_types = [AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS]
    else:
        selected_attack_types = [AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS]
    
    try:
        modular_result = await modular_generator.generate_modular_questions(
            textual_dfd=request.textual_dfd,
            llm_client=llm,
            attack_types=selected_attack_types,
            context=None
        )
        
        return ModularQuestionResponse(
            questions_with_options=modular_result.get("questions_with_options", []),
            generation_metadata=modular_result.get("generation_metadata", {}),
            supported_attack_types=[at.value for at in supported_types]
        )
        
    except Exception as e:
        logger.error(f"Modular question generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate modular questions: {str(e)}"
        )

@router.get("/attack-types", status_code=status.HTTP_200_OK)
@with_logging
async def get_supported_attack_types(
    modular_generator: ModularQuestionGenerator = Depends(get_modular_question_generator),
) -> dict:
    """
    Get information about supported attack types for modular question generation.
    """
    supported_types = modular_generator.get_supported_attack_types()
    attack_type_info = {}
    
    for attack_type in supported_types:
        attack_type_info[attack_type.value] = modular_generator.get_attack_type_info(attack_type)
    
    return {
        "supported_attack_types": [at.value for at in supported_types],
        "attack_type_details": attack_type_info,
        "default_attack_types": ["model_poisoning", "evasion_attacks"],
        "total_supported": len(supported_types)
    }

async def _handle_initial_chat(
    request: ChatRefinementRequest, 
    llm: LLMClient, 
    builder: PromptBuilder,
    modular_generator: ModularQuestionGenerator
) -> ChatRefinementResponse:
    """Handles the first message in a chat refinement conversation using modular attack-specific questions."""
    logger.info("Using modular question generation for initial chat")
    
    # Generate questions using the modular approach
    try:
        modular_result = await modular_generator.generate_modular_questions(
            textual_dfd=request.textual_dfd,
            llm_client=llm,
            attack_types=[AttackType.MODEL_POISONING, AttackType.EVASION_ATTACKS],
            context=None
        )
        
        questions_with_options = modular_result.get("questions_with_options", [])
        generation_metadata = modular_result.get("generation_metadata", {})
        
        logger.info(f"Modular generation completed: {generation_metadata}")
        
    except Exception as e:
        logger.error(f"Modular question generation failed, falling back to legacy: {str(e)}")
        # Fallback to legacy approach
        question_generation_prompt = builder.build_question_generation_prompt(
            detected_areas=[], reasoning="Fallback due to modular failure", textual_dfd=request.textual_dfd
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question_generation_prompt}
        ]
        
        question_response = await llm.chat_completion_json(messages=messages, temperature=0.3)
        question_data = json.loads(question_response)
        questions_with_options = question_data.get("questions_with_options", [])
        generation_metadata = {"method": "legacy_fallback", "total_questions": len(questions_with_options)}
    
    logger.debug(f"Generated questions with options: {questions_with_options}")
    
    # Convert to MultipleChoiceQuestion objects
    multiple_choice_questions = []
    for q_data in questions_with_options:
        options = [
            MultipleChoiceOption(
                id=opt["id"],
                text=opt["text"],
                is_editable=True
            ) for opt in q_data.get("options", [])
        ]
        
        mc_question = MultipleChoiceQuestion(
            id=q_data["id"],
            question=q_data["question"],
            options=options,
            allow_other=True,
            allow_edit_options=True
        )
        multiple_choice_questions.append(mc_question)

    # Generate enhanced assistant response based on attack types analyzed
    attack_types_analyzed = generation_metadata.get("attack_types_analyzed", [])
    attack_summary = ""
    if attack_types_analyzed:
        attack_names = []
        if "model_poisoning" in attack_types_analyzed:
            attack_names.append("model poisoning")
        if "evasion_attacks" in attack_types_analyzed:
            attack_names.append("evasion attacks")
        attack_summary = f" I'm focusing on **{' and '.join(attack_names)}** vulnerabilities."
    
    question_text_list = [q.question for q in multiple_choice_questions]
    assistant_response = f"""I'm analyzing your ML system's data-flow diagram for security vulnerabilities.{attack_summary}
    
Let me start with some targeted questions about your system's architecture and security posture. For each question, you can choose from the provided options, edit them if needed, or provide your own answer:

{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(question_text_list))}"""
    
    # Store questions for later answer processing
    _last_questions_by_dfd[request.textual_dfd] = multiple_choice_questions
    
    return ChatRefinementResponse(
        message="need_more_info",
        status="need_more_info",
        assistant_response=assistant_response,
        multiple_choice_questions=multiple_choice_questions,
        structured_answers=[],
        coverage_analysis={
            "detected_areas": attack_types_analyzed, 
            "covered_areas": [],
            "generation_metadata": generation_metadata
        }
    )

def _convert_multiple_choice_answers_to_text(multiple_choice_answers: List[UserAnswer], questions: List[MultipleChoiceQuestion] = None) -> str:
    """Convert multiple choice answers into a text format for processing."""
    if not multiple_choice_answers:
        return ""
    
    # Create a lookup map for questions and options if provided
    questions_map = {}
    if questions:
        for q in questions:
            options_map = {opt.id: opt.text for opt in q.options}
            questions_map[q.id] = {
                'question': q.question,
                'options': options_map
            }
    
    converted_text = []
    for answer in multiple_choice_answers:
        if answer.custom_answer:
            # User provided a custom answer or "other"
            question_text = questions_map.get(answer.question_id, {}).get('question', answer.question_id)
            converted_text.append(f"Q: {question_text}\nA: {answer.custom_answer}")
        elif answer.selected_option_id:
            # User selected one of the options
            question_text = questions_map.get(answer.question_id, {}).get('question', answer.question_id)
            option_text = questions_map.get(answer.question_id, {}).get('options', {}).get(answer.selected_option_id, answer.selected_option_id)
            converted_text.append(f"Q: {question_text}\nA: {option_text}")
    
    return "\n\n".join(converted_text)

async def _handle_followup_chat(
    request: ChatRefinementRequest, llm: LLMClient, builder: PromptBuilder
) -> ChatRefinementResponse:
    """Handles subsequent messages in the chat, extracting info and deciding next steps."""
    logger.debug("Processing follow-up conversation")
    
    chat_messages = [msg for msg in request.conversation_history if msg.role == "assistant"]
    user_messages = [msg for msg in request.conversation_history if msg.role == "user"]

    if not user_messages:
        raise ValueError("No user messages found in conversation history")
    
    latest_chat_message = chat_messages[-1].content
    latest_user_response = user_messages[-1].content
    
    # Include multiple choice answers in the user response
    stored_questions = _last_questions_by_dfd.get(request.textual_dfd, [])
    mc_answers_text = _convert_multiple_choice_answers_to_text(request.multiple_choice_answers, stored_questions)
    if mc_answers_text:
        latest_user_response += f"\n\nMultiple Choice Answers:\n{mc_answers_text}"
    
    extraction_prompt = builder.build_extraction_prompt(
        latest_chat_message, latest_user_response, request.textual_dfd
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": extraction_prompt}
    ]
    
    extraction_response = await llm.chat_completion_json(messages=messages, temperature=0.0)
    extraction_data = json.loads(extraction_response)
    logger.debug(f"Extraction result: {extraction_data}")
    
    new_structured_answers = [
        StructuredAnswer(**ext) for ext in extraction_data.get("extractions", [])
    ]
    all_structured_answers = request.structured_answers + new_structured_answers
    
    coverage = extraction_data.get("coverage_assessment", {})
    needs_followup = coverage.get("needs_followup", True)
    
    if needs_followup:
        missing_information = coverage.get("missing_information", "")
        followup_prompt = builder.build_followup_prompt(
            missing_information, request.textual_dfd, request.conversation_history
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": followup_prompt}
        ]
        
        followup_response = await llm.chat_completion_json(messages=messages, temperature=0.3)
        followup_data = json.loads(followup_response)
        questions_with_options = followup_data.get("questions_with_options", [])
        
        logger.debug(f"Generated follow-up questions with options: {questions_with_options}")
        
        # Convert to MultipleChoiceQuestion objects
        multiple_choice_questions = []
        for q_data in questions_with_options:
            options = [
                MultipleChoiceOption(
                    id=opt["id"],
                    text=opt["text"],
                    is_editable=True
                ) for opt in q_data.get("options", [])
            ]
            
            mc_question = MultipleChoiceQuestion(
                id=q_data["id"],
                question=q_data["question"],
                options=options,
                allow_other=True,
                allow_edit_options=True
            )
            multiple_choice_questions.append(mc_question)

        # Generate fallback text for backward compatibility
        question_text_list = [q.question for q in multiple_choice_questions]
        assistant_response = f"""Thank you for that information. I have a few more specific questions to ensure comprehensive ML security coverage:

{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(question_text_list))}

For each question, you can choose from the provided options, edit them if needed, or provide your own answer."""
        
        # Store questions for later answer processing
        _last_questions_by_dfd[request.textual_dfd] = multiple_choice_questions
        
        return ChatRefinementResponse(
            message="need_more_info",
            status="need_more_info",
            assistant_response=assistant_response,
            multiple_choice_questions=multiple_choice_questions,
            structured_answers=all_structured_answers,
            coverage_analysis={
                "confidence": coverage.get("confidence_level", 0),
                "needs_followup": needs_followup,
                "missing_information": missing_information
            }
        )
    else:
        logger.info("Sufficient information gathered, preparing Q&A for context enumeration")
        
        qa_extraction_prompt = builder.build_qa_extraction_prompt(request.conversation_history)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": qa_extraction_prompt}
        ]
        
        qa_extraction_response = await llm.chat_completion_json(messages=messages, temperature=0.0)
        qa_data = json.loads(qa_extraction_response)
        logger.debug(f"Q&A extraction result: {qa_data}")
        
        questions = [pair["question"].strip() for pair in qa_data.get("qa_pairs", []) if "question" in pair]
        answers = [pair["answer"].strip() for pair in qa_data.get("qa_pairs", []) if "answer" in pair]
        
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
