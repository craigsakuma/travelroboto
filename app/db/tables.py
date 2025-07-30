"""
SQLAlchemy ORM models for travel itinerary data.

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

# Standard library
import uuid
from datetime import datetime

# Third-party
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    Text,
    Table,
    Index
)
from sqlalchemy.orm import relationship

# Local application
from app.db.base import Base


# ---------------------------------------------------------
# Utility for UUID primary keys
# ---------------------------------------------------------
def generate_uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------
# Association Tables
# ---------------------------------------------------------
traveler_flight = Table(
    "traveler_flight",
    Base.metadata,
    Column("traveler_id", String, ForeignKey("travelers.traveler_id"), primary_key=True),
    Column("flight_id", String, ForeignKey("flights.flight_id"), primary_key=True),
)

traveler_event = Table(
    "traveler_event",
    Base.metadata,
    Column("traveler_id", String, ForeignKey("travelers.traveler_id"), primary_key=True),
    Column("event_id", String, ForeignKey("events.event_id"), primary_key=True),
)

traveler_trip = Table(
    "traveler_trip",
    Base.metadata,
    Column("traveler_id", String, ForeignKey("travelers.traveler_id"), primary_key=True),
    Column("trip_id", String, ForeignKey("trips.trip_id"), primary_key=True),
)

traveler_hotel_reservation = Table(
    "traveler_hotel_reservation",
    Base.metadata,
    Column("traveler_id", String, ForeignKey("travelers.traveler_id"), primary_key=True),
    Column("hotel_reservation_id", String, ForeignKey("hotel_reservations.hotel_reservation_id"), primary_key=True)
)

# ---------------------------------------------------------
# Traveler Table
# ---------------------------------------------------------
class Traveler(Base):
    """
    Represents a traveler including contact information.
    """
    __tablename__ = "travelers"

    traveler_id = Column(String, primary_key=True, default=generate_uuid)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    street_address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)

    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flights = relationship("Flight", secondary=traveler_flight, back_populates="travelers")
    hotel_reservations = relationship("HotelReservation", secondary="traveler_hotel_reservation", back_populates="travelers")
    events = relationship("Event", secondary=traveler_event, back_populates="travelers")
    trips = relationship("Trip", secondary=traveler_trip, back_populates="travelers")

# ---------------------------------------------------------
# Trip Table
# ---------------------------------------------------------
class Trip(Base):
    """
    Represents a vacation trip that can include flights, hotels, and events.
    """
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    travelers = relationship("Traveler", secondary=traveler_trip, back_populates="trips") 
    flights = relationship("Flight", back_populates="trip")  
    events = relationship("Event", back_populates="trip")
    hotel_reservations = relationship("HotelReservation", back_populates="trip")


# ---------------------------------------------------------
# Flight Table
# ---------------------------------------------------------
class Flight(Base):
    """
    Represents flight booking information.
    """
    __tablename__ = "flights"

    flight_id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.trip_id"), nullable=False)
    airline = Column(String(100), nullable=False)
    flight_number = Column(String(20), nullable=False)
    origin_airport_id = Column(String, ForeignKey("airports.airport_id"), nullable=False, index=True)
    destination_airport_id = Column(String, ForeignKey("airports.airport_id"), nullable=False, index=True)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    confirmation_number = Column(String(50), nullable=True)

    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    travelers = relationship("Traveler", secondary=traveler_flight, back_populates="flights")
    trip = relationship("Trip", back_populates="flights")


# ---------------------------------------------------------
# Airport Table
# ---------------------------------------------------------
class Airport(Base):
    """
    Represents an airport, uniquely identified by its IATA code.

    Attributes:
        iata_code (str): 3-letter IATA airport code (e.g., 'SFO', 'LAX').
        name (str): Full airport name (e.g., 'San Francisco International Airport').
        street_address (str): Street address of the airport.
        city (str): City where the airport is located.
        state (str): State or province of the airport.
        country (str): Country of the airport.
    """

    __tablename__ = "airports"

    # IATA code as primary key ensures one row per airport
    airport_id = Column(String, primary_key=True, default=generate_uuid)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    street_address = Column(Text, nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False)


# ---------------------------------------------------------
# Hotel Tables
# ---------------------------------------------------------
class Hotel(Base):
    """
    Represents hotel information.
    """
    __tablename__ = "hotels"

    hotel_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    street_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    website = Column(String(200), nullable=True)

    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    hotel_reservations = relationship("HotelReservation", back_populates="hotel")


class HotelReservation(Base):
    """
    Represents individual hotel reservations.
    """    
    __tablename__ = "hotel_reservations"

    hotel_reservation_id = Column(String, primary_key=True, default=generate_uuid)
    hotel_id = Column(String, ForeignKey("hotels.hotel_id"), nullable=False)
    trip_id = Column(String, ForeignKey("trips.trip_id"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    reservation_number = Column(String(50), nullable=True)

    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    hotel = relationship("Hotel", back_populates="hotel_reservations")
    travelers = relationship("Traveler", secondary="traveler_hotel_reservation", back_populates="hotel_reservations")
    trip = relationship("Trip", back_populates="hotel_reservations")


# ---------------------------------------------------------
# Event Table
# ---------------------------------------------------------
class Event(Base):
    """
    Represents an activity or reservation such as a hike, tour, dinner, or excursion.
    """
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, default=generate_uuid)
    trip_id = Column(String, ForeignKey("trips.trip_id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # e.g., "tour", "boat ride", "dinner"
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    street_address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    reservation_required = Column(Boolean, default=False)
 
    # Slowly Changing Dimensions and Auditing fields
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    travelers = relationship("Traveler", secondary=traveler_event, back_populates="events")
    trip = relationship("Trip", back_populates="events")