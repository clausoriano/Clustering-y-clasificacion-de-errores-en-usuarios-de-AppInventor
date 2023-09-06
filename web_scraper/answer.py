import pymysql
import config
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()


#Clase que nos permite manejar las respuestas de la BD y sus atributos como objeto
class answer:

    #Constructor
    def __init__(self,question_id,answer_id,owner=0,text="",category="",score="0",date=0,time=0,sentiments ="",site=""):
        self.question_id = question_id
        self.answer_id = answer_id
        self.owner = owner
        self.text = text
        self.score = score
        self.category = category
        self.date = date
        self.time = time
        self.sentiments = sentiments
        self.site = site


    #Insertar un nuevo registro en la BD
    def insert(self):
        query = 'INSERT INTO answers(question_id,answer_id,owner,text,category,score,date,time,sentiments,site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        params = [self.question_id,self.answer_id,self.owner,self.text,self.category,self.score,self.date,self.time,self.sentiments,self.site]
        cursor.execute(query, params)
        conn.commit()

    #Borrar un registro de la BD
    def delete(self):
        query = 'DELETE FROM answers WHERE answer_id = %s;'
        params = self.answer_id
        cursor.execute(query, params)
        conn.commit()

#Buscar respuestas en la BD
def get_answers(question_id):
    query = 'SELECT * FROM answers WHERE question_id = %s;'
    params = question_id
    cursor.execute(query, params)
    data = cursor.fetchall()
    data = data[0]
    return answer(data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11])