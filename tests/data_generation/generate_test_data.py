"""
TripBot Sample Data Generator

Used prompt to generate python code for testing.
Creates DataFrames for each table in the database schema.
Exports DataFrames as csv files in the designate path for test data 
"""


import pandas as pd
import random
import io, zipfile

from app.config import TEST_DATA_DIR

# Ensure the directory exists
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

# -------------------
# Travelers
# -------------------
travelers = [
    ("T1","Avi","Makadia","Princeton"),
    ("T2","Beena","Hudka","Princeton"),
    ("T3","Manisha","Radadia","Princeton"),
    ("T4","Kiran","Hudka","San Francisco"),
    ("T5","Arti","Bhimani","Los Angeles"),
    ("T6","Craig","Sakuma","San Francisco"),
    ("T7","Utpal","Hudka","Princeton"),
    ("T8","Rajul","Radadia","Princeton"),
    ("T9","Anushka","Radadia","Princeton"),
    ("T10","Jaiden","Estime","Los Angeles"),
    ("T11","Devin","Estime","Los Angeles"),
]
df_travelers = pd.DataFrame([{
    "traveler_id": t[0],
    "first_name": t[1],
    "last_name": t[2],
    "email": f"{t[1].lower()}.{t[2].lower()}@example.com",
    "phone_number": f"555-{1000+i}",
    "street_address": f"{100+i} Main St",
    "city": t[3],
    "state": "CA" if t[3] in ["Los Angeles","San Francisco"] else "NJ",
    "effective_from": "2025-01-01T00:00:00",
    "is_active": 1,
    "created_at": "2025-01-01T00:00:00",
    "last_updated_at": "2025-01-01T00:00:00"
} for i,t in enumerate(travelers)])

# -------------------
# Trips
# -------------------
trips = [
    ("TRIP1","Banff Aug 2025","Family vacation to Banff","2025-08-02","2025-08-10"),
    ("TRIP2","Honolulu Sept 2025","Beach trip to Honolulu","2025-09-05","2025-09-12")
]
df_trips = pd.DataFrame([{
    "trip_id": t[0],
    "name": t[1],
    "description": t[2],
    "start_date": t[3],
    "end_date": t[4],
    "effective_from": "2025-01-01T00:00:00",
    "is_active": 1,
    "created_at": "2025-01-01T00:00:00",
    "last_updated_at": "2025-01-01T00:00:00"
} for t in trips])

# -------------------
# Airports
# -------------------
airports = [
    ("A1","LAX","Los Angeles Intl","Los Angeles","CA","USA"),
    ("A2","SFO","San Francisco Intl","San Francisco","CA","USA"),
    ("A3","EWR","Newark Liberty Intl","Newark","NJ","USA"),
    ("A4","YYC","Calgary Intl","Calgary","AB","Canada"),
    ("A5","HNL","Honolulu Intl","Honolulu","HI","USA")
]
df_airports = pd.DataFrame([{
    "airport_id": a[0],
    "iata_code": a[1],
    "name": a[2],
    "street_address": f"{a[2]} Road",
    "city": a[3],
    "state": a[4],
    "country": a[5]
} for a in airports])

# -------------------
# Hotels (4)
# -------------------
hotels = [
    ("H1","Westin Calgary","320 4 Ave SW","Calgary","AB","Canada","https://westin.com/calgary"),
    ("H2","Airbnb Canmore","120 Mountain St","Canmore","AB","Canada","https://airbnb.com/canmore"),
    ("H3","Airbnb Hinton","98 Pine Ave","Hinton","AB","Canada","https://airbnb.com/hinton"),
    ("H4","Hilton Hawaiian Village","2005 Kalia Rd","Honolulu","HI","USA","https://hilton.com/hhv")
]
df_hotels = pd.DataFrame([{
    "hotel_id": h[0],
    "name": h[1],
    "street_address": h[2],
    "city": h[3],
    "state": h[4],
    "country": h[5],
    "phone": f"555-{3000+i}",
    "website": h[6],
    "effective_from": "2025-01-01T00:00:00",
    "is_active": 1,
    "created_at": "2025-01-01T00:00:00",
    "last_updated_at": "2025-01-01T00:00:00"
} for i,h in enumerate(hotels)])

