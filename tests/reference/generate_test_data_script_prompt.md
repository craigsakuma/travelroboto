# Prompt: Generate Synthetic Travel Database Test Data
version: 1.0
use_case: developer_reference
last_updated: 2025-07-31
author: Your Name
dependencies:
  - ../reference/test_sql_schema.sql
notes:
  - This prompt is for **development use only**.
  - It generates python code to create synthetic CSV datasets based on the SQLite schema in `../reference/test_sql_schema.sql`.
  - Generated data is intended to validate database setup before implementing data pipelines.
  - Data output must match table structures and respect foreign key relationships.

---

## Prompt Content
```prompt
Create sample data in csv format for the following sqlite3 schema. The key challenge is creating a small set of records (minimum of 2 and a maximum of 30 records per table) that share foreign keys across the different tables. Here are some additional guidelines for creating the data: 
- There should be two trips "Banff Aug 2025" and "Honolulu Sept 2025"
- Travelers names (firstname lastname) are: Avi Makadia, Beena Hudka, Manisha Radadia, Kiran Hudka, Arti Bhimani, Craig Sakuma, Utpal Hudka, Rajul Radadia, Anushka Radadia, Jaiden Estime and Devin Estime 
- Events should include examples of typical vacation events like hikes, dinners, boat rides, snorkeling, rock climbing, scenic drive
- Hotels could airbnb or traditional hotel
- Exclude null values in sample data set
- Create separate csv files and the file names should be the tablename with _test_data.csv (for example the travelers table should be named travelers_test_data.csv. But I also want you to expand some of the sample datasets:
- Every traveler will have at least 1 trip and 2 travelers will be on both trips
- For each unique traveler and trip combo, a traveler should have a departing and returning flight
- Banff should have 15 events and honolulu should have 5 events
- Each traveler should have at least one hotel reservation and the total duration of all hotel reservations should cover the entire trip duration
- Every traveler should have a random number of events between 4 and 10
- All travelers live in one of the following cities: Los Angeles, San Francisco, Princeton 
- Use the following airports for flights: LAX, SFO, EWR, YYC, HNL
- Banff trip begins 2025/08/02 and ends 2025/08/10
- Remove the Amelia Island trip and replace it with "Honolulu Sept 2025"
- Devin, Jaiden and Arti live in Los Angeles
- All other travelers live in Princeton
- Everyone will be on the Banff trip and only Kiran and craig will be on both trips
- The first and last night of the banff trip will be at the Westin Calgary
- The second hotel for banff will be an airbnb in Canmore
- The third hotel in banff will be at an airbnb in Hinton
- Craig and Kiran are the only two people that live in SF
- id fields should be created deterministically
- for event assignment use a randomized matching
```