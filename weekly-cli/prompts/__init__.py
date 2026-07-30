"""Load LLM prompt templates from prompts/ directory."""
import json
from pathlib import Path

PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by path (e.g. 'dialectical/grasping')."""
    path = PROMPT_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))["prompt"]
