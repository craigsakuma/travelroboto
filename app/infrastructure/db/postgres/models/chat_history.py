"""
SQLAlchemy ORM models for chat history.

Includes:
- Travelers
- Trips
- Flights
- Hotels and Hotel Reservations
- Events (e.g., tours, meals, excursions)
- Association tables for many-to-many relationships
- Slowly Changing Dimensions (SCD) and auditing fields for historical tracking

Supports:
- Multiple travelers sharing trips, flights, hotels, and events
- Versioning of records when itinerary details change
- Portability (SQLite → PostgreSQL)
"""

# Third-party
from sqlalchemy import Column, Integer, String, DateTime, func, Index

# Local application
from app.db.base import Base


class ChatMessage(Base):
    """
    Table for storing chatbot message history.

    Attributes:
        id (int): Auto-incrementing primary key (PostgreSQL identity).
        session_id (str): Identifier for a unique chat session.
        role (str): Role of the message sender (e.g., 'human', 'ai').
        content (str): Text content of the message.
        timestamp (datetime): UTC timestamp when the message was created.
    """
    __tablename__ = "chat_messages"
    
    msg_id = Column(Integer, primary_key=True, index=True)  # Postgresql autoincrements as serial
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add compound index for common query pattern: filter by session and order by timestamp
    __table_args__ = (
        Index("idx_chat_session_timestamp", "session_id", "timestamp"),
    )
