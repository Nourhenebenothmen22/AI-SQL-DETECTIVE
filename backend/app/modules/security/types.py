from dataclasses import dataclass

# Private process-local sentinel used to prevent external callers from
# constructing ValidatedSQL objects directly and bypassing SecurityGate.
_GATE_SENTINEL = object()


@dataclass(frozen=True, slots=True)
class SecurityRuleCheck:
    """Result of one deterministic security rule check."""

    rule: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ValidatedSQL:
    """Sealed validated SQL artifact minted exclusively by SecurityGate."""

    original_sql: str
    normalized_sql: str
    execution_sql: str
    enforced_limit: int
    limit_was_injected: bool
    limit_was_clamped: bool
    has_select_star: bool
    checks: tuple[SecurityRuleCheck, ...]
    _token: object = _GATE_SENTINEL

    def __post_init__(self) -> None:
        if self._token is not _GATE_SENTINEL:
            raise PermissionError(
                "ValidatedSQL cannot be instantiated directly; use SecurityGate.validate()."
            )


def mint_validated_sql(
    *,
    original_sql: str,
    normalized_sql: str,
    execution_sql: str,
    enforced_limit: int,
    limit_was_injected: bool,
    limit_was_clamped: bool,
    has_select_star: bool,
    checks: tuple[SecurityRuleCheck, ...],
) -> ValidatedSQL:
    """Internal factory used exclusively by SecurityGate."""
    return ValidatedSQL(
        original_sql=original_sql,
        normalized_sql=normalized_sql,
        execution_sql=execution_sql,
        enforced_limit=enforced_limit,
        limit_was_injected=limit_was_injected,
        limit_was_clamped=limit_was_clamped,
        has_select_star=has_select_star,
        checks=checks,
        _token=_GATE_SENTINEL,
    )


def verify_validated_sql(candidate: object) -> ValidatedSQL:
    """Verify that a SQL artifact is a genuine ValidatedSQL minted by SecurityGate."""
    if not isinstance(candidate, ValidatedSQL) or candidate._token is not _GATE_SENTINEL:
        raise TypeError(
            "SQLExecutor requires a ValidatedSQL object produced by SecurityGate.validate()."
        )
    return candidate


@dataclass(frozen=True, slots=True)
class SecurityValidationResult:
    """Deterministic outcome from the Independent Security Gate."""

    passed: bool
    validated_sql: ValidatedSQL | None
    violations: tuple[str, ...]
    checks: tuple[SecurityRuleCheck, ...]
