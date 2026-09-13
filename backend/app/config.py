"""Application settings (env-overridable in later phases)."""

from dataclasses import dataclass, field


@dataclass
class Settings:
    """Central configuration for the backend service."""

    app_name: str = "Container Congestion Predictor & Port Operations Optimiser"
    host: str = "127.0.0.1"
    port: int = 8000
    # Vite dev server origins (frontend runs on 5173 during development).
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://port-optimizer.vercel.app",
            "https://ship-management.vercel.app",
            "https://port-optimizer-api.onrender.com",
        ]
    )


settings = Settings()
