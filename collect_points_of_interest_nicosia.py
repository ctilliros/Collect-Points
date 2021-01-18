import osmnx as ox
import pandas as pd
import psycopg2
import re
import os.path
from os import path
import requests, feedparser
import json  

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

import ssl

# Web scrapping libraries
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

# Get current date 
from datetime import datetime, timedelta
import time
from timeloop import Timeloop

# Import configurations
# from config import * 

date_now = datetime.today()

# Connect to postgres
# conn = psycopg2.connect(host=host, port = postgresport, options='-c statement_timeout=1000', database=database, user=user,password=password)
conn = psycopg2.connect(host='localhost', database='testing', user='postgres', password='9664241907')
cursor = conn.cursor()

'''
Create table 
'''
def create_table():
    sql = 'CREATE TABLE IF NOT EXISTS points_of_interest (\
        id SERIAL NOT NULL,\
        title text COLLATE pg_catalog."default",\
        source integer,\
        category text COLLATE pg_catalog."default",\
        subcategory text COLLATE pg_catalog."default",\
        description text COLLATE pg_catalog."default",\
        latitude double precision,\
        longitude double precision,\
        postalcode integer,\
        date_add date,\
        delete_date date,\
        CONSTRAINT points_of_interest_pkey PRIMARY KEY (id)\
    )'
    cursor.execute(sql,)
    conn.commit()

file = 'nicosia_postcodes_with_population.json'
with open(file,'r') as f:
    global postalcodes 
    postalcodes = json.load(f)     
f.close()   

    
def find_postal_code(latitude, longitude):
    point = (float(latitude),float(longitude))
    #append polygons and postcodes in two different lists
    polygons = []
    postcodes = []
    for i in postalcodes['features']:
        for row, rowvalue in i.items():        
            if row == 'properties':
                post_code = rowvalue['post_code']
                postcodes.append(post_code)
            if row == 'geometry':
                geo = rowvalue['coordinates'][0][0]
                polygons.append(geo)                  
    from shapely.geometry import Point, Polygon, LineString, shape
    for j in range(0,len(polygons)):
        if (Point(point).within(Polygon(polygons[j]))):                    
            return postcodes[j]
    return 0
'''
Find category of subcategory 
'''
def find_category(subcategory):
    if subcategory in art_culture:
        category = 'Art & Culture'   
    if subcategory in family:
        category = 'Family Friendliness'   
    if subcategory in nightlife:
        category = 'Nightlife'   
    if subcategory in goverment:
        category = 'Goverment'   
    if subcategory in environment:
        category = 'Environment'   
    if subcategory in transport:
        category = 'Transport'   
    if subcategory in other:
        category = 'Other'   
    if subcategory in safety:
        category = 'Public Safety'
    if subcategory in health_sports:
        category = 'Health Care & Sport Facilities'
    return category


'''
Find geolocations via webscrapping  
'''
def webscrapping_location(title):
    title_new = title.replace(" ","+")
    url = 'https://www.google.com/search?q='+title_new+"+Λευκωσία"
    options = Options()
    options.headless = True
    response = requests.get(url)
    import subprocess
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    soup=BeautifulSoup(driver.page_source, "html.parser")
    get_link = soup.find_all("div", attrs={"class":"rhsg3 rhsl5 rhsmap4col"})
    print(get_link)
    import re
    if not get_link:
        url = 'https://www.google.com/maps/place/'+title
        driver.get(url)
        soup=BeautifulSoup(driver.page_source,"html.parser")
        get_link = soup.find_all("meta",  property="og:image")
        for link in get_link:
            url = link.get("content", None)    
            locate = re.search('markers=(.*)&sensor', str(url))            
            if not locate:
                lat = 0
                lon = 0 
                driver.close()
                return lat, lon
            else:
                locate = locate.group(1)
                lat = locate.split("%2C")[0]
                lon = locate.split("%2C")[1]
                driver.close()
                return lat, lon        
    else:        
        for links in get_link:
            for tag in links.find_all('a'): 
                data_url = tag['data-url']
                data = re.search('/@(.*),15z', data_url)
                if not data:
                    lat = 0
                    lon = 0
                    driver.close()
                    return(lat, lon)
                else: 
                    data = data.group(1)                            
                    lat = data.split(",")[0]
                    lon = data.split(",")[1]
                    driver.close()
                    return(lat, lon)
                    


