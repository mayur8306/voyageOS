"""Conversation and trip history management for VoyageOS."""

import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from memory.database import Database

logger = logging.getLogger(__name__)


class ConversationHistory:
    """Manage conversation history in SQLite."""

    def __init__(self, database: Database):
        """
        Initialize conversation history.
        
        Args:
            database: Database instance
        """
        self.db = database

    def add_message(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> bool:
        """
        Add a conversation message pair to history.
        
        Args:
            session_id: Unique session identifier
            user_message: User's message
            assistant_message: Assistant's response
            
        Returns:
            True if successful, False otherwise
        """
        cursor = None
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                """
                INSERT INTO conversation_history 
                (session_id, user_message, assistant_message, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, user_message, assistant_message, datetime.now())
            )
            self.db.get_connection().commit()
            logger.debug(f"Saved conversation for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                """
                SELECT user_message, assistant_message, timestamp
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (session_id, limit)
            )

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'user_message': row['user_message'],
                    'assistant_message': row['assistant_message'],
                    'timestamp': row['timestamp']
                })

            return messages

        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return []

    def get_recent_sessions(self, limit: int = 20) -> List[Dict]:
        """
        Get recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                """
                SELECT DISTINCT session_id, 
                       MAX(timestamp) as last_activity,
                       COUNT(*) as message_count
                FROM conversation_history
                GROUP BY session_id
                ORDER BY last_activity DESC
                LIMIT ?
                """,
                (limit,)
            )

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row['session_id'],
                    'last_activity': row['last_activity'],
                    'message_count': row['message_count']
                })

            return sessions

        except Exception as e:
            logger.error(f"Failed to get recent sessions: {str(e)}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete all messages for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        cursor = None
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                "DELETE FROM conversation_history WHERE session_id = ?",
                (session_id,)
            )
            self.db.get_connection().commit()
            logger.info(f"Deleted session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()

    def clear_all_history(self) -> bool:
        """
        Clear all conversation history.
        
        Returns:
            True if successful, False otherwise
        """
        cursor = None
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("DELETE FROM conversation_history")
            self.db.get_connection().commit()
            logger.info("Cleared all conversation history")
            return True

        except Exception as e:
            logger.error(f"Failed to clear history: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()


class TripHistory:
    """Manage trip history in SQLite."""

    def __init__(self, database: Database):
        """
        Initialize trip history.
        
        Args:
            database: Database instance
        """
        self.db = database

    def save_trip(
        self,
        session_id: str,
        trip_data: Dict,
        itinerary: str
    ) -> bool:
        """
        Save a trip to history.
        
        Args:
            session_id: Session identifier
            trip_data: Dictionary with trip details
            itinerary: Generated itinerary text
            
        Returns:
            True if successful, False otherwise
        """
        cursor = None
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                """
                INSERT INTO trip_history 
                (session_id, origin, destination, budget, duration, travelers,
                 trip_type, weather_json, transport_json, hotels_json,
                 places_json, budget_json, generated_itinerary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    trip_data.get('origin'),
                    trip_data.get('destination'),
                    trip_data.get('budget'),
                    trip_data.get('duration'),
                    trip_data.get('travelers'),
                    trip_data.get('trip_type'),
                    json.dumps(trip_data.get('weather', {})),
                    json.dumps(trip_data.get('transport', {})),
                    json.dumps(trip_data.get('hotels', [])),
                    json.dumps(trip_data.get('places', [])),
                    json.dumps(trip_data.get('budget', {})),
                    itinerary
                )
            )
            self.db.get_connection().commit()
            logger.info(f"Saved trip for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save trip: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_session_trips(self, session_id: str) -> List[Dict]:
        """
        Get all trips for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of trip dictionaries
        """
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                """
                SELECT * FROM trip_history
                WHERE session_id = ?
                ORDER BY created_at DESC
                """,
                (session_id,)
            )

            trips = []
            for row in cursor.fetchall():
                trips.append({
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'origin': row['origin'],
                    'destination': row['destination'],
                    'budget': row['budget'],
                    'duration': row['duration'],
                    'travelers': row['travelers'],
                    'trip_type': row['trip_type'],
                    'weather': json.loads(row['weather_json']) if row['weather_json'] else {},
                    'transport': json.loads(row['transport_json']) if row['transport_json'] else {},
                    'hotels': json.loads(row['hotels_json']) if row['hotels_json'] else [],
                    'places': json.loads(row['places_json']) if row['places_json'] else [],
                    'budget': json.loads(row['budget_json']) if row['budget_json'] else {},
                    'itinerary': row['generated_itinerary'],
                    'created_at': row['created_at']
                })

            return trips

        except Exception as e:
            logger.error(f"Failed to get session trips: {str(e)}")
            return []

    def get_latest_trip(self, session_id: str) -> Optional[Dict]:
        """
        Get the most recent trip for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Trip dictionary or None
        """
        trips = self.get_session_trips(session_id)
        return trips[0] if trips else None

    def delete_trip(self, trip_id: int) -> bool:
        """
        Delete a trip by ID.
        
        Args:
            trip_id: Trip ID
            
        Returns:
            True if successful, False otherwise
        """
        cursor = None
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                "DELETE FROM trip_history WHERE id = ?",
                (trip_id,)
            )
            self.db.get_connection().commit()
            logger.info(f"Deleted trip {trip_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete trip: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
