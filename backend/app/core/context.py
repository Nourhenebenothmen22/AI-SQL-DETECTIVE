from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Actor and permission context for API requests.

    MVP operates in local developer mode without authentication. Keeping this
    context injected through FastAPI dependencies preserves a clean boundary
    for adding authentication and RBAC later without redesigning services.
    """

    actor_id: str = "local-dev"
    roles: tuple[str, ...] = ("analyst",)


def get_request_context() -> RequestContext:
    """Resolve the current request context."""
    return RequestContext()
