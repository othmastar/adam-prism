"""
[PHASE5] Multi-tenancy support for Adam Prism.
Enables multiple organizations (tenants) to share an instance
with strict data isolation.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("adam_prism.tenancy")


class Role(Enum):
    """[PHASE5] RBAC roles within a tenant."""

    OWNER = "owner"  # Full control
    ADMIN = "admin"  # Manage users, settings, all resources
    EDITOR = "editor"  # Create/edit resources, run chat
    VIEWER = "viewer"  # Read-only access
    GUEST = "guest"  # Limited temporary access


# Role permission matrix
PERMISSIONS: dict[Role, set[str]] = {
    Role.OWNER: {
        "tenant.delete", "tenant.update", "tenant.read",
        "user.create", "user.read", "user.update", "user.delete",
        "role.assign",
        "chat.create", "chat.read", "chat.update", "chat.delete",
        "knowledge.create", "knowledge.read", "knowledge.update", "knowledge.delete",
        "settings.read", "settings.update",
        "billing.read", "billing.update",
        "audit.read",
    },
    Role.ADMIN: {
        "tenant.read", "tenant.update",
        "user.create", "user.read", "user.update", "user.delete",
        "role.assign",
        "chat.create", "chat.read", "chat.update", "chat.delete",
        "knowledge.create", "knowledge.read", "knowledge.update", "knowledge.delete",
        "settings.read", "settings.update",
        "audit.read",
    },
    Role.EDITOR: {
        "tenant.read",
        "user.read",
        "chat.create", "chat.read", "chat.update",
        "knowledge.create", "knowledge.read", "knowledge.update",
        "settings.read",
    },
    Role.VIEWER: {
        "tenant.read",
        "user.read",
        "chat.read",
        "knowledge.read",
        "settings.read",
    },
    Role.GUEST: {
        "chat.read",
        "knowledge.read",
    },
}


@dataclass
class Tenant:
    """[PHASE5] Represents an organization using Adam Prism."""

    id: str
    name: str
    slug: str  # URL-friendly identifier
    plan: str = "free"  # free, pro, enterprise
    created_at: float = 0.0
    is_active: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "plan": self.plan,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "settings": self.settings,
        }


@dataclass
class TenantMembership:
    """[PHASE5] User's membership in a tenant with a specific role."""

    user_id: str
    tenant_id: str
    role: Role
    joined_at: float = 0.0
    is_active: bool = True

    def has_permission(self, permission: str) -> bool:
        return permission in PERMISSIONS.get(self.role, set())


# [PHASE5] Context variable for the current request's tenant
_current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)
_current_membership: ContextVar[TenantMembership | None] = ContextVar(
    "current_membership", default=None
)


def get_current_tenant() -> Tenant | None:
    """[PHASE5] Get the current tenant from request context."""
    return _current_tenant.get()


def get_current_membership() -> TenantMembership | None:
    """[PHASE5] Get the current user's membership in the current tenant."""
    return _current_membership.get()


def set_current_tenant(tenant: Tenant | None, membership: TenantMembership | None = None) -> None:
    """[PHASE5] Set the current tenant context."""
    _current_tenant.set(tenant)
    _current_membership.set(membership)


def require_tenant() -> Tenant:
    """[PHASE5] Get current tenant or raise."""
    tenant = get_current_tenant()
    if tenant is None:
        raise PermissionError("No tenant in current context")
    return tenant


def require_permission(permission: str) -> None:
    """[PHASE5] Check current user has permission, raise if not."""
    membership = get_current_membership()
    if not membership or not membership.has_permission(permission):
        raise PermissionError(
            f"User {membership.user_id if membership else 'anonymous'} "
            f"lacks permission: {permission}"
        )


class TenantManager:
    """[PHASE5] Manages tenants and memberships."""

    def __init__(self):
        self._tenants: dict[str, Tenant] = {}
        self._memberships: dict[str, list[TenantMembership]] = {}  # user_id -> memberships

    def create_tenant(self, name: str, slug: str, plan: str = "free") -> Tenant:
        """[PHASE5] Create a new tenant."""
        import time
        import secrets

        tenant = Tenant(
            id=f"tenant_{secrets.token_hex(8)}",
            name=name,
            slug=slug,
            plan=plan,
            created_at=time.time(),
        )
        self._tenants[tenant.id] = tenant
        return tenant

    def add_member(self, user_id: str, tenant_id: str, role: Role) -> TenantMembership:
        """[PHASE5] Add a user to a tenant with a role."""
        import time

        membership = TenantMembership(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            joined_at=time.time(),
        )
        self._memberships.setdefault(user_id, []).append(membership)
        return membership

    def get_user_memberships(self, user_id: str) -> list[TenantMembership]:
        """[PHASE5] Get all tenants a user belongs to."""
        return [m for m in self._memberships.get(user_id, []) if m.is_active]

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)


# [PHASE5] Singleton instance
_tenant_manager: TenantManager | None = None


def get_tenant_manager() -> TenantManager:
    """[PHASE5] Get the singleton tenant manager."""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager
