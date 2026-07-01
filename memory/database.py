"""Database setup for VoyageOS memory system."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    """Manage SQLite database for VoyageOS."""

    def __init__(self, db_path: str = "database/voyageos.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize()

    def _initialize(self):
        """Initialize database and create tables if they don't exist."""
        try:
            # Enable WAL mode and set timeout to prevent "database is locked" errors
            self.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            self.conn.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrent access
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
            
            self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            cursor = self.conn.cursor()

            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trip history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trip_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    origin TEXT,
                    destination TEXT,
                    budget REAL,
                    duration INTEGER,
                    travelers INTEGER,
                    trip_type TEXT,
                    weather_json TEXT,
                    transport_json TEXT,
                    hotels_json TEXT,
                    places_json TEXT,
                    budget_json TEXT,
                    generated_itinerary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_session 
                ON conversation_history(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trip_session 
                ON trip_history(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trip_created 
                ON trip_history(created_at DESC)
            """)

            self.conn.commit()
            logger.info("Database tables created/verified")

        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Return database connection."""
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()