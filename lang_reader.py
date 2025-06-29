import json
from pathlib import Path
from typing import Dict

LANG_DIR = Path(__file__).parent / "lang"

_cache: Dict[str, dict] = {}


def get_translation(lang_code: str = "en") -> dict:
    if lang_code in _cache:
        return _cache[lang_code]
    file_path = LANG_DIR / f"{lang_code}.json"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[lang_code] = data
    return data 