from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Pic2Ads API", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    api_prefix: str = Field(default="/v1", alias="API_PREFIX")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    supabase_db_url: str | None = Field(default=None, alias="SUPABASE_DB_URL")
    supabase_pooler_url: str | None = Field(default=None, alias="SUPABASE_POOLER_URL")

    temporal_enabled: bool = Field(default=False, alias="TEMPORAL_ENABLED")
    temporal_address: str = Field(default="localhost:7233", alias="TEMPORAL_ADDRESS")
    temporal_namespace: str = Field(default="default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field(default="pic2ads-main", alias="TEMPORAL_TASK_QUEUE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_vision_model: str = Field(default="gpt-4o", alias="OPENAI_VISION_MODEL")
    openai_script_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_SCRIPT_MODEL")

    fal_api_key: str | None = Field(default=None, alias="FAL_API_KEY")
    fal_queue_base_url: str = Field(default="https://queue.fal.run", alias="FAL_QUEUE_BASE_URL")
    fal_seedance_text_endpoint: str = Field(
        default="bytedance/seedance-2.0/text-to-video",
        alias="FAL_SEEDANCE_TEXT_ENDPOINT",
    )
    fal_seedance_image_endpoint: str = Field(
        default="bytedance/seedance-2.0/image-to-video",
        alias="FAL_SEEDANCE_IMAGE_ENDPOINT",
    )
    fal_seedance_reference_endpoint: str = Field(
        default="bytedance/seedance-2.0/reference-to-video",
        alias="FAL_SEEDANCE_REFERENCE_ENDPOINT",
    )
    fal_callback_url: str | None = Field(default=None, alias="FAL_CALLBACK_URL")
    fal_webhook_secret: str | None = Field(default=None, alias="FAL_WEBHOOK_SECRET")
    fal_max_retries: int = Field(default=3, alias="FAL_MAX_RETRIES")
    fal_retry_base_delay_seconds: int = Field(default=30, alias="FAL_RETRY_BASE_DELAY_SECONDS")
    fal_retry_worker_enabled: bool = Field(default=False, alias="FAL_RETRY_WORKER_ENABLED")
    fal_retry_worker_interval_seconds: int = Field(
        default=20,
        alias="FAL_RETRY_WORKER_INTERVAL_SECONDS",
    )
    fal_retry_worker_batch_size: int = Field(default=10, alias="FAL_RETRY_WORKER_BATCH_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "database_url",
        "supabase_db_url",
        "supabase_pooler_url",
        "openai_api_key",
        "fal_api_key",
        "fal_callback_url",
        mode="before",
    )
    @classmethod
    def _normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().strip('"').strip("'")
        return normalized or None

    @field_validator("fal_api_key")
    @classmethod
    def _normalize_fal_api_key(cls, value: str | None) -> str | None:
        if not value:
            return value
        lowered = value.lower()
        if lowered.startswith("bearer "):
            return value[7:].strip()
        if lowered.startswith("key "):
            return value[4:].strip()
        return value

    @property
    def resolved_database_url(self) -> str | None:
        return self.database_url or self.supabase_db_url or self.supabase_pooler_url


settings = Settings()
