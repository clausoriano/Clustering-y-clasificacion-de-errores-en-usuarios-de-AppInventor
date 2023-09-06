import json
import os
import time
import openai
import pymysql
import tiktoken
import config

# creamos la conexion con la API
openai.api_key = config.api_key
# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()


def load_locations():
    query = "SELECT DISTINCT location from users where location !=''"
    cursor.execute(query)
    locations = cursor.fetchall()

    for location in locations:
        query = "INSERT INTO locations(name) VALUES (%s)"
        params = [location[0]]
        cursor.execute(query, params)
        conn.commit()
        print("Insertado: " + location[0])


def get_coordinates_gpt():
    query = "SELECT name FROM locations WHERE latitude = 0 AND longitude = 0"
    cursor.execute(query)
    locations = cursor.fetchall()

    for location in locations:
        # explicacion tarea para chatGPT
        duty_explanation = '''What is the latitude and longitude of ''' + location[0] + ''' ? Answer in json format '''
        final_instruction = '''Please provide latitude and longitude in json format.'''

        # tarea y llamada a la api de chatGPT, por cada pregunta hacemos llamada a la api
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", temperature=0,
            messages=[
                {"role": "user", "content": duty_explanation},
                {"role": "user", "content": final_instruction}
            ]
        )
        print("The location is: " + location[0])
        solution = completion.choices[0].message.content

        json_object = json.loads(solution)
        latitude = json_object['latitude']
        longitude = json_object['longitude']

        print("Latitude: " + str(latitude) + ", Longitude: " + str(longitude))

        # guardamos la respuesta en la BBDD
        query = "UPDATE locations SET latitude = %s, longitude = %s WHERE name = %s"
        params = [latitude,longitude,location[0]]
        cursor.execute(query,params)
        conn.commit()

        time.sleep(20)

def coords_to_users():
    query = "SELECT name,latitude,longitude FROM locations"
    cursor.execute(query)
    locations = cursor.fetchall()

    for location in locations:
        query = "UPDATE users SET latitude = %s, longitude = %s WHERE location = %s"
        params = [location[1],location[2],location[0]]
        cursor.execute(query,params)
        conn.commit()


def main():
    load_locations()
    get_coordinates_gpt()
    coords_to_users()
