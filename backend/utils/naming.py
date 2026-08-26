import re
from collections.abc import Iterable

_SUFFIX_RE = re.compile(r"^(.*) \((\d+)\)$")


def next_unique_name(desired: str, existing_names: Iterable[str]) -> str:
    """
    Return `desired` unchanged if it doesn't collide (case-insensitively)
    with any name in `existing_names`. Otherwise, silently append/increment
    a numbered suffix until it's unique:

        "Report"      -> "Report (2)"   (if "Report" is taken)
        "Report (2)"  -> "Report (3)"   (if "Report (2)" is also taken)

    `existing_names` should already exclude the record being renamed (if
    any), so renaming a record to the name it already has is a no-op.
    """
    existing_lower = {n.lower() for n in existing_names}
    if desired.lower() not in existing_lower:
        return desired

    match = _SUFFIX_RE.match(desired)
    base = match.group(1) if match else desired
    n = int(match.group(2)) + 1 if match else 2

    candidate = f"{base} ({n})"
    while candidate.lower() in existing_lower:
        n += 1
        candidate = f"{base} ({n})"
    return candidate