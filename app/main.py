from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, engine
from app.models import Base
from app.routers import auth_router, oauth2_router, user_router
from app.services.oidc_service import OIDCService

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth_router, tags=["authentication"])
app.include_router(oauth2_router, tags=["oauth2", "oidc"])
app.include_router(user_router, tags=["users"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to login or show welcome page."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
        "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/config")
async def get_client_config():
    """Get client configuration for frontend applications."""
    return {
        "issuer": settings.issuer,
        "clientId": settings.sample_client_id,
        "clientSecret": settings.sample_client_secret,
        "redirectUris": settings.sample_client_redirect_uris,
        "scopes": settings.sample_client_scopes,
        "alertAutoHideSeconds": settings.alert_auto_hide_seconds,
        "formLoadingTimeoutSeconds": settings.form_loading_timeout_seconds,
        "clientExamplePort": settings.client_example_port
    }


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 OIDC Authentication Server starting up...")
    print(f"📍 Server running on {settings.host}:{settings.port}")
    print(f"🔗 Issuer: {settings.issuer}")
    print(f"🔍 Discovery endpoint: {settings.issuer}/.well-known/openid-configuration")
    
    # Create a sample OAuth2 client for testing
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        # Check if sample client already exists
        from app.models.client import OAuth2Client
        existing_client = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == settings.sample_client_id
        ).first()
        
        if not existing_client:
            sample_client = OIDCService.create_sample_client(db)
            print(f"✅ Created sample OAuth2 client:")
            print(f"   Client ID: {sample_client.client_id}")
            print(f"   Client Secret: {settings.sample_client_secret}")
            print(f"   Redirect URIs: {sample_client.redirect_uris}")
        else:
            print("✅ Sample OAuth2 client already exists")
        
        db.close()
    except Exception as e:
        print(f"⚠️  Warning: Could not create sample client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("🛑 OIDC Authentication Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
