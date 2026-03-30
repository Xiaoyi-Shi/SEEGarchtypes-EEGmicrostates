from __future__ import annotations

from collections.abc import Iterable


def canonicalize_channel_name(name: str) -> str:
    normalized = str(name).strip().upper()
    aliases = {
        "FP1": "Fp1",
        "FP2": "Fp2",
        "FZ": "Fz",
        "CZ": "Cz",
        "PZ": "Pz",
        "T3": "T7",
        "T4": "T8",
        "T5": "P7",
        "T6": "P8",
    }
    return aliases.get(normalized, normalized.capitalize() if len(normalized) == 2 and normalized.endswith("Z") else normalized)


def canonicalize_channel_names(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(canonicalize_channel_name(name) for name in names)


def channel_coverage_report(
    channel_names: Iterable[str],
    required_channels: Iterable[str],
) -> dict[str, object]:
    present = tuple(canonicalize_channel_names(channel_names))
    required = tuple(canonicalize_channel_names(required_channels))
    present_set = set(present)
    missing = tuple(channel for channel in required if channel not in present_set)
    extra = tuple(channel for channel in present if channel not in required)
    return {
        "present_channels": present,
        "missing_channels": missing,
        "extra_channels": extra,
        "covers_required": len(missing) == 0,
    }
