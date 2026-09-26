# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    general_model: str = "qwen2.5:3b-instruct"
    vision_model: str = "moondream"
    embedding_model: str = "nomic-embed-text"
    ollama_models_dir: str = "D:\\SovereignAI\\models"
    
    storage_root: str = "D:\\SovereignAI\\storage"
    max_upload_size_mb: int = 50
    # Comma-separated list of allowed browser origins. Defaults preserve the
    # local dev setup; Docker Compose overrides this via CORS_ORIGINS.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    rag_top_k: int = 3
    rag_max_top_k: int = 10
    rag_similarity_threshold: float = 0.35
    rag_max_context_chars: int = 4000
    
    max_agent_steps: int = 10
    max_replans: int = 2

    @property
    def cors_origins_list(self) -> list:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_dir(self) -> str:
        import os
        return os.path.join(self.storage_root, "uploads")
        
    @property
    def projects_dir(self) -> str:
        import os
        return os.path.join(self.storage_root, "projects")
        
    @property
    def reviews_dir(self) -> str:
        import os
        return os.path.join(self.storage_root, "reviews")
        
    @property
    def security_dir(self) -> str:
        import os
        return os.path.join(self.storage_root, "security")

    class Config:
        env_file = ".env"

settings = Settings()
