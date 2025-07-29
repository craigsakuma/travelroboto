"""
Pydantic data models used for parsing and validating structured travel information
extracted from travel-related data sources (e.g., airline confirmation emails).

These models are designed to:
- Provide strong type validation for travel data.
- Be compatible with LangChain's PydanticOutputParser for converting
  unstructured text (e.g., airline emails) into structured Python objects.

The models in this file are focused on data interchange and validation only.
They are **not** tied to any database schema (those belong in SQLModel or ORM models).

Models Included:
---------------
1. Passenger:
   - Represents a traveler in the itinerary.
   - Includes basic name information.

2. FlightDetails:
   - Represents an individual flight in an itinerary.
   - Includes airline, flight number, departure/arrival details, and passenger list.

3. FlightManifest:
   - Represents a full set of one or more flights associated with an itinerary.
   - Designed to encapsulate multiple passengers and multiple flights in one structure.

Usage Example:
--------------
>>> from app.models import FlightManifest
>>> manifest = FlightManifest(
...     flights=[
...         {
...             "flight_number": "DL123",
...             "airline_name": "Delta",
...             "departure_date": "2025-08-01",
...             "departure_time": "10:30:00",
...             "arrival_date": "2025-08-01T16:00:00",
...             "arrival_time": "16:00:00",
...             "origin": "SFO",
...             "destination": "JFK",
...             "passengers": [{"first_name": "Alice", "last_name": "Smith"}]
...         }
...     ]
... )
>>> manifest.flights[0].origin
'SFO'
"""

from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel

class Passenger(BaseModel):
    """Represents a passenger in a flight itinerary."""
    first_name: str
    last_name: str

class FlightDetails(BaseModel):
    """Represents the details of an individual flight."""
    flight_number: str
    airline_name: str
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[time] = None
    origin: str
    destination: str
    passengers: List[Passenger]

class FlightManifest(BaseModel):
    """Represents the overall manifest containing one or more flights."""
    flights: List[FlightDetails]