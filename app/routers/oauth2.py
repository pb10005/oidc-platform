from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.oidc_service import OIDCService
from app.services.token_service import TokenService
from app.routers.auth import get_current_user
from app.models.user import User
from typing import Optional
import urllib.parse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect Discovery endpoint."""
    return OIDCService.get_discovery_document()


@router.get("/jwks")
async def jwks():
    """JSON Web Key Set endpoint."""
    return OIDCService.get_jwks()


@router.get("/oauth2/authorize", response_class=HTMLResponse)
async def authorization_endpoint(
    request: Request,
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: Optional[str] = Query(None),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """OAuth2/OIDC Authorization endpoint."""
    
    # Validate response_type
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")
    
    # Validate client
    client = OIDCService.validate_client(db, client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    # Validate redirect_uri
    if not OIDCService.validate_redirect_uri(client, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # Validate scope
    if not OIDCService.validate_scope(client, scope):
        raise HTTPException(status_code=400, detail="Invalid scope")
    
    # Check if user is authenticated
    user = get_current_user(request, db)
    if not user:
        # Redirect to login with return URL
        login_url = f"/login?redirect_uri={urllib.parse.quote(str(request.url))}"
        return RedirectResponse(url=login_url, status_code=302)
    
    # Show consent page
    return templates.TemplateResponse("consent.html", {
        "request": request,
        "client": client,
        "user": user,
        "scope": scope,
        "response_type": response_type,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "nonce": nonce
    })


@router.post("/auth/consent")
async def consent_endpoint(
    request: Request,
    action: str = Form(...),
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    state: Optional[str] = Form(None),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    nonce: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Handle user consent."""
    
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    if action == "deny":
        # User denied consent
        error_params = {"error": "access_denied"}
        if state:
            error_params["state"] = state
        
        error_query = urllib.parse.urlencode(error_params)
        return RedirectResponse(url=f"{redirect_uri}?{error_query}", status_code=302)
    
    if action == "allow":
        # User granted consent, create authorization code
        auth_code = TokenService.create_authorization_code(
            db=db,
            client_id=client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        # Redirect back to client with authorization code
        callback_params = {"code": auth_code.code}
        if state:
            callback_params["state"] = state
        
        callback_query = urllib.parse.urlencode(callback_params)
        return RedirectResponse(url=f"{redirect_uri}?{callback_query}", status_code=302)
    
    raise HTTPException(status_code=400, detail="Invalid action")


@router.post("/oauth2/token")
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """OAuth2/OIDC Token endpoint."""
    
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
    
    if not code or not redirect_uri:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # Validate client
    client = OIDCService.validate_client(db, client_id, client_secret)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    # Exchange code for tokens
    tokens = TokenService.exchange_code_for_tokens(
        db=db,
        code=code,
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier
    )
    
    if not tokens:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Add ID token if openid scope is requested
    if "openid" in tokens["scope"]:
        # Get user for ID token
        from app.models.token import AuthorizationCode
        auth_code = db.query(AuthorizationCode).filter(
            AuthorizationCode.code == code
        ).first()
        
        if auth_code:
            user = db.query(User).filter(User.id == auth_code.user_id).first()
            if user:
                tokens["id_token"] = OIDCService.create_id_token(user, client_id)
    
    return JSONResponse(content=tokens)


@router.get("/oauth2/userinfo")
async def userinfo_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """OIDC UserInfo endpoint."""
    
    # Get access token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Get user from token
    user = TokenService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    return OIDCService.get_userinfo(user)