health_sports = ['clinic','dentist','doctors','dojo','hospital','pharmacy','toilets','veterinary','drinking_water',
                 'Sports','Pools','community_centre']

art_culture = ['arts_centre','library','place_of_worship','theatre',
               'Cultural centers','Historic schools','Libraries','Museums','Nicosia artists',
               'Picture galleries','Religion','Theatres','monastery']

family = ['atm','bank','bench','bureau_de_change','cafe','childcare','college','fast_food','food_court','ice_cream','internet_cafe',
         'kindergarten','language_school','marketplace','music_school','school','university','vending_machine',
         'social_facility','Education','Markets','Restaurants','Shopping','Sights',
          'Squares','Stay','research_institute','social_centre']

nightlife = ['bar','biergarten','casino','cinema','nightclub','pub','restaurant']

goverment = ['courthouse','embassy','post_office','post_box','prisons','townhall','Government','prison']

environment = ['waste_disposal','recycling','Parks']

transport = ['bicycle_parking','bicycle_rental','bus_station','car_rental','driving_school','fuel','motorcycle_parking',
            'parking','parking_entrance','parking_space','taxi','Bicycles','Parking','Transportations',
            'Walkthroughs','charging_station']

other = ['car_wash','fountain','grave_yard','import','public_building','studio',
         'telephone','other','Social_Space','tv_station']

safety = ['fire_station','police','shelter']

