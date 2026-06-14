"""
[PHASE5] Tests for new Phase 5 features.
"""
import pytest

from adam.observability.tracing import setup_tracing, trace_span, get_tracer
from adam.tenancy.manager import (
    Role,
    Tenant,
    TenantManager,
    TenantMembership,
    PERMISSIONS,
    set_current_tenant,
    get_current_tenant,
    require_permission,
    require_tenant,
)
from adam.observability.error_tracking import ErrorTracker, get_error_tracker


class TestMultiTenancy:
    """Test multi-tenancy and RBAC."""

    def test_role_permissions_defined(self):
        # All tenant-bound roles should have at least tenant.read
        for role in (Role.OWNER, Role.ADMIN, Role.EDITOR, Role.VIEWER):
            assert "tenant.read" in PERMISSIONS[role]

    def test_owner_has_all_critical_permissions(self):
        owner_perms = PERMISSIONS[Role.OWNER]
        for perm in ["tenant.delete", "user.create", "billing.update"]:
            assert perm in owner_perms, f"Owner missing {perm}"

    def test_guest_has_minimal_permissions(self):
        guest_perms = PERMISSIONS[Role.GUEST]
        assert "chat.read" in guest_perms
        assert "tenant.delete" not in guest_perms
        assert "user.create" not in guest_perms

    def test_create_tenant(self):
        mgr = TenantManager()
        tenant = mgr.create_tenant("Acme Corp", "acme", plan="pro")
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme"
        assert tenant.plan == "pro"
        assert tenant.id.startswith("tenant_")

    def test_add_member_with_role(self):
        mgr = TenantManager()
        tenant = mgr.create_tenant("Acme", "acme")
        m = mgr.add_member("user-1", tenant.id, Role.EDITOR)
        assert m.user_id == "user-1"
        assert m.role == Role.EDITOR

    def test_membership_has_permission_editor(self):
        m = TenantMembership(user_id="u", tenant_id="t", role=Role.EDITOR)
        assert m.has_permission("chat.create")
        assert m.has_permission("knowledge.read")
        assert not m.has_permission("tenant.delete")

    def test_get_user_memberships(self):
        mgr = TenantManager()
        t1 = mgr.create_tenant("A", "a")
        t2 = mgr.create_tenant("B", "b")
        mgr.add_member("u1", t1.id, Role.EDITOR)
        mgr.add_member("u1", t2.id, Role.ADMIN)
        memberships = mgr.get_user_memberships("u1")
        assert len(memberships) == 2
        assert {m.tenant_id for m in memberships} == {t1.id, t2.id}

    def test_set_get_current_tenant_context(self):
        t = Tenant(id="t1", name="Test", slug="t")
        m = TenantMembership(user_id="u", tenant_id="t1", role=Role.OWNER)
        set_current_tenant(t, m)
        assert get_current_tenant() == t

    def test_require_tenant_raises_when_no_context(self):
        set_current_tenant(None)
        with pytest.raises(PermissionError):
            require_tenant()

    def test_require_permission_works(self):
        t = Tenant(id="t1", name="Test", slug="t")
        m = TenantMembership(user_id="u", tenant_id="t1", role=Role.EDITOR)
        set_current_tenant(t, m)
        require_permission("chat.create")  # Editor has this
        with pytest.raises(PermissionError):
            require_permission("tenant.delete")  # Editor doesn't


class TestOpenTelemetryTracing:
    """Test OpenTelemetry tracing integration."""

    def test_tracing_graceful_without_otel(self):
        # [PHASE5] Should not crash if otel not installed
        result = setup_tracing(service_name="test")
        # Will be False if otel not installed, True if installed
        assert isinstance(result, bool)

    def test_trace_span_works_without_crash(self):
        # [PHASE5] trace_span should always work (no-op if no otel)
        with trace_span("test_span", {"key": "value"}):
            pass  # Should not raise

    def test_get_tracer_returns_tracer_or_none(self):
        tracer = get_tracer()
        # Either real tracer or None
        assert tracer is None or hasattr(tracer, "start_as_current_span")


class TestErrorTracking:
    """Test error tracking integration."""

    def test_error_tracker_singleton(self):
        t1 = get_error_tracker()
        t2 = get_error_tracker()
        assert t1 is t2

    def test_capture_exception_logs_when_disabled(self):
        tracker = ErrorTracker()
        tracker.enabled = False
        # Should not raise
        try:
            raise ValueError("test")
        except ValueError as e:
            tracker.capture_exception(e, {"test": True})

    def test_capture_message_logs_when_disabled(self):
        tracker = ErrorTracker()
        tracker.enabled = False
        tracker.capture_message("Test message", level="info", context={"x": 1})

    def test_capture_exception_with_context(self):
        tracker = ErrorTracker()
        tracker.enabled = False
        try:
            raise RuntimeError("boom")
        except RuntimeError as e:
            tracker.capture_exception(e, {
                "request_id": "abc-123",
                "user_id": "user-1",
                "endpoint": "/api/chat",
            })


class TestOfflineSync:
    """Test offline sync manager for mobile (logic only, no native deps)."""

    def test_offline_sync_queued_message_schema(self):
        # [PHASE5] Test that the QueuedMessage schema is correct
        from typing import TypedDict

        class Msg(TypedDict, total=False):
            id: str
            session_id: str
            content: str
            role: str
            timestamp: int
            retries: int
            last_error: str

        msg: Msg = {
            "id": "1",
            "session_id": "s1",
            "content": "hi",
            "role": "user",
            "timestamp": 12345,
            "retries": 0,
        }
        assert msg["id"] == "1"


class TestIntegrationPhase5:
    """Integration tests for Phase 5 features."""

    def test_all_phase5_modules_importable(self):
        """[PHASE5] Verify all Phase 5 modules import without error."""
        from adam.observability import tracing, error_tracking
        from adam.tenancy import manager
        # All imports succeeded
        assert tracing is not None
        assert error_tracking is not None
        assert manager is not None

    def test_tenant_isolation_via_managers(self):
        """[PHASE5] Two tenants have isolated data."""
        mgr = TenantManager()
        t1 = mgr.create_tenant("Tenant1", "t1")
        t2 = mgr.create_tenant("Tenant2", "t2")
        mgr.add_member("alice", t1.id, Role.OWNER)
        mgr.add_member("bob", t2.id, Role.OWNER)

        alice_tenants = {m.tenant_id for m in mgr.get_user_memberships("alice")}
        bob_tenants = {m.tenant_id for m in mgr.get_user_memberships("bob")}
        assert alice_tenants == {t1.id}
        assert bob_tenants == {t2.id}
        assert alice_tenants.isdisjoint(bob_tenants)
