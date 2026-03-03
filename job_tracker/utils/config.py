"""
Configuration Management
Loads and validates environment variables for database connection.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from job_tracker.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """
    Application configuration loaded from environment variables.

    Attributes:
        db_host: PostgreSQL host address
        db_port: PostgreSQL port number
        db_name: Database name
        db_user: Database username
        db_password: Database password
    """

    def __init__(self):
        """Initialize configuration from environment variables."""
        logger.debug("Loading configuration from environment variables")

        # Load .env file from project root
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            logger.debug(f"Loading .env file from {env_path}")
            load_dotenv(env_path)
        else:
            logger.warning(f".env file not found at {env_path}")

        # Load database configuration
        self.db_host: str = os.getenv('DB_HOST', 'localhost')
        self.db_port: int = int(os.getenv('DB_PORT', '5432'))
        self.db_name: str = os.getenv('DB_NAME', 'job_tracker')
        self.db_user: str = os.getenv('DB_USER', 'postgres') # Must change later
        self.db_password: str = os.getenv('DB_PASSWORD', 'm0535266305') # Must change later

        logger.debug(f"Database configuration loaded: {self}")

        # Validate configuration
        self._validate()
        logger.info("Configuration validated successfully")

    def _validate(self) -> None:
        """
        Validate that all required configuration values are present.

        :raises ConfigError: If required configuration is missing or invalid
        :return: None
        """
        logger.debug("Validating configuration...")
        missing = []

        if not self.db_user:
            missing.append('DB_USER')
        if not self.db_password:
            missing.append('DB_PASSWORD')

        if missing:
            error_msg = f"Missing required configuration: {', '.join(missing)}. Please set these in your .env file."
            logger.error(error_msg)
            raise ConfigError(error_msg)

        # Validate port is valid
        if not (1 <= self.db_port <= 65535):
            error_msg = f"Invalid DB_PORT: {self.db_port}. Must be between 1 and 65535."
            logger.error(error_msg)
            raise ConfigError(error_msg)

        logger.debug("All configuration validations passed")

    def get_connection_string(self) -> str:
        """
        Generate a PostgreSQL connection string for psycopg2.

        :return: Connection string with format: "host=X port=Y dbname=Z user=A password=B"
        """
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )

    def __repr__(self) -> str:
        """String representation (hides password for security)."""
        return (
            f"Config(host={self.db_host}, port={self.db_port}, "
            f"db={self.db_name}, user={self.db_user})"
        )
