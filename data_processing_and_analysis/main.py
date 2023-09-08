import pymysql
import config
import cat_classification_gpt_api
import clustering
import get_embeddings
import location_gpt_api
import mean_time_calculator
import sentiment_analysis
import solution_finder_gpt_api
import tags
import top

# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

query = "SELECT * FROM questions WHERE text != ''"
cursor.execute(query)
questions = cursor.fetchall()

#Ejecutar la totalidad del analisis de datos.
def execute_data_analysis1():
    for question in questions:
        print("----------------------------------------------")
        print("Question: " + question[1])
        if question[10] == '':
            cat_classification_gpt_api.process(question) #Asignar categoría
        if question[12] == '':
            sentiment_analysis.process1(question) #Sentiment analisis de la pregunta y sus respuestas
        if question[14] == '':
            get_embeddings.process(question) #Embeddings de la pregunta y sus respuestas

        query = "SELECT * FROM ai_answers WHERE question_id = %s"
        params = [question[1]]
        cursor.execute(query,params)
        has_ai_answer = cursor.fetchall()
        if len(has_ai_answer) == 0:
            solution_finder_gpt_api.process(question) #Recomendacion respuesta de la AI
        print("----------------------------------------------")

def execute_data_analysis2():
    print("Ejecutando analisis de sentimientos globales y por categoria.")
    sentiment_analysis.process2()
    print("Ejecutando tags.")
    tags.process()
    print("Ejecutando meantime.")
    mean_time_calculator.process()
    print("Ejecutando location.")
    location_gpt_api.process()
    print("Ejecutando tops.")
    top.process()
    print("Ejecutando clustering.")
    clustering.process()

execute_data_analysis1()
execute_data_analysis2()
