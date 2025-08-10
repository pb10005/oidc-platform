from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.token import AccessToken, RefreshToken, AuthorizationCode
from app.models.user import User
import secrets
import string


class TokenService:
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def generate_authorization_code() -> str:
        """Generate a secure authorization code."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))

    @staticmethod
    def generate_random_token() -> str:
        """Generate a secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))

    @staticmethod
    def create_authorization_code(
        db: Session,
        client_id: str,
        user_id: int,
        redirect_uri: str,
        scope: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> AuthorizationCode:
        """Create an authorization code."""
        code = TokenService.generate_authorization_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            expires_at=expires_at
        )
        
        db.add(auth_code)
        db.commit()
        db.refresh(auth_code)
        return auth_code

    @staticmethod
    def exchange_code_for_tokens(
        db: Session,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """Exchange authorization code for access and refresh tokens."""
        # Get the authorization code
        auth_code = db.query(AuthorizationCode).filter(
            AuthorizationCode.code == code,
            AuthorizationCode.client_id == client_id,
            AuthorizationCode.redirect_uri == redirect_uri,
            AuthorizationCode.used == False,
            AuthorizationCode.expires_at > datetime.utcnow()
        ).first()
        
        if not auth_code:
            return None
        
        # Verify PKCE if present
        if auth_code.code_challenge and code_verifier:
            import hashlib
            import base64
            
            if auth_code.code_challenge_method == "S256":
                verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
                verifier_challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip('=')
                if verifier_challenge != auth_code.code_challenge:
                    return None
            elif auth_code.code_challenge_method == "plain":
                if code_verifier != auth_code.code_challenge:
                    return None
        
        # Mark code as used
        auth_code.used = True
        
        # Create access token
        access_token_data = {
            "sub": str(auth_code.user_id),
            "client_id": client_id,
            "scope": auth_code.scope
        }
        access_token = TokenService.create_access_token(access_token_data)
        
        # Store access token in database
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        db_access_token = AccessToken(
            token=access_token,
            client_id=client_id,
            user_id=auth_code.user_id,
            scope=auth_code.scope,
            expires_at=access_token_expires
        )
        db.add(db_access_token)
        db.flush()
        
        # Create refresh token
        refresh_token = TokenService.generate_random_token()
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        db_refresh_token = RefreshToken(
            token=refresh_token,
            access_token_id=db_access_token.id,
            expires_at=refresh_token_expires
        )
        db.add(db_refresh_token)
        
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "refresh_token": refresh_token,
            "scope": auth_code.scope
        }

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """Get user from access token."""
        payload = TokenService.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return db.query(User).filter(User.id == int(user_id)).first()
