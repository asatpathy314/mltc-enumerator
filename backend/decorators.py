import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def with_logging(func):
    """
    A decorator that logs the entry, exit, timing, and exceptions of an async function.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        logger.info(f"Entering '{func_name}'...")
        
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            logger.info(f"'{func_name}' completed successfully in {processing_time:.2f}s")
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in '{func_name}' after {processing_time:.2f}s: {str(e)}", exc_info=True)
            raise
            
    return wrapper
