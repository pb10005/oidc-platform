from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.client import OAuth2Client
from app.models.user import User
from app.services.token_service import TokenService
import json


class OIDCService:
    @staticmethod
    def get_discovery_document() -> Dict[str, Any]:
        """Return the OpenID Connect discovery document."""
        return {
            "issuer": settings.issuer,
            "authorization_endpoint": f"{settings.issuer}/oauth2/authorize",
            "token_endpoint": f"{settings.issuer}/oauth2/token",
            "userinfo_endpoint": f"{settings.issuer}/oauth2/userinfo",
            "jwks_uri": f"{settings.issuer}/jwks",
            "scopes_supported": settings.supported_scopes,
            "response_types_supported": settings.supported_response_types,
            "response_modes_supported": settings.supported_response_modes,
            "grant_types_supported": settings.supported_grant_types,
            "subject_types_supported": settings.supported_subject_types,
            "id_token_signing_alg_values_supported": settings.supported_id_token_signing_algs,
            "token_endpoint_auth_methods_supported": settings.supported_token_endpoint_auth_methods,
            "code_challenge_methods_supported": settings.supported_code_challenge_methods,
            "claims_supported": settings.supported_claims
        }

    @staticmethod
    def get_jwks() -> Dict[str, Any]:
        """Return the JSON Web Key Set (JWKS)."""
        # For simplicity, we're using HMAC (symmetric key)
        # In production, you should use RSA keys
        return {
            "keys": [
                {
                    "kty": "oct",
                    "use": "sig",
                    "kid": "1",
                    "alg": "HS256"
                }
            ]
        }

    @staticmethod
    def validate_client(db: Session, client_id: str, client_secret: Optional[str] = None) -> Optional[OAuth2Client]:
        """Validate OAuth2 client credentials."""
        client = db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id).first()
        if not client:
            return None
        
        # For public clients, no secret validation needed
        if client.client_type == "public":
            return client
        
        # For confidential clients, validate secret only if provided
        # (authorization endpoint doesn't require secret, token endpoint does)
        if client_secret is not None:
            if client.client_secret_hash:
                from app.services.auth_service import AuthService
                if AuthService.verify_password(client_secret, client.client_secret_hash):
                    return client
                else:
                    return None
            else:
                return None
        
        # If no secret provided, return client (for authorization endpoint)
        return client

    @staticmethod
    def validate_redirect_uri(client: OAuth2Client, redirect_uri: str) -> bool:
        """Validate if redirect URI is allowed for the client."""
        allowed_uris = json.loads(client.redirect_uris)
        return redirect_uri in allowed_uris

    @staticmethod
    def validate_scope(client: OAuth2Client, requested_scope: str) -> bool:
        """Validate if the requested scope is allowed for the client."""
        allowed_scopes = json.loads(client.scopes)
        requested_scopes = requested_scope.split()
        return all(scope in allowed_scopes for scope in requested_scopes)

    @staticmethod
    def create_id_token(user: User, client_id: str, nonce: Optional[str] = None) -> str:
        """Create an OpenID Connect ID token."""
        now = TokenService.create_access_token({})  # Get current timestamp logic
        
        id_token_data = {
            "iss": settings.issuer,
            "sub": str(user.id),
            "aud": client_id,
            "exp": TokenService.verify_token(TokenService.create_access_token({}))["exp"],
            "iat": TokenService.verify_token(TokenService.create_access_token({}))["iat"],
            "auth_time": TokenService.verify_token(TokenService.create_access_token({}))["iat"],
            "name": f"{user.first_name} {user.last_name}",
            "given_name": user.first_name,
            "family_name": user.last_name,
            "email": user.email,
            "email_verified": True
        }
        
        if nonce:
            id_token_data["nonce"] = nonce
        
        return TokenService.create_access_token(id_token_data)

    @staticmethod
    def get_userinfo(user: User) -> Dict[str, Any]:
        """Get user information for the userinfo endpoint."""
        return {
            "sub": str(user.id),
            "name": f"{user.first_name} {user.last_name}",
            "given_name": user.first_name,
            "family_name": user.last_name,
            "email": user.email,
            "email_verified": True
        }

    @staticmethod
    def create_sample_client(db: Session) -> OAuth2Client:
        """Create a sample OAuth2 client for testing."""
        from app.services.auth_service import AuthService
        
        client = OAuth2Client(
            client_id=settings.sample_client_id,
            client_secret_hash=AuthService.get_password_hash(settings.sample_client_secret),
            name=settings.sample_client_name,
            redirect_uris=json.dumps(settings.sample_client_redirect_uris),
            scopes=json.dumps(settings.sample_client_scopes),
            client_type=settings.sample_client_type
        )
        
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
