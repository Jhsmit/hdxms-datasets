import difflib


def diff_sequence(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()
