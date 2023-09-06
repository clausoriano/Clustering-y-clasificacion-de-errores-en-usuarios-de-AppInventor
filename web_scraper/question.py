import pymysql
import config

conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

#Clase que nos permite manejar las preguntas de la BD y sus atributos como objeto
class question:

    #Constructor
    def __init__(self,link,owner=0,title="",text="",score="", views="0",date="",time="",about="",tags="",sentiments="",site=""):
        self.link = link
        self.owner = owner
        self.title = title
        self.text = text
        self.score = score
        self.views = views
        self.date = date
        self.time = time
        self.about = about
        self.tags = tags
        self.sentiments = sentiments
        self.site = site

    #Insertar un nuevo registro en la BD
    def insert(self):
        query = 'INSERT INTO questions(link,title,owner,text,score,views,date,time,about,tags,sentiments,site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        params = [self.link,self.title,self.owner,self.text,self.score,self.views,self.date,self.time,self.about,self.tags,self.sentiments,self.site]
        cursor.execute(query, params)
        conn.commit()


    #Borrar un registro de la BD
    def delete(self):
        query = 'DELETE FROM questions WHERE link = %s;'
        params = self.link
        cursor.execute(query, params)
        conn.commit()

#Buscar una pregunta en la BD
def get_question(link):
    query = 'SELECT * FROM questions WHERE link = %s;'
    params = link
    cursor.execute(query, params)
    data = cursor.fetchall()
    data = data[0]
    return question(data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10])


#Obtener N parametros de todas las preguntas.
def get_params(params):
    query = 'SELECT ' + params + ' FROM questions;'
    cursor.execute(query)
    data = cursor.fetchall()
    return data



