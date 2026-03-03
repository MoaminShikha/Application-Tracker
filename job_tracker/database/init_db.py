from pathlib import Path

from job_tracker.utils.config import Config
from job_tracker.utils.logger import get_logger
from .connection import DatabaseConnection
from .exceptions import DatabaseError

logger = get_logger(__name__)


class InitDB:
    """
    Database initialization helper.

    Loads schema SQL and applies it to a target PostgreSQL database.
    """

    def __init__(self, schema_path: str | Path | None = None):
        """
        Initialize InitDB with configuration and schema location.

        :param schema_path: Optional path to schema SQL file
        :return: None
        """
        self.config = Config()
        self.connection_string = self.config.get_connection_string()

        if schema_path is None:
            project_root = Path(__file__).resolve().parents[2]
            schema_path = project_root / "database_setup" / "schema.sql"

        self.schema_path = Path(schema_path)
        self._db = DatabaseConnection(self.connection_string)
        self._expected_tables = {
            "companies",
            "positions",
            "applications",
            "application_events",
            "recruiters",
            "application_statuses",
        }

    def load_schema(self):
        """
        Load the schema SQL from disk.

        :return: Schema SQL as a string
        :raises DatabaseError: If schema file is missing or empty
        :raises FileNotFoundError: If schema file cannot be read
        """
        try:
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

            schema_sql = self.schema_path.read_text(encoding="utf-8").strip()
            if not schema_sql:
                raise DatabaseError(f"Schema file cant be read: {self.schema_path}")

            logger.info(f"Loaded schema from {self.schema_path}")
            return schema_sql
        except (OSError, FileNotFoundError) as exc:
            logger.error(f"Failed to load schema: {exc}")
            raise DatabaseError(f"Failed to load schema: {exc}")

    def apply_schema(self):
        """
        Apply the schema SQL to the database.

        :return: None
        :raises DatabaseError: If schema execution fails
        """
        schema_sql = self.load_schema()

        try:
            with self._db as db:
                db.execute_query(schema_sql, fetch=False)
            logger.info("Schema applied successfully")
        except DatabaseError:
            logger.error("Failed to apply schema")
            raise

    def _get_missing_tables(self):
        """
        Get a list of expected tables that are missing.

        :return: List of missing table names
        :raises DatabaseError: If lookup fails
        """
        query = (
            "SELECT table_name "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )

        try:
            with self._db as db:
                rows = db.execute_query(query, fetch=True)
            existing = {row[0] for row in rows}
            return sorted(self._expected_tables - existing)
        except DatabaseError:
            logger.error("Failed to query existing tables")
            raise

    def verify_tables(self):
        """
        Verify that all expected tables exist.

        :return: None
        :raises DatabaseError: If any required tables are missing
        """
        missing = self._get_missing_tables()
        if missing:
            raise DatabaseError(f"Missing tables: {', '.join(missing)}")

        logger.info("All expected tables verified")

    def seed_reference_data(self):
        """
        Seed reference data required by the application.

        Uses UPSERT to keep this idempotent.
        """
        seed_sql = (
            "INSERT INTO application_statuses (status_name, description, is_terminal) VALUES "
            "('Applied', 'Initial application submitted', FALSE), "
            "('Interview Scheduled', 'Interview has been scheduled', FALSE), "
            "('Interviewed', 'Interview completed', FALSE), "
            "('Offer', 'Offer received', FALSE), "
            "('Accepted', 'Offer accepted', TRUE), "
            "('Rejected', 'Application rejected', TRUE), "
            "('Withdrawn', 'Application withdrawn by candidate', TRUE) "
            "ON CONFLICT (status_name) DO NOTHING;"
        )

        try:
            with self._db as db:
                db.execute_query(seed_sql, fetch=False)
            logger.info("Reference data seeded successfully")
        except DatabaseError:
            logger.error("Failed to seed reference data")
            raise

    def initialize_database(self):
        """
        Initialize the database schema.

        :return: None
        :raises DatabaseError: If initialization fails
        """
        try:
            missing = self._get_missing_tables()
            if missing:
                logger.info(f"Missing tables detected: {', '.join(missing)}")
                self.apply_schema()
                self.verify_tables()
            else:
                logger.info("Schema already exists; skipping initialization")

            self.seed_reference_data()
            logger.info("Database initialization completed")
        except DatabaseError:
            logger.error("Database initialization failed")
            raise
