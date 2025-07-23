from fastapi import APIRouter, status, HTTPException, Depends
from schemas import (
    ThreatVerificationRequest, ThreatVerificationResponse, ThreatVerificationQuestion,
    ThreatFilterRequest, ThreatFilterResponse, FilteredThreatChain
)
from services.threat_verifier import ThreatVerifier
from services.client import LLMClient
from dependencies import get_llm_client
from decorators import with_logging
import logging

router = APIRouter(tags=["Threat Verification"])
logger = logging.getLogger(__name__)

async def get_threat_verifier(llm_client: LLMClient = Depends(get_llm_client)) -> ThreatVerifier:
    """Dependency to get threat verifier instance."""
    return ThreatVerifier(llm_client)

@router.post("/verify/questions", response_model=ThreatVerificationResponse, status_code=status.HTTP_200_OK)
@with_logging
async def generate_verification_questions(
    request: ThreatVerificationRequest,
    verifier: ThreatVerifier = Depends(get_threat_verifier)
) -> ThreatVerificationResponse:
    """
    Generate verification questions for threat chains to assess their plausibility.
    
    This endpoint analyzes the generated threats and creates targeted questions
    to help users verify whether the threats are realistic in their specific context.
    """
    try:
        logger.info(f"Generating verification questions for {len(request.threat_chains)} threats")
        
        if not request.threat_chains:
            raise HTTPException(
                status_code=400,
                detail="At least one threat chain must be provided for verification."
            )
        
        # Generate verification questions
        questions = await verifier.generate_verification_questions(
            request.threat_chains, 
            request.context
        )
        
        logger.info(f"Successfully generated {len(questions)} verification questions")
        
        return ThreatVerificationResponse(
            verification_questions=questions,
            total_questions=len(questions)
        )
        
    except Exception as e:
        logger.error(f"Error generating verification questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate verification questions: {str(e)}"
        )

@router.post("/verify/filter", response_model=ThreatFilterResponse, status_code=status.HTTP_200_OK)
@with_logging
async def filter_threats(
    request: ThreatFilterRequest,
    verifier: ThreatVerifier = Depends(get_threat_verifier)
) -> ThreatFilterResponse:
    """
    Filter threat chains based on verification answers using AI analysis.
    
    This endpoint takes the original threats and user verification responses,
    then uses AI to assess the plausibility of each threat and filter out
    those that are deemed unrealistic or implausible.
    """
    try:
        logger.info(f"Filtering {len(request.threat_chains)} threats based on {len(request.verification_answers)} answers")
        
        if not request.threat_chains:
            raise HTTPException(
                status_code=400,
                detail="At least one threat chain must be provided for filtering."
            )
        
        if not request.verification_answers:
            logger.warning("No verification answers provided - keeping all threats with medium confidence")
            # Return all threats with medium plausibility if no answers provided
            filtered_threats = [
                FilteredThreatChain(
                    threat_chain=threat,
                    plausibility_score=0.5,
                    reasoning="No verification answers provided - kept with medium confidence",
                    kept=True
                ) for threat in request.threat_chains
            ]
        else:
            # Filter threats based on verification answers
            filtered_threats = await verifier.filter_threats_by_verification(
                request.threat_chains,
                request.verification_answers,
                request.context
            )
        
        # Calculate summary statistics
        kept_count = sum(1 for ft in filtered_threats if ft.kept)
        removed_count = len(filtered_threats) - kept_count
        
        # Generate filtering summary
        if removed_count == 0:
            filtering_summary = f"All {len(filtered_threats)} threats were deemed plausible and kept."
        elif kept_count == 0:
            filtering_summary = f"All {len(filtered_threats)} threats were deemed implausible and removed."
        else:
            filtering_summary = f"Filtered {len(filtered_threats)} threats: {kept_count} kept as plausible, {removed_count} removed as implausible."
        
        logger.info(f"Filtering complete: {filtering_summary}")
        
        return ThreatFilterResponse(
            filtered_threats=filtered_threats,
            removed_count=removed_count,
            kept_count=kept_count,
            filtering_summary=filtering_summary
        )
        
    except Exception as e:
        logger.error(f"Error filtering threats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to filter threats: {str(e)}"
        ) 