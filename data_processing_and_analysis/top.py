from collections import Counter
import config
import pymysql

# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

#Funcion que devuelve el top 10 de preguntas mas vistas por categoría
def top_cat(cat):
    query = "SELECT link,title,text,views FROM questions WHERE about = %s ORDER BY views DESC"
    params = [cat]
    cursor.execute(query,params)
    data = cursor.fetchall()
    print(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9])
    print("FIN")

#Funcion que devuelve el top 10 de usuarios mas activos por categoria
def top_users_cat(cat):
    query = "SELECT owner,link FROM questions WHERE about = %s AND text != ''"
    params = [cat]
    cursor.execute(query,params)
    data = cursor.fetchall()

    users = []
    for user in data:
        users.append(user[0])

    counts_questions = Counter(users)
    counts_questions = counts_questions.most_common()
    top_users = counts_questions[:10]
    top_users_string = str(top_users)

    query = "UPDATE categories SET top_users = %s WHERE ID = %s"
    params = [top_users_string,cat]
    cursor.execute(query,params)
    conn.commit()
    print('fin')

#Contar las preguntas de una categoria
def count_questions(cat):
    query = "SELECT * FROM questions WHERE text != '' AND about = %s"
    params = [cat]
    cursor.execute(query,params)
    questions = cursor.fetchall()
    questions = len(questions)
    print("La categoría : " + str(cat) + " tiene " + str(questions) + " preguntas.")
    query = "UPDATE categories SET questions = %s WHERE ID = %s"
    params = [questions,cat]
    cursor.execute(query,params)
    conn.commit()

#Contar respuestas de una categoria
def count_answers(cat):
    query = "SELECT * FROM questions WHERE text != '' AND about = %s"
    params = [cat]
    cursor.execute(query, params)
    questions = cursor.fetchall()

    answers = 0
    for question in questions:
        query = "SELECT * FROM answers WHERE question_id = %s"
        params = [question[1]]
        cursor.execute(query,params)
        answ = cursor.fetchall()
        answers = answers + len(answ)

    print("La categoria : " + str(cat) + " tiene " + str(answers) + " respuestas.")
    query = "UPDATE categories SET answers = %s WHERE ID = %s"
    params = [answers, cat]
    cursor.execute(query, params)
    conn.commit()

#Contar visitas de una categoría
def count_likes_views(cat):
    query = "SELECT * FROM questions WHERE text != '' AND about = %s"
    params = [cat]
    cursor.execute(query, params)
    questions = cursor.fetchall()

    likes = 0
    views = 0
    for question in questions:
        likes = likes + question[6]
        views = views + question[7]

    query = "UPDATE categories SET likes = %s, views = %s WHERE ID = %s"
    params = [likes, views, cat]
    cursor.execute(query, params)
    conn.commit()

def main():
    cats = [5,20,11,17,10,19,12,18,14,24,3,21,13,27,7,9,16,29,28]
    for cat in cats:
        top_cat(cat)
        count_likes_views(cat)
        count_answers(cat)
        count_questions(cat)
        top_users_cat(cat)