# -------------------
# Events (Banff 15, Honolulu 5)
# -------------------
banff_events = [
    "Lake Louise Hike","Johnston Canyon Hike","Moraine Lake Canoe","Sulphur Mountain Gondola",
    "Banff Upper Hot Springs","Peyto Lake Overlook","Icefields Parkway Scenic Drive","Banff Wildlife Tour",
    "Cave and Basin Tour","Bow Falls Walk","Lake Minnewanka Cruise","Horseback Riding Tour","Yoho National Park Visit",
    "Takakkaw Falls Hike","Emerald Lake Canoe"
]
honolulu_events = [
    "Waikiki Beach Surfing","Diamond Head Hike","Pearl Harbor Tour","Snorkeling at Hanauma Bay","Luau Dinner"
]
event_rows = []
eid=1
for name in banff_events:
    event_rows.append({"event_id":f"E{eid}","trip_id":"TRIP1","name":name,"description":f"{name} experience",
                       "category":"Activity","date":f"2025-08-{(2+eid)%10+1:02d}","start_time":"09:00","end_time":"12:00",
                       "duration_minutes":180,"street_address":"Various","city":"Banff","state":"AB",
                       "url":"https://banff.com","reservation_required":0,"effective_from":"2025-01-01T00:00:00",
                       "is_active":1,"created_at":"2025-01-01T00:00:00","last_updated_at":"2025-01-01T00:00:00"})
    eid+=1
for name in honolulu_events:
    event_rows.append({"event_id":f"E{eid}","trip_id":"TRIP2","name":name,"description":f"{name} experience",
                       "category":"Activity","date":f"2025-09-{(5+eid)%12+1:02d}","start_time":"09:00","end_time":"12:00",
                       "duration_minutes":180,"street_address":"Various","city":"Honolulu","state":"HI",
                       "url":"https://honolulu.com","reservation_required":0,"effective_from":"2025-01-01T00:00:00",
                       "is_active":1,"created_at":"2025-01-01T00:00:00","last_updated_at":"2025-01-01T00:00:00"})
    eid+=1
df_events = pd.DataFrame(event_rows)

# -------------------
# Traveler-Trip (everyone on Banff, Craig & Kiran on Honolulu)
# -------------------
traveler_trip = [{"traveler_id":tid,"trip_id":"TRIP1"} for tid in df_travelers["traveler_id"]] + \
                [{"traveler_id":"T4","trip_id":"TRIP2"},{"traveler_id":"T6","trip_id":"TRIP2"}]
df_traveler_trip = pd.DataFrame(traveler_trip)

# -------------------
# Flights (depart & return per traveler-trip)
# -------------------
city_airport = {"Los Angeles":"A1","San Francisco":"A2","Princeton":"A3"}
flight_rows, traveler_flight_rows = [], []
fid=1
for _,row in df_traveler_trip.iterrows():
    tid, trip = row["traveler_id"], row["trip_id"]
    origin = city_airport[df_travelers.loc[df_travelers["traveler_id"]==tid,"city"].values[0]]
    dest = "A4" if trip=="TRIP1" else "A5"
    depart = "2025-08-02" if trip=="TRIP1" else "2025-09-05"
    ret = "2025-08-10" if trip=="TRIP1" else "2025-09-12"
    # departure flight
    flight_rows.append({"flight_id":f"F{fid}","trip_id":trip,"airline":"United","flight_number":f"UA{100+fid}",
                        "origin_airport_id":origin,"destination_airport_id":dest,"departure_time":f"{depart}T08:00:00",
                        "arrival_time":f"{depart}T12:00:00","confirmation_number":f"CN{1000+fid}",
                        "effective_from":"2025-01-01T00:00:00","is_active":1,
                        "created_at":"2025-01-01T00:00:00","last_updated_at":"2025-01-01T00:00:00"})
    traveler_flight_rows.append({"traveler_id":tid,"flight_id":f"F{fid}"})
    fid+=1
    # return flight
    flight_rows.append({"flight_id":f"F{fid}","trip_id":trip,"airline":"United","flight_number":f"UA{100+fid}",
                        "origin_airport_id":dest,"destination_airport_id":origin,"departure_time":f"{ret}T12:00:00",
                        "arrival_time":f"{ret}T18:00:00","confirmation_number":f"CN{1000+fid}",
                        "effective_from":"2025-01-01T00:00:00","is_active":1,
                        "created_at":"2025-01-01T00:00:00","last_updated_at":"2025-01-01T00:00:00"})
    traveler_flight_rows.append({"traveler_id":tid,"flight_id":f"F{fid}"})
    fid+=1
