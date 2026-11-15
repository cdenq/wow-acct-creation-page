"""Allow-list validation. This is the security boundary: nothing that fails here reaches the SOAP command."""

import re

# AccountMgr.h: MAX_ACCOUNT_STR 17, MAX_PASS_STR 16. Both caps below stay under those.
ACCOUNT_RE = re.compile(r"[A-Za-z0-9]{3,16}")
# No spaces (the console splits arguments on them), no % or braces (format strings), and no XML specials.
PASSWORD_RE = re.compile(r"[A-Za-z0-9!@#$*_.-]{6,16}")

ACCOUNT_RULE = "3 to 16 letters or digits."
PASSWORD_RULE = "6 to 16 characters: letters, digits, or ! @ # $ * _ . -"


def validate_account(name: str) -> str | None:
    """Return the normalized (uppercased) name, or None if invalid."""
    if ACCOUNT_RE.fullmatch(name):
        return name.upper()
    return None


def validate_password(password: str) -> bool:
    return PASSWORD_RE.fullmatch(password) is not None
