"""Configuration for the Resume Tailoring Pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file in the resume_tailoring directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Authentication Configuration:
# By default, uses AI Studio with GOOGLE_API_KEY from .env file.
# To use Vertex AI instead, set GOOGLE_GENAI_USE_VERTEXAI=TRUE in your .env
# and ensure you have Google Cloud credentials configured.

if os.getenv("GOOGLE_API_KEY"):
    # AI Studio mode (default): Use API key authentication
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
else:
    # Vertex AI mode: Fall back to Google Cloud credentials
    import google.auth

    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


@dataclass
class ResumeTailoringConfiguration:
    """Configuration for resume tailoring pipeline.

    Attributes:
        critic_model (str): Model for evaluation/review tasks.
        worker_model (str): Model for working/generation tasks.
        max_tailoring_iterations (int): Maximum iterations for the tailoring loop.
    """

    critic_model: str = "gemini-2.0-flash"
    worker_model: str = "gemini-3-flash-preview"
    max_tailoring_iterations: int = 3


config = ResumeTailoringConfiguration()
