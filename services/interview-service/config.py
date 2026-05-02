import os
from dotenv import load_dotenv

# Load correct .env file based on ENVIRONMENT variable
env = os.getenv("ENVIRONMENT", "development")
env_file = os.path.join(os.path.dirname(__file__), f".env.{env}")
load_dotenv(env_file)

# All config in one place — never hardcode these anywhere else
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
ENVIRONMENT     = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS    = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DB_URL          = os.getenv("DB_URL", "sqlite:///./local.db")
REDIS_URL       = os.getenv("REDIS_URL", "redis://localhost:6379")

IS_PRODUCTION   = ENVIRONMENT == "production"
