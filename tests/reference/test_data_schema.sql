CREATE TABLE travelers (
	traveler_id VARCHAR NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	email VARCHAR(100), 
	phone_number VARCHAR(20), 
	street_address TEXT, 
	city TEXT, 
	state TEXT, 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (traveler_id)
);
CREATE TABLE trips (
	trip_id VARCHAR NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	start_date DATETIME NOT NULL, 
	end_date DATETIME NOT NULL, 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (trip_id)
);
CREATE TABLE airports (
	airport_id VARCHAR NOT NULL, 
	iata_code VARCHAR(3) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	street_address TEXT, 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100), 
	country VARCHAR(100) NOT NULL, 
	PRIMARY KEY (airport_id)
);
CREATE UNIQUE INDEX ix_airports_iata_code ON airports (iata_code);
CREATE TABLE hotels (
	hotel_id VARCHAR NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	street_address TEXT NOT NULL, 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100), 
	country VARCHAR(100) NOT NULL, 
	phone VARCHAR(20), 
	website VARCHAR(200), 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (hotel_id)
);
CREATE TABLE traveler_trip (
	traveler_id VARCHAR NOT NULL, 
	trip_id VARCHAR NOT NULL, 
	PRIMARY KEY (traveler_id, trip_id), 
	FOREIGN KEY(traveler_id) REFERENCES travelers (traveler_id), 
	FOREIGN KEY(trip_id) REFERENCES trips (trip_id)
);
CREATE TABLE flights (
	flight_id VARCHAR NOT NULL, 
	trip_id VARCHAR NOT NULL, 
	airline VARCHAR(100) NOT NULL, 
	flight_number VARCHAR(20) NOT NULL, 
	origin_airport_id VARCHAR NOT NULL, 
	destination_airport_id VARCHAR NOT NULL, 
	departure_time DATETIME NOT NULL, 
	arrival_time DATETIME NOT NULL, 
	confirmation_number VARCHAR(50), 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (flight_id), 
	FOREIGN KEY(trip_id) REFERENCES trips (trip_id), 
	FOREIGN KEY(origin_airport_id) REFERENCES airports (airport_id), 
	FOREIGN KEY(destination_airport_id) REFERENCES airports (airport_id)
);
CREATE INDEX ix_flights_origin_airport_id ON flights (origin_airport_id);
CREATE INDEX ix_flights_destination_airport_id ON flights (destination_airport_id);
CREATE TABLE hotel_reservations (
	hotel_reservation_id VARCHAR NOT NULL, 
	hotel_id VARCHAR NOT NULL, 
	trip_id VARCHAR NOT NULL, 
	check_in DATETIME NOT NULL, 
	check_out DATETIME NOT NULL, 
	reservation_number VARCHAR(50), 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (hotel_reservation_id), 
	FOREIGN KEY(hotel_id) REFERENCES hotels (hotel_id), 
	FOREIGN KEY(trip_id) REFERENCES trips (trip_id)
);
CREATE TABLE events (
	event_id VARCHAR NOT NULL, 
	trip_id VARCHAR NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	category VARCHAR(50) NOT NULL, 
	date DATETIME NOT NULL, 
	start_time DATETIME, 
	end_time DATETIME, 
	duration_minutes INTEGER, 
	street_address TEXT, 
	city TEXT, 
	state TEXT, 
	url VARCHAR(500), 
	reservation_required BOOLEAN, 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME NOT NULL, 
	last_updated_at DATETIME NOT NULL, 
	PRIMARY KEY (event_id), 
	FOREIGN KEY(trip_id) REFERENCES trips (trip_id)
);
CREATE TABLE traveler_flight (
	traveler_id VARCHAR NOT NULL, 
	flight_id VARCHAR NOT NULL, 
	PRIMARY KEY (traveler_id, flight_id), 
	FOREIGN KEY(traveler_id) REFERENCES travelers (traveler_id), 
	FOREIGN KEY(flight_id) REFERENCES flights (flight_id)
);
CREATE TABLE traveler_event (
	traveler_id VARCHAR NOT NULL, 
	event_id VARCHAR NOT NULL, 
	PRIMARY KEY (traveler_id, event_id), 
	FOREIGN KEY(traveler_id) REFERENCES travelers (traveler_id), 
	FOREIGN KEY(event_id) REFERENCES events (event_id)
);
CREATE TABLE traveler_hotel_reservation (
	traveler_id VARCHAR NOT NULL, 
	hotel_reservation_id VARCHAR NOT NULL, 
	PRIMARY KEY (traveler_id, hotel_reservation_id), 
	FOREIGN KEY(traveler_id) REFERENCES travelers (traveler_id), 
	FOREIGN KEY(hotel_reservation_id) REFERENCES hotel_reservations (hotel_reservation_id)
);
