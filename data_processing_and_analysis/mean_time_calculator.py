import pandas as pd
import pymysql

import datetime
import config
import numpy as np
import _strptime


conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

#Calcular el tiempo medio de respuesta por cada categoria
def mean_time_per_cat(category):
    query = "SELECT * FROM questions WHERE about = %s"
    params = [category]
    cursor.execute(query,params)
    questions = cursor.fetchall()
    days = []

    for question in questions:
        query = "SELECT * FROM answers WHERE question_id = %s AND category = %s"
        params = [question[1],"acceptedAnswer"]
        cursor.execute(query,params)
        acceptedanswer = cursor.fetchall()
        if len(acceptedanswer) != 0:
            quest_date = str(question[8])
            answ_date = str(acceptedanswer[0][7])

            d1 = datetime.datetime.strptime(answ_date, "%Y-%m-%d")
            d2 = datetime.datetime.strptime(quest_date, "%Y-%m-%d")

            delta_date = d1 - d2
            print("Respuesta aceptada encontrada en: " + str(delta_date.days) + " dias.")

            days.append(int(delta_date.days))

    np_vector = np.array(days)
    np_vector.sort()
    q3, q1 = np.percentile(np_vector, [75, 25])
    iqr = q3 - q1
    iqr = round(iqr,2)
    print("Tiempo medio (rango intercuartil) para la respuesta aceptada: " + str(round(iqr,2)) + " dias.")

    query = "UPDATE categories SET ans_mean_time = %s WHERE ID = %s"
    params = [iqr,category]
    cursor.execute(query,params)
    conn.commit()

def main():
    cats = [5, 20, 11, 17, 10, 19, 12, 18, 14, 24, 3, 21, 13, 27, 7, 9, 16, 29, 28]
    for cat in cats:
        mean_time_per_cat(cat)


