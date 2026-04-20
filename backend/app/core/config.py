from pydantic import Field
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

    kie_api_key: str | None = Field(default=None, alias="KIE_API_KEY")
    kie_base_url: str = Field(default="https://api.kie.ai", alias="KIE_BASE_URL")
    kie_create_task_path: str = Field(
        default="/api/v1/jobs/createTask",
        alias="KIE_CREATE_TASK_PATH",
    )
    kie_task_detail_path: str = Field(
        default="/api/v1/jobs/getTaskDetail",
        alias="KIE_TASK_DETAIL_PATH",
    )
    kie_default_model: str = Field(default="bytedance/seedance-2", alias="KIE_DEFAULT_MODEL")
    kie_callback_url: str | None = Field(default=None, alias="KIE_CALLBACK_URL")
    kie_webhook_secret: str | None = Field(default=None, alias="KIE_WEBHOOK_SECRET")
    kie_max_retries: int = Field(default=3, alias="KIE_MAX_RETRIES")
    kie_retry_base_delay_seconds: int = Field(default=30, alias="KIE_RETRY_BASE_DELAY_SECONDS")
    kie_retry_worker_enabled: bool = Field(default=False, alias="KIE_RETRY_WORKER_ENABLED")
    kie_retry_worker_interval_seconds: int = Field(
        default=20,
        alias="KIE_RETRY_WORKER_INTERVAL_SECONDS",
    )
    kie_retry_worker_batch_size: int = Field(default=10, alias="KIE_RETRY_WORKER_BATCH_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str | None:
        return self.database_url or self.supabase_db_url or self.supabase_pooler_url


settings = Settings()
