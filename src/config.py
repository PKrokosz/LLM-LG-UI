"""Application configuration constants."""

import os

LLAMA_BASE_URL = os.environ.get("LLAMA_BASE_URL", "http://127.0.0.1:8000")
LLAMA_MODEL = os.environ.get("LLAMA_MODEL", "local")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 384))
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.2))
STOP = ["<|end|>", "</s>", "<|endoftext|>"]
