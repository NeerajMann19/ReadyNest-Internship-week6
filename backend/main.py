"""
Analytics Studio — FastAPI ASGI Entry Point

Main application module initializing FastAPI, configuring CORS middleware for Render & Vercel,
and registering router endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import APP_NAME, VERSION, CORS_ORIGINS
from api.routes import router as api_router

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Analytics Studio — Decision Intelligence Platform API",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)
