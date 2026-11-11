import re
import secrets

# No O, 0, I, 1 or L: a Case ID is read off a screen or a photo and typed back in, often by someone upset.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CASE_ID_PATTERN = re.compile(rf"^KGPY-[{ALPHABET}]{{4}}-[{ALPHABET}]{{4}}$")


def generate_case_id() -> str:
    """KGPY-XXXX-XXXX from a cryptographically secure source: the ID is the only key to an anonymous report,
    so it must not be guessable (the standard `random` module is predictable)."""
    part = lambda: "".join(secrets.choice(ALPHABET) for _ in range(4))
    return f"KGPY-{part()}-{part()}"
