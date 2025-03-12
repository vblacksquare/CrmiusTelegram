
from uuid import uuid3, NAMESPACE_URL


def string_to_uuid(string: str) -> str:
    return uuid3(NAMESPACE_URL, string.lower()).hex