### Loop every 3600 seconds (one hour)
tl = Timeloop()
@tl.job(interval=timedelta(seconds=900))
def sample_job_every_1000s():    
    ''' 
    Get data from osmnx 
    '''
    print(" Start collect data from Openstreetmap ")
    place = "Nicosia, Cyprus"
    tags = {'amenity' : True}
    poi_gdf = ox.geometries_from_place(place, tags, which_result=2)
    poi_gdf = poi_gdf[poi_gdf.name.notnull()]
    poi_gdf.amenity = poi_gdf.amenity.fillna('other')

    dfosmnx = pd.DataFrame(columns={"title","source",'category', "subcategory", "description","latitude", "longitude", "postal_code","date_add"})
    dfopendata = dfosmnx.copy()

    from shapely.geometry import Point
    for key, value in poi_gdf.iterrows():
        if value['geometry'].geom_type == 'Polygon':
            longitude = value['geometry'].centroid.x
            latitude = value['geometry'].centroid.y            
            loc_osmnx = Point([longitude, latitude]) 
        elif value['geometry'].geom_type == 'Point':
            longitude = value['geometry'].x
            latitude = value['geometry'].y
            loc_osmnx = Point([longitude, latitude])  
        title = value['name']

        category = find_category(value['amenity'])

        subcategory = str(value['amenity'])   
        subcategory = re.sub('_', ' ', subcategory).title()
        link = value['website']
        description = value['description']    
        geolocation = value['geometry']
        postal_code = find_postal_code(longitude, latitude)
        source = 1 
        if postal_code:
            sql = 'select * from points_of_interest where title =%s and latitude =%s and longitude=%s and postalcode = %s;'
            cursor.execute(sql,(title, latitude, longitude, postal_code,))
            sql_values = cursor.fetchall()
            conn.commit()
            dfosmnx=dfosmnx.append({"title":title,"source":1,'category':category, "subcategory":subcategory, "description":description,"latitude":latitude, "longitude":longitude, "postal_code":postal_code, "date_add":date_now},ignore_index=True)
            if not sql_values:        
                sql = 'insert into points_of_interest(title, source,category, subcategory, description,latitude, longitude, postalcode, date_add)\
                 values (%s, %s, %s,%s, %s,%s,%s,%s,%s)'
                cursor.execute(sql, (title, source, category, subcategory, description, latitude, longitude, postal_code, date_now,))
                conn.commit()

    ''' 
    Get data from cyprus opendata 
    '''
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
    all_data = 'http://www.nicosia.org.cy/rss/general/?path=/discover/&num=200'
    feed = feedparser.parse(all_data)
    print(" Start collect data from Opendata Cyprus ")
                        
    for post in feed.entries:
        for key,value in post.items():
            if key=='id':
                start = 'discover#'
                end = '#'
                value = value.replace("/","#")
                subcategory = re.search('%s(.*)%s' % (start, end), value).group(1)
                subcategory = re.search('(.*)%s' % (end), subcategory).group(1)            
                if subcategory.replace("-", " "):
                    subcategory = subcategory.replace("-", " ")
                subcategory = subcategory.split('#')[0]
                subcategory = subcategory.capitalize()
                category=find_category(subcategory)
            if key == 'title':
                title = value
            if key == 'link':
                link = value
            if key == 'summary':
                description = value.split('/>')[1]            
            if key == 'geolocation':
                geolocation = value
                if value:
                    latitude = geolocation.split(',')[0]
                    longitude = geolocation.split(',')[1]
                else:
                    latitude, longitude = webscrapping_location(title)
                postal_code = find_postal_code(longitude,latitude)    
            if key == 'tags':
                for i in value:
                    for j, k in i.items():
                        if j == 'term':
                            category = k            
            source = 0
            if postal_code:
                sql = 'select * from points_of_interest where title =%s and latitude =%s and longitude=%s and postalcode = %s;'
                cursor.execute(sql,(title, latitude, longitude, postal_code,))
                sql_values = cursor.fetchall()
                conn.commit()
                if not sql_values and latitude != 0 and longitude != 0:        
                    dfopendata=dfopendata.append({"title":title,"source":0,'category':category, "subcategory":subcategory, "description":description,"latitude":latitude, "longitude":longitude, "postal_code":postal_code,"date_add":date_now},ignore_index=True)
                    sql = 'insert into points_of_interest(title, source,category, subcategory, description,latitude, longitude, postalcode, date_add)\
                     values (%s, %s, %s,%s, %s,%s,%s,%s,%s)'
                    cursor.execute(sql, (title, source, category, subcategory, description, latitude, longitude, postal_code, date_now,))
                    conn.commit()

    sql = 'select * from points_of_interest;'
    df_sql = pd.read_sql(sql, conn)

    df = pd.concat([dfopendata, dfosmnx])
    print("Enosi ton df")
    print(df)
    print("tzino pou to db")
    print(df_sql)
    final_df = pd.merge(df, df_sql, on=['title','title'], how="outer", indicator=True)    
    final_df = final_df[final_df['_merge'] == 'right_only']
    print("To teliko")
    print(final_df)
    if len(final_df):
        final_df = final_df.drop(['id','source_x','subcategory_x','category_x','description_x','latitude_x','longitude_x','date_add_x'], axis=1).reset_index()
        print("erexe ")
        for _, row in final_df.iterrows():
            for key, value in row.items():
                if key == 'title':
                    title = value
                if key == 'longitude_y':
                    lon = value
                if key == 'latitude_y':
                    lat = value    
                    print(lat)
                if key == 'description_y':
                    description = value
                if key == 'source_y':
                    source = value
                if key == 'category_y':
                    category = value
                if key == 'subcategory_y':
                    subcategory = value 
            sql = 'update points_of_interest set delete_date = %s where title =%s and source = %s and category =%s \
            and subcategory = %s and description = %s and latitude = %s and longitude = %s'
            cursor.execute(sql, (date_now, title, source, category, subcategory, description, lat, lon, ))
            conn.commit()

if __name__ == "__main__":        
    create_table()
    tl.start(block=True)