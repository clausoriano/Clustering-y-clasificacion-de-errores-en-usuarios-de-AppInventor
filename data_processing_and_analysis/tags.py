# creamos la conexion con la BD
import json

import pymysql
from collections import Counter
import os
import time
import openai
import tiktoken

import config

conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

# Guarda los tags en la tabla tags de la BD
def get_tags():
    query = "SELECT DISTINCT tags FROM questions WHERE site = 1"
    cursor.execute(query)
    tags = cursor.fetchall()
    tags_string = ""
    for tag in tags:
        tags_string = tags_string +","+(tag[0])
    tags_array = tags_string.split(",")
    tags_list = []
    for tag in tags_array:
        if tag not in tags_list:
            tags_list.append(tag)

    for tag in tags_list:
        query = "INSERT INTO tags(name) values (%s);"
        params = [tag]
        print("Insertado tag: " + tag)
        cursor.execute(query,params)
        conn.commit()

#Cuenta el uso de cada tag en cada categoría
def tags_per_cat(cat):
    query = "SELECT DISTINCT tags FROM questions WHERE site = 1 AND about = %s"
    params = [cat]
    cursor.execute(query,params)
    tags = cursor.fetchall()
    tags_string = ""
    for tag in tags:
        tags_string = tags_string +","+(tag[0])
    tags_array = tags_string.split(",")
    tags_list = []
    for tag in tags_array:
        tags_list.append(tag)

    counts = Counter(tags_list)
    counts = counts.most_common()

    query = "UPDATE categories SET tags = %s WHERE ID = %s"
    params = [str(counts),cat]
    cursor.execute(query,params)
    conn.commit()


# Genera la descripcion de los tags mediante chatgpt
def get_tags_description_gpt():
    # creamos la conexion con la API
    openai.api_key = config.api_key


    query = "SELECT name FROM tags WHERE description =''"
    cursor.execute(query)
    tags = cursor.fetchall()

    for tag in tags:
        # tarea para chatGPT
        duty_explanation = '''Give a short description to this tag in a programming context: ''' + tag[0]
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", temperature=0,
            messages=[
                {"role": "user", "content": duty_explanation},
            ]
        )

        solution = completion.choices[0].message.content

        query = "UPDATE tags SET description = %s WHERE name = %s"
        params = [solution,tag[0]]
        cursor.execute(query,params)
        conn.commit()

        # esperamos el timeout de la api
        time.sleep(20)


# Calcula y guarda los sentimientos por tag
def get_tags_sentiments():
    query = "SELECT name from tags where neutral = 0"
    cursor.execute(query)
    tags = cursor.fetchall()

    # seleccionamos para cada tag los sentimientos de las preguntas que contienen dicho tag
    for tag in tags:
        query = "SELECT sentiments,link FROM questions WHERE tags LIKE %s AND sentiments !=''"
        tag_sql = '%'+tag[0]+'%'
        params = [tag_sql]
        cursor.execute(query,params)
        sentiments = cursor.fetchall()

        anger = 0
        disgust = 0
        fear = 0
        joy = 0
        neutral = 0
        sadness = 0
        surprise = 0
        lenght = len(sentiments)
        if lenght == 0:
            lenght = 1

        # calculamos la media de sentimientos de las preguntas que contienen dicho tag
        for sentiment in sentiments:
            sentiment = sentiment[0].split(",")
            anger = anger + float(sentiment[0].split(":")[1])
            disgust = disgust + float(sentiment[1].split(":")[1])
            fear = fear + float(sentiment[2].split(":")[1])
            joy = joy + float(sentiment[3].split(":")[1])
            neutral = neutral + float(sentiment[4].split(":")[1])
            sadness = sadness + float(sentiment[5].split(":")[1])
            surprise = surprise + float(sentiment[6].split(":")[1])

        anger = round((anger / lenght) * 100, 1)
        disgust = round((disgust / lenght) * 100, 1)
        fear = round((fear / lenght) * 100, 1)
        joy = round((joy / lenght) * 100, 1)
        neutral = round((neutral / lenght) * 100, 1)
        sadness = round((sadness / lenght) * 100, 1)
        surprise = round((surprise / lenght) * 100, 1)


        query = "UPDATE tags SET anger = %s, disgust = %s, fear = %s, joy = %s, neutral = %s, sadness = %s, surprise = %s WHERE name = %s"
        params = [anger,disgust,fear,joy,neutral,sadness,surprise,tag[0]]
        cursor.execute(query,params)
        conn.commit()
        print("Tag: " + tag[0])
        print('anger: '+str(anger)+' disgust: '+str(disgust)+' fear: '+str(fear)+' joy: '+str(joy)+' neutral: '+str(neutral)+' sadness: '+str(sadness)+' surprise: '+str(surprise))
        print('----------------------------------------------------------')

# Funcion que carga todas la preguntas sin tags a la tabla ai_tags
def load_unttaged_questions():
    query = "SELECT link,text FROM questions WHERE tags =''"
    cursor.execute(query)
    untagged_questions = cursor.fetchall()

    for question in untagged_questions:
        query = "INSERT INTO ai_tags(question_id) VALUES (%s)"
        params = [question[0]]
        cursor.execute(query,params)
        conn.commit()

# Funcion que elige mediante chat gpt los tags recomendados para las preguntas
def get_recommended_tags_gpt():

    openai.api_key = config.api_key

    query = "SELECT link,text FROM questions WHERE tags =''"
    cursor.execute(query)
    untagged_questions = cursor.fetchall()

    query = "SELECT name,description FROM tags"
    cursor.execute(query)
    tags = cursor.fetchall()

    tag_list = []
    for tag in tags:
        tag_list.append(tag[0])

    for question in untagged_questions:

        query = "SELECT suggested_tags FROM ai_tags WHERE question_id = %s"
        params = [question[0]]
        cursor.execute(query,params)
        data = cursor.fetchall()
        if data[0][0] == '':
            duty_explanation = "This is a list of tags: " + str(tag_list) + ". What of those tags included on the list would you assign to the following text: " + question[1]
            final_instruction = "Provide the answer in json format"
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", temperature=0,
                messages=[
                    {"role": "user", "content": duty_explanation},
                    {"role": "user", "content": final_instruction},
                ]
            )
            solution = completion.choices[0].message.content
            solution = json.loads(solution)
            suggested_tags = str(solution['tags'])

            query = "UPDATE ai_tags SET suggested_tags = %s WHERE question_id = %s"
            params = [suggested_tags,question[0]]
            cursor.execute(query,params)
            conn.commit()

            print("------------------------------------------------")
            print("Question: " + question[0] + ". Tags: " + suggested_tags)
            print("------------------------------------------------")
            time.sleep(20)
        else:
            print("------------------------------------------------")
            print("Question: " + question[0] + " is already tagged.")
            print("------------------------------------------------")




def process():
    get_tags()
    load_unttaged_questions()
    get_recommended_tags_gpt()
    cats = [5, 20, 11, 17, 10, 19, 12, 18, 14, 24, 3, 21, 13, 27, 7, 9, 16, 29, 28]
    for cat in cats:
        tags_per_cat(cat)
    get_tags_sentiments()
    get_tags_description_gpt()


