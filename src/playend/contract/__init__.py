"""The observation contract: what the teacher writes for each frame, and how it is validated."""

from .contract import (
    COUNTER_KINDS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    TIMER_KINDS,
    empty_observation,
    output_schema,
    parse_strict_json,
    upgrade_legacy,
    upgrade_v20,
    validate_any,
    validate_observation,
)

__all__ = [
    "COUNTER_KINDS",
    "SCHEMA_VERSION",
    "SUPPORTED_VERSIONS",
    "TIMER_KINDS",
    "empty_observation",
    "output_schema",
    "parse_strict_json",
    "upgrade_legacy",
    "upgrade_v20",
    "validate_any",
    "validate_observation",
]
