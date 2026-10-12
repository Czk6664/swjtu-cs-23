from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
STATE_DIR = ROOT_DIR / "services" / "api" / ".task_state"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    app_name: str = "traffic-decision-api"
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")

    traffic_forecast_results_dir: Path = Field(
        default=ROOT_DIR / "大作业1" / "results",
        alias="TRAFFIC_FORECAST_RESULTS_DIR",
    )
    traffic_detection_run_dir: Path = Field(
        default=ROOT_DIR / "大作业2" / "exp_C_704_b8_w0_e50" / "exp_C_704_b8_w0_e50",
        alias="TRAFFIC_DETECTION_RUN_DIR",
    )
    traffic_detection_dataset_config: Path = Field(
        default=ROOT_DIR / "大作业2" / "traffic_sign_detection" / "configs" / "dataset" / "tt100k.yaml",
        alias="TRAFFIC_DETECTION_DATASET_CONFIG",
    )
    task_backend: str = Field(default="memory", alias="TASK_BACKEND")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    hermes_enabled: bool = Field(default=False, alias="HERMES_ENABLED")
    hermes_command: str = Field(default="hermes", alias="HERMES_COMMAND")
    hermes_base_url: str | None = Field(default=None, alias="HERMES_BASE_URL")
    hermes_timeout_seconds: int = Field(default=120, alias="HERMES_TIMEOUT_SECONDS")
    hermes_workspace_root: Path = Field(default=ROOT_DIR, alias="HERMES_WORKSPACE_ROOT")
    hermes_templates_dir: Path = Field(default=STATE_DIR / "hermes" / "templates", alias="HERMES_TEMPLATES_DIR")
    hermes_payload_dir: Path = Field(default=STATE_DIR / "hermes" / "payloads", alias="HERMES_PAYLOAD_DIR")
    hermes_logs_dir: Path = Field(default=STATE_DIR / "hermes" / "logs", alias="HERMES_LOGS_DIR")
    hermes_wsl_enabled: bool = Field(default=True, alias="HERMES_WSL_ENABLED")
    hermes_wsl_command: str = Field(default="wsl.exe", alias="HERMES_WSL_COMMAND")
    hermes_wsl_distribution: str | None = Field(default="Ubuntu-22.04", alias="HERMES_WSL_DISTRIBUTION")
    hermes_wsl_workspace_root: str | None = Field(default=None, alias="HERMES_WSL_WORKSPACE_ROOT")
    report_output_dir: Path = Field(default=STATE_DIR / "reports", alias="REPORT_OUTPUT_DIR")
    audio_output_dir: Path = Field(default=STATE_DIR / "audio", alias="AUDIO_OUTPUT_DIR")
    summary_output_dir: Path = Field(default=STATE_DIR / "summaries", alias="SUMMARY_OUTPUT_DIR")


settings = Settings()

for path in (
    STATE_DIR,
    settings.report_output_dir,
    settings.audio_output_dir,
    settings.summary_output_dir,
    settings.hermes_templates_dir,
    settings.hermes_payload_dir,
    settings.hermes_logs_dir,
):
    path.mkdir(parents=True, exist_ok=True)
