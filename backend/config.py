"""Central config — reads from .env file."""
import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_LLM_MODEL = os.getenv("NIM_LLM_MODEL", "meta/llama-3.1-8b-instruct")
NIM_EMBED_MODEL = os.getenv("NIM_EMBED_MODEL", "nvidia/nv-embed-v2")

DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.35"))
TRAJECTORY_WINDOW = int(os.getenv("TRAJECTORY_WINDOW", "3"))

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
