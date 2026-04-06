from pathlib import Path

from job_tracker.utils.config import Config
from job_tracker.utils.logger import get_logger
from .connection import DatabaseConnection
from .query_executor import QueryExecutor
from .exceptions import DatabaseError

logger = get_logger(__name__)


class InitDB:
    """
    Database initialization helper.

    Loads schema SQL and applies it to a target PostgreSQL database.
    """

    def __init__(self, schema_path: str | Path | None = None):
        self.config = Config()
        self.connection_string = self.config.get_connection_string()

        if schema_path is None:
            project_root = Path(__file__).resolve().parents[2]
            schema_path = project_root / "database_setup" / "schema.sql"

        self.schema_path = Path(schema_path)
        self._expected_tables = {
            "companies",
            "positions",
            "applications",
            "application_events",
            "recruiters",
            "application_statuses",
        }

    def _connect(self) -> DatabaseConnection:
        return DatabaseConnection(self.connection_string)

    def load_schema(self) -> str:
        try:
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
            schema_sql = self.schema_path.read_text(encoding="utf-8").strip()
            if not schema_sql:
                raise DatabaseError(f"Schema file is empty: {self.schema_path}")
            logger.info(f"Loaded schema from {self.schema_path}")
            return schema_sql
        except (OSError, FileNotFoundError) as exc:
            logger.error(f"Failed to load schema: {exc}")
            raise DatabaseError(f"Failed to load schema: {exc}")

    def apply_schema(self) -> None:
        schema_sql = self.load_schema()
        try:
            with self._connect() as db:
                executor = QueryExecutor(db.connection)
                executor.execute_update(schema_sql)
                db.connection.commit()
            logger.info("Schema applied successfully")
        except DatabaseError:
            logger.error("Failed to apply schema")
            raise

    def _get_missing_tables(self) -> list[str]:
        query = (
            "SELECT table_name "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
        try:
            with self._connect() as db:
                executor = QueryExecutor(db.connection)
                rows = executor.execute_query(query)
            existing = {row["table_name"] for row in rows}
            return sorted(self._expected_tables - existing)
        except DatabaseError:
            logger.error("Failed to query existing tables")
            raise

    def verify_tables(self) -> None:
        missing = self._get_missing_tables()
        if missing:
            raise DatabaseError(f"Missing tables: {', '.join(missing)}")
        logger.info("All expected tables verified")

    def seed_reference_data(self) -> None:
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
            with self._connect() as db:
                executor = QueryExecutor(db.connection)
                executor.execute_update(seed_sql)
                db.connection.commit()
            logger.info("Reference data seeded successfully")
        except DatabaseError:
            logger.error("Failed to seed reference data")
            raise

    def ensure_schema_compatibility(self) -> None:
        """Apply additive schema updates for existing databases."""
        compatibility_sql = """
            ALTER TABLE applications
            ADD COLUMN IF NOT EXISTS job_id VARCHAR(100);

            ALTER TABLE applications
            DROP CONSTRAINT IF EXISTS applications_job_id_check;

            ALTER TABLE applications
            ADD CONSTRAINT applications_job_id_check
            CHECK (job_id IS NULL OR job_id <> '');

            CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications (job_id);
        """
        try:
            with self._connect() as db:
                executor = QueryExecutor(db.connection)
                executor.execute_update(compatibility_sql)
                db.connection.commit()
            logger.info("Schema compatibility checks completed")
        except DatabaseError:
            logger.error("Failed while applying schema compatibility updates")
            raise

    def initialize_database(self) -> None:
        try:
            missing = self._get_missing_tables()
            if missing:
                logger.info(f"Missing tables detected: {', '.join(missing)}")
                self.apply_schema()
                self.verify_tables()
            else:
                logger.info("Schema already exists; skipping initialization")

            self.ensure_schema_compatibility()
            self.seed_reference_data()
            logger.info("Database initialization completed")
        except DatabaseError:
            logger.error("Database initialization failed")
            raise
