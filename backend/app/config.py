import os
from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EncroWatch AI"
    PROJECT_VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"

    # Environment: 'production', 'staging', 'development'
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security & Cryptographic Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "encrowatch-ai-super-secret-key-mca-major-2026")
    ALGORITHM: str = "HS256"
    # Default: 1 day in production (1440 mins), 7 days in dev (10080 mins)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "1440" if os.getenv("ENVIRONMENT") == "production" else "10080"
    ))

    # Demo Persona Switching (strictly disabled by default in production)
    ALLOW_DEMO_SWITCH: bool = (
        os.getenv("ALLOW_DEMO_SWITCH", "false" if os.getenv("ENVIRONMENT") == "production" else "true").lower() in ("true", "1")
    )
    
    # MongoDB Config
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "encrowatch_ai_db")
    
    # Storage
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    )

    # CORS Allowed Origins
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000")
    )
    
    # City Center Coordinates (Bengaluru default)
    DEFAULT_LAT: float = float(os.getenv("DEFAULT_LAT", "12.9716"))
    DEFAULT_LNG: float = float(os.getenv("DEFAULT_LNG", "77.5946"))

    # AI Model Configuration
    YOLO_WEIGHTS_PATH: str = os.getenv(
        "YOLO_WEIGHTS_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "ai", "weights", "yolov5n.onnx"))
    )
    ALLOW_DEMO_MODE: bool = os.getenv("ALLOW_DEMO_MODE", "false").lower() in ("true", "1")
    
    model_config = ConfigDict(case_sensitive=True, extra="allow")

    @property
    def allowed_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_environment(self) -> List[str]:
        """
        Validates environment variables for production readiness.
        Raises ValueError on security vulnerabilities or configuration blockers.
        """
        warnings = []
        is_prod = self.ENVIRONMENT.lower() == "production"

        if is_prod:
            # 1. SECRET_KEY strength verification
            weak_keys = [
                "encrowatch-ai-super-secret-key-mca-major-2026",
                "secret",
                "changeme",
                "CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY_AT_LEAST_32_CHARS"
            ]
            if self.SECRET_KEY in weak_keys or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL PRODUCTION SECURITY ERROR: SECRET_KEY must be a cryptographically strong "
                    "secret of at least 32 characters in production. Generate via: python scripts/generate_secret_key.py"
                )

            # 2. Demo controls configuration notice
            if self.ALLOW_DEMO_SWITCH:
                warnings.append("Notice: ALLOW_DEMO_SWITCH is enabled for evaluation and testing.")
            if self.ALLOW_DEMO_MODE:
                warnings.append("Notice: ALLOW_DEMO_MODE is enabled for evaluation and testing.")

            # 3. Wildcard CORS with credentials check
            if "*" in self.allowed_origins_list:
                raise ValueError("CRITICAL SECURITY ERROR: Wildcard '*' in CORS_ORIGINS is prohibited in production.")
        else:
            if len(self.SECRET_KEY) < 16:
                warnings.append("Notice: SECRET_KEY is shorter than 16 characters.")

        # 4. Verify MongoDB URI scheme
        if not self.MONGODB_URI.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(f"Invalid MONGODB_URI scheme: must start with mongodb:// or mongodb+srv://")

        return warnings

settings = Settings()
