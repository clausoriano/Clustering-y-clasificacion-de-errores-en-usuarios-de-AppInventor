import decimal
import config
import pymysql
from transformers import pipeline
from nltk.tokenize import word_tokenize

# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

# Funcion que analiza y guarda los sentimientos de las preguntas en la BBDD
def question_diagnosis(question):
    classifier = pipeline("text-classification", model = "j-hartmann/emotion-english-distilroberta-base", return_all_scores=True, truncation = True)

    sentiments = classifier(question[5])
    diagnosis = ""
    for sentiment in sentiments[0]:
        diagnosis = diagnosis + sentiment['label'] + ": " + str(sentiment['score']) + ", "

    print("Diagnosis: " + diagnosis)
    query = "UPDATE questions SET sentiments = %s WHERE link = %s AND site = %s"
    params = [diagnosis,question[1],question[13]]
    cursor.execute(query,params)
    conn.commit()

    query = "SELECT answer_id,text,site FROM answers WHERE sentiments = '' AND question_id = %s"
    params = [question[1]]
    cursor.execute(query, params)
    answers = cursor.fetchall()
    answers_diagnosis(answers)
    print("test")


# Funcion que analiza y guarda los sentimientos de las respuestas en la BBDD
def answers_diagnosis(answers):

    # las pasamos al modelo de sentiment analysis y las guardamos el resultado en la BBDD
    for answer in answers:
        classifier = pipeline("text-classification", model = "j-hartmann/emotion-english-distilroberta-base", return_all_scores=True, truncation = True)
        sentiments = classifier(answer[1])

        diagnosis = ""
        for sentiment in sentiments[0]:
            diagnosis = diagnosis + sentiment['label'] + ": " + str(sentiment['score']) + ", "


        query = "UPDATE answers SET sentiments = %s WHERE answer_id = %s AND site = %s"
        params = [diagnosis, answer[0], answer[2]]
        cursor.execute(query, params)
        conn.commit()

# Funcion que devuelve los sentimientos de la categoría especificada
def sentiment_per_cat(cat):
    query = "SELECT link,about,sentiments FROM questions WHERE about = %s AND sentiments != ''"
    params = [cat]
    cursor.execute(query,params)
    data = cursor.fetchall()
    anger = 0
    disgust = 0
    fear = 0
    joy = 0
    neutral = 0
    sadness = 0
    surprise = 0
    lenght = len(data)

    # Sumamos los valores y los dividimos para hacer la media de cada sentimiento
    for d in data:
        sentiments = d[2].split(",")
        anger = anger + float(sentiments[0].split(":")[1])
        disgust = disgust + float(sentiments[1].split(":")[1])
        fear = fear + float(sentiments[2].split(":")[1])
        joy = joy + float(sentiments[3].split(":")[1])
        neutral = neutral + float(sentiments[4].split(":")[1])
        sadness = sadness + float(sentiments[5].split(":")[1])
        surprise = surprise + float(sentiments[6].split(":")[1])

    anger = round((anger/lenght)*100,1)
    disgust = round((disgust/lenght)*100,1)
    fear = round((fear/lenght)*100,1)
    joy = round((joy/lenght)*100,1)
    neutral = round((neutral/lenght)*100,1)
    sadness = round((sadness/lenght)*100,1)
    surprise = round((surprise/lenght)*100,1)

    print("Anger: " + str(anger))
    print("Disgust: " + str(disgust))
    print("Fear: " + str(fear))
    print("Joy: " + str(joy))
    print("Neutral: " + str(neutral))
    print("Sadness: " + str(sadness))
    print("Surprise: " + str(surprise))

    query = "UPDATE categories SET anger = %s, disgust = %s, fear = %s, joy = %s, neutral = %s, sadness = %s, surprise = %s WHERE ID = %s"
    params = [anger, disgust, fear, joy, neutral, sadness, surprise, cat]
    cursor.execute(query, params)
    conn.commit()



def global_sentiments():
    query = "SELECT link,about,sentiments FROM questions WHERE sentiments != ''"
    cursor.execute(query)
    data = cursor.fetchall()
    anger = 0
    disgust = 0
    fear = 0
    joy = 0
    neutral = 0
    sadness = 0
    surprise = 0
    lenght = len(data)

    # Sumamos los valores y los dividimos para hacer la media de cada sentimiento
    for d in data:
        sentiments = d[2].split(",")
        anger = anger + float(sentiments[0].split(":")[1])
        disgust = disgust + float(sentiments[1].split(":")[1])
        fear = fear + float(sentiments[2].split(":")[1])
        joy = joy + float(sentiments[3].split(":")[1])
        neutral = neutral + float(sentiments[4].split(":")[1])
        sadness = sadness + float(sentiments[5].split(":")[1])
        surprise = surprise + float(sentiments[6].split(":")[1])

    anger = round((anger/lenght)*100,1)
    disgust = round((disgust/lenght)*100,1)
    fear = round((fear/lenght)*100,1)
    joy = round((joy/lenght)*100,1)
    neutral = round((neutral/lenght)*100,1)
    sadness = round((sadness/lenght)*100,1)
    surprise = round((surprise/lenght)*100,1)

    print("Anger: " + str(anger))
    print("Disgust: " + str(disgust))
    print("Fear: " + str(fear))
    print("Joy: " + str(joy))
    print("Neutral: " + str(neutral))
    print("Sadness: " + str(sadness))
    print("Surprise: " + str(surprise))

    query = "UPDATE sentiments SET anger = %s, disgust = %s, fear = %s, joy = %s, neutral = %s, sadness = %s, surprise = %s"
    params = [anger,disgust,fear,joy,neutral,sadness,surprise]
    cursor.execute(query,params)
    conn.commit()


def process1(question):
    question_diagnosis(question)

def process2():
    cats = [5, 20, 11, 17, 10, 19, 12, 18, 14, 24, 3, 21, 13, 27, 7, 9, 16, 29, 28]
    for cat in cats:
        print("Analizando categoria: " + str(cat))
        sentiment_per_cat(cat)

    global_sentiments()
