def handle_normalize_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return value
    return " ".join(word.capitalize() for word in value.split())
