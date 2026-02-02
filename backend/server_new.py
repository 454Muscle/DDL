"""
Download Portal API - Main Application
Refactored from monolithic server.py into modular structure
"""
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from services.database import client, shutdown_db_client

# Import routers
from routers.downloads import router as downloads_router
from routers.auth import router as auth_router
from routers.submissions import router as submissions_router
from routers.admin import router as admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(
    title="Download Portal API",
    description="API for managing downloads, submissions, and admin functions",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Include all routers
api_router.include_router(downloads_router)
api_router.include_router(auth_router)
api_router.include_router(submissions_router)
api_router.include_router(admin_router)

# Include the main api_router in the app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await shutdown_db_client()
