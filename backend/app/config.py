from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    alembic_database_url: str

    openai_api_key: str = ""
    dashboard_secret_token: str = "changeme-generate-a-long-random-string"

    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:5173"

    max_batch_size: int = 500
    max_payload_size_mb: int = 10
    max_field_length_chars: int = 32768

    eval_worker_poll_interval_sec: float = 2.0
    eval_worker_max_retries: int = 3
    llm_judge_default_model: str = "gpt-4o-mini"

    scheduler_jobstore_path: str = "./scheduler_jobs.sqlite"
    drift_snapshot_interval_min: int = 30
    alert_check_interval_min: int = 5
    rollup_interval_min: int = 60

    default_alert_webhook_url: str = ""
    pricing_table_path: str = "./config/model_pricing.json"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()