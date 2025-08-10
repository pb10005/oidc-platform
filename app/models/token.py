from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AuthorizationCode(Base):
    __tablename__ = "authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    code_challenge = Column(String, nullable=True)  # For PKCE
    code_challenge_method = Column(String, nullable=True)  # For PKCE
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    client = relationship("OAuth2Client")

    def __repr__(self):
        return f"<AuthorizationCode(id={self.id}, code='{self.code[:8]}...', user_id={self.user_id})>"


class AccessToken(Base):
    __tablename__ = "access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scope = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    client = relationship("OAuth2Client")

    def __repr__(self):
        return f"<AccessToken(id={self.id}, token='{self.token[:8]}...', user_id={self.user_id})>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    access_token_id = Column(Integer, ForeignKey("access_tokens.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    access_token = relationship("AccessToken")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, token='{self.token[:8]}...', access_token_id={self.access_token_id})>"
