import time
import numpy as np
from numpy.linalg import norm
import pandas as pd
pd.set_option('display.max_columns', None)
import pymysql
import openai
import config


# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

# Funcion que guarda en la tabla ai_answers todas las preguntas que no tienen respuesta aceptada
def get_unanswered_questions(quest):
    # Por cada pregunta buscamos sus respuestas en la tabla de respuestas y comprobamos si alguna de ellas esta catalogada como solucion oficialmente (acceptedAnswer)
    query = "SELECT answer_id,text,category,score FROM answers WHERE question_id = %s"
    params = [quest[1]]
    cursor.execute(query, params)
    answers = cursor.fetchall()

    # Si alguna respuesta es acceptedAnswer salimos y no hacemos nada, si no encontramos ninguna acceptedAnswer, guardamos el link de la pregunta en la BBDD
    flag = True
    for answ in answers:
        if str(answ[2]) == "acceptedAnswer":
            flag = False

    if flag:
        query = "INSERT INTO ai_answers (question_id) VALUES (%s)"
        params = [quest[1]]
        cursor.execute(query,params)
        conn.commit()
        get_solution_gpt_api(quest)
    else:
        print("Con respuesta aceptada: " + str(quest[0]))


# Funcion que realiza el embedding del texto
def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   embedding = openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']
   time.sleep(20)
   return embedding

# Funcion que mediante embeddings de chat gpt propone una respuesta aceptada a las preguntas de la tabla ai_answers
def get_solution_gpt_api(question):
    # configuracion api chat gpt
    openai.api_key = config.api_key

    # por cada pregunta sacamos su texto y sus respuestas
    question_text = question[5]

    query = "SELECT text,answer_id,embedding FROM answers WHERE question_id = %s"
    params = [question[1]]
    cursor.execute(query,params)
    answers = cursor.fetchall()
    answers_texts = []
    for answer in answers:
        answers_texts.append(answer)

    if len(answers_texts) != 0:
        # ahora llamamos a chatgpt para que responda a la pregunta
        duty_explanation = "I'm working with App Inventor: " + question_text
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", temperature=0,
            messages=[
                {"role": "user", "content": duty_explanation},
            ]
        )
        solution = completion.choices[0].message.content
        solution_df = pd.DataFrame([solution], columns=['solution'])

        # embedding pregunta
        solution_df['ada_embedding'] = solution_df.solution.apply(lambda x: get_embedding(x, model='text-embedding-ada-002'))
        A = np.array(solution_df['ada_embedding'])
        A = np.array(A[0])

        # embeddings de las respuestas del foro
        df = pd.DataFrame(answers_texts, columns=['text','link','embedding'])
        answ = df.values.tolist()

        index = 0
        aux_cosine = 0
        aux_index = 0
        for ans in answ:
            #B = np.array(ans[2])
            answ_embedding = ans[2]
            answ_embedding = answ_embedding.replace("[","").replace("]","")
            B =np.fromstring(answ_embedding,sep=',')
            cosine1 = np.dot(A,B)
            cosine2 = norm(A) * norm(B)
            cosine = np.dot(A, B) / (norm(A) * norm(B))
            print("Cosine Similarity with answer " + str(index) + ":" +  str(cosine))
            if cosine > aux_cosine:
                aux_cosine = cosine
                aux_index = index
            index += 1

        best_answer = df.loc[aux_index, ['text', 'link']]
        print("The best answer is: " + str(best_answer))
        best_answer_id = int(best_answer['link'])

        query = "UPDATE ai_answers SET ai_answer = %s, ai_suggested_answer = %s WHERE question_id = %s"
        params = [solution,best_answer_id,question[1]]
        cursor.execute(query,params)
        conn.commit()


        print("FIN")

def process(question):
    get_unanswered_questions(question)