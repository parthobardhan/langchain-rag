"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str
    mongodb_database: str = "rag_db"
    mongodb_collection: str = "documents"
    vector_index_name: str = "vector_index"

    voyage_api_key: str
    voyage_embedding_model: str = "voyage-4-lite"
    voyage_embedding_dimensions: int = 1024

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4


def get_settings() -> Settings:
    return Settings()
