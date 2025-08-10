from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True, nullable=False)
    client_secret_hash = Column(String, nullable=True)  # Nullable for public clients
    name = Column(String, nullable=False)
    redirect_uris = Column(Text, nullable=False)  # JSON string of URIs
    scopes = Column(Text, nullable=False)  # JSON string of allowed scopes
    client_type = Column(String, default="confidential")  # confidential or public
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OAuth2Client(id={self.id}, client_id='{self.client_id}', name='{self.name}')>"