df_flights = pd.DataFrame(flight_rows)
df_traveler_flight = pd.DataFrame(traveler_flight_rows)

# -------------------
# Hotel Reservations (Banff split + Honolulu single)
# -------------------
hotel_res = [
    ("HR1","H1","TRIP1","2025-08-02","2025-08-03"),
    ("HR2","H2","TRIP1","2025-08-03","2025-08-07"),
    ("HR3","H3","TRIP1","2025-08-07","2025-08-09"),
    ("HR4","H1","TRIP1","2025-08-09","2025-08-10"),
    ("HR5","H4","TRIP2","2025-09-05","2025-09-12")
]
df_hotel_reservations = pd.DataFrame([{
    "hotel_reservation_id":r[0],"hotel_id":r[1],"trip_id":r[2],"check_in":r[3],"check_out":r[4],
    "reservation_number":f"RN{1000+i}","effective_from":"2025-01-01T00:00:00",
    "is_active":1,"created_at":"2025-01-01T00:00:00","last_updated_at":"2025-01-01T00:00:00"
} for i,r in enumerate(hotel_res)])

traveler_hotel = []
for hrid,trip in [("HR1","TRIP1"),("HR2","TRIP1"),("HR3","TRIP1"),("HR4","TRIP1")]:
    for tid in df_travelers["traveler_id"]:
        traveler_hotel.append({"traveler_id":tid,"hotel_reservation_id":hrid})
# Honolulu hotel only Craig & Kiran
for tid in ["T4","T6"]:
    traveler_hotel.append({"traveler_id":tid,"hotel_reservation_id":"HR5"})
df_traveler_hotel = pd.DataFrame(traveler_hotel)

# -------------------
# Traveler-Event (4-10 random per traveler)
# -------------------
traveler_event = []
for tid, trips_for_trav in df_traveler_trip.groupby("traveler_id")["trip_id"]:
    for trip in trips_for_trav:
        events = df_events[df_events["trip_id"]==trip]["event_id"].tolist()
        n = random.randint(4,min(10,len(events)))
        for e in random.sample(events,n):
            traveler_event.append({"traveler_id":tid,"event_id":e})
df_traveler_event = pd.DataFrame(traveler_event)

# -------------------
# CSV creation
# -------------------
# Save each DataFrame as CSV in TEST_DATA_DIR
# Dictionary mapping filenames to DataFrames
dataframes = {
    "travelers_test_data.csv": df_travelers,
    "trips_test_data.csv": df_trips,
    "airports_test_data.csv": df_airports,
    "hotels_test_data.csv": df_hotels,
    "hotel_reservations_test_data.csv": df_hotel_reservations,
    "events_test_data.csv": df_events,
    "flights_test_data.csv": df_flights,
    "traveler_trip_test_data.csv": df_traveler_trip,
    "traveler_flight_test_data.csv": df_traveler_flight,
    "traveler_event_test_data.csv": df_traveler_event,
    "traveler_hotel_reservation_test_data.csv": df_traveler_hotel,
}

# Save each DataFrame as CSV
for filename, df in dataframes.items():
    output_path = TEST_DATA_DIR / filename
    df.to_csv(output_path, index=False)
    print(f"Saved {output_path}")

