import json
import os
from dotenv import load_dotenv

# Load local.settings.json when running locally via uvicorn
_settings_path = os.path.join(
    os.path.dirname(__file__), "..", "local.settings.json"
)
if os.path.exists(_settings_path):
    with open(_settings_path) as f:
        _data = json.load(f)
    for k, v in _data.get("Values", {}).items():
        os.environ.setdefault(k, v)

load_dotenv()


class Settings:
    SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    SQL_SERVER = os.getenv("SQL_SERVER")
    SQL_DATABASE = os.getenv("SQL_DATABASE")
    SQL_USERNAME = os.getenv("SQL_USERNAME")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD")

    APP_NAME = "SWA Project Moderation POC API"
    CONTENT_SCOPE = "PROJECT_ONLY"

    ENABLED_POLICIES_RAW = os.getenv("ENABLED_POLICIES", "TYPE-PROJECT-01")

    USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")

    LOG_DIR = os.getenv("LOG_DIR", "logs")

    @property
    def enabled_policies(self) -> list[str]:
        return [
            policy.strip()
            for policy in self.ENABLED_POLICIES_RAW.split(",")
            if policy.strip()
        ]


settings = Settings()
