from fastapi import APIRouter, status, HTTPException
from schemas import ContextEnumeration, ThreatEnumeration
from dependencies import get_threat_generator
from decorators import with_logging
import logging

router = APIRouter(tags=["Threats"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=ThreatEnumeration, status_code=status.HTTP_200_OK)
@with_logging
async def generate(request: ContextEnumeration) -> ThreatEnumeration:
    """
    Generate comprehensive threat chains using ML-aware threat modeling.
    
    This endpoint analyzes the provided context (attackers, entry points, assets, 
    assumptions, and Q&A data) to generate sophisticated threat chains that are
    specific to ML systems and traditional security threats adapted for ML environments.
    """
    try:
        logger.info(f"Starting threat generation for system: {request.textual_dfd[:100]}...")
        
        # Validate that we have sufficient context
        if not request.attackers and not request.entry_points and not request.assets:
            raise HTTPException(
                status_code=400,
                detail="Insufficient context provided. At least one attacker, entry point, or asset must be specified."
            )
        
        # Get threat generator instance
        threat_generator = await get_threat_generator()
        
        # Generate threat chains using the advanced threat generator
        threat_chains = await threat_generator.generate_threat_chains(request)
        
        logger.info(f"Successfully generated {len(threat_chains)} threat chains")
        
        return ThreatEnumeration(threat_chains=threat_chains)
        
    except Exception as e:
        logger.error(f"Error generating threat chains: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate threat chains: {str(e)}"
        )
