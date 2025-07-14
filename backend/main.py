from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from settings import settings, setup_logging
from routers import ping, enumerate, generate, chat_refine
import logging

# Set up logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MLTC API",
    version="0.1.0",
    docs_url="/",
    redoc_url=None
)

# Add CORS middleware from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router)
app.include_router(enumerate.router)
app.include_router(generate.router)
app.include_router(chat_refine.router)

logger.info("MLTC API starting up.")
