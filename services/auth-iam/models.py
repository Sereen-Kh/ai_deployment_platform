"""Database models for Auth/IAM service."""

from shared.models import UserRole
from shared.database import Base
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', String, ForeignKey('roles.id', ondelete='CASCADE'))
)

organization_members = Table(
    'organization_members',
    Base.metadata,
    Column('organization_id', String, ForeignKey(
        'organizations.id', ondelete='CASCADE')),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role', SQLEnum(UserRole), default=UserRole.VIEWER)
)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # OAuth fields
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    organizations = relationship(
        "Organization", secondary=organization_members, back_populates="members")
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan")


class Organization(Base):
    """Organization/Workspace model."""

    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    owner_id = Column(String, ForeignKey("users.id"))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship(
        "User", secondary=organization_members, back_populates="organizations")


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String, ForeignKey("roles.id"))
    resource = Column(String, nullable=False)  # e.g., "deployments", "models"
    # e.g., "create", "read", "update", "delete"
    action = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    role = relationship("Role", back_populates="permissions")


class APIKey(Base):
    """API Key model for programmatic access."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # Hashed API key
    # First 8 chars for identification
    prefix = Column(String, nullable=False, index=True)

    scopes = Column(String)  # JSON array of scopes
    is_active = Column(Boolean, default=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="api_keys")
