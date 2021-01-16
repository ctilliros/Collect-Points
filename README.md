# Collect-Points

This script collects data for Nicosia Municipallity.

The main sources are:
Open Data of Cyprus Government 
OSMNx (OpenStreetMap Python library) 

# Main Idea

The script runs every month and recollect the data, with main purpose the update of exists, which points were closed. 

# Solution

Collect data from OSMNx and Open Data from Cyprus and check if the data is in the database. If yes, then get next data, else insert in the database. 

For OSMNx:
- Get the amenities from the library and insert to database.
- Add data to OSMNx DataFrame.

For OpenData:
- Get data from API.
- If data do not have geolocation, then get data via Google or Google Maps using Web Scrapping with Selenium.
- Add data to OpenData DataFrame.

Merge the two dataframes. 

Then query my database, and parse data to another one DataFrame. 

Create OuterJoin between the two final dataframes. The last values are the Points which were closed. 

# Libraries:
* psycopg2
* osmnx
* pandas
* feedparser
* selenium
* timeloop
* beautifulsoup4


