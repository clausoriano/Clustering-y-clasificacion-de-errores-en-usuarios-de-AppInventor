import urllib.request
import time
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
import re
import config
import answer as ans
import question
import requests
from bs4 import BeautifulSoup
import urllib.request
import pymysql
import urllib

# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

# Obtiene y guarda en la BD todos los links de las preguntas referentes a app-inventor en StackOverflow (Tabla Questions)
def obtain_questions_so():
    page = 1  # pagina a visitar
    flag = True  # controla si hemos llegado a la ultima pagina de resultados
    links_to_questions = []  # vector con los links de todas las preguntas

    while flag:
        url = "https://stackoverflow.com/questions/tagged/app-inventor?tab=votes&page=" + str(page) + "&pagesize=50"
        try:
            html_page = urllib.request.urlopen(url)
        except:
            flag = False
            break
        soup = BeautifulSoup(html_page, "html.parser")
        questions = soup.find("div", {"id": "questions"})
        questions = questions.find_all("div", {"class": "s-post-summary js-post-summary"})

        for q in questions:
            link = q.find("a", {"class": "s-link"})
            r1 = re.findall("\/([0-9]*)\/", str(link))
            links_to_questions.append(r1[0])

        page = page + 1

    # Guardar todos estos links en la bd
    for link in links_to_questions:
        newquestion = question.question(link, '', '', '', '', '', '', '', '', '', '',0)
        print("Insertado link: " + link)
        newquestion.insert()

# Obtiene y guarda en la BD todos los links de las preguntas del foro App Inventor (Tabla Questions)
def obtain_questions_forum():
    page = 0
    flag = True

    while flag:
        r = requests.get(
            'https://community.appinventor.mit.edu/latest.json?ascending=false&no_definitions=true&page=' + str(page))
        print('https://community.appinventor.mit.edu/latest.json?ascending=false&no_definitions=true&page=' + str(page))
        data = r.json()
        questions = data['topic_list']['topics']
        page = page + 1
        if len(questions) == 0:
            flag = False

        for q in questions:
            link = str(q['id'])
            title = q['title']
            score = q['like_count']
            views = q['views']
            date_info = q['created_at'].split("T")
            date = date_info[0]
            time_info = date_info[1].split(".")
            time_info = time_info[0]
            in_time = datetime.strptime(time_info, "%H:%M:%S")
            out_time = datetime.strftime(in_time, "%H:%M")
            category = q['category_id']
            owner = q['posters'][0]['user_id']
            tags = q['tags']
            tags = ','.join(tags)
            newquestion = question.question(link, owner, title, '', score, views, date, out_time, category, tags, '', 1)
            newquestion.insert()


def visit_links_forum():
    query = "SELECT link FROM questions WHERE site = 1 AND text = ''" # Seleccionamos los links de AppInventor community de la BD
    cursor.execute(query)
    links = cursor.fetchall()
    print (len(links))
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))  # Inicializamos el driver web
    driver.set_window_size(700, 768)
    for link in links:  # Procesamos cada link para obtener la pregunta y las respuestas
        url = "https://community.appinventor.mit.edu/t/" + str(link[0])
        print(url)
        driver.get(url)
        elems = driver.find_elements(By.CLASS_NAME, "topic-post")
        answers = []
        cont=0

        SCROLL_PAUSE_TIME = 0.5
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        print("LAST HEIGHT:" + str(last_height))

        # Visitar y guardar las respuestas de esa pregunta en la BD
        while True:
            elems = driver.find_elements(By.CLASS_NAME, "topic-post")
            for elem in elems:
                elem = elem.get_attribute('innerHTML')
                soup = BeautifulSoup(elem, "html.parser")
                user = soup.contents[0].attrs['data-user-id']
                score = soup.find("button", {"class": "widget-button btn-flat button-count like-count highlight-action regular-likes btn-text"})
                if score is None:
                    score = "0"
                else:
                    score = score.text
                postid = soup.contents[0].attrs['data-post-id']
                id = soup.contents[0].attrs['id']
                relative_date = soup.find("span", {"class": "relative-date"}).attrs['title']
                relative_date = relative_date.split()
                formated_time = relative_date[3] + " " + relative_date[4]
                in_time = datetime.strptime(formated_time, "%I:%M %p")
                out_time = datetime.strftime(in_time,"%H:%M")
                month = datetime.strptime(relative_date[0], '%b').month
                date = datetime(int(relative_date[2]), month, int(relative_date[1].replace(',','')))
                date = date.strftime("%Y-%m-%d")
                text = soup.find("div", {"class": "cooked"}).text
                is_solution = soup.find("span", {"class": "accepted-label"})
                if is_solution is None:
                    is_solution = "suggestedAnswer"
                else:
                    is_solution = "acceptedAnswer"
                #print("Pregunta: " + link[0]+ " Respuesta " + id + ":" + text)

                if id not in answers:
                    if id == 'post_1':  #Si es la pregunta, updateamos sus datos en la tabla questions
                        if text == '':
                            text = 'PREGUNTA SIN TEXTO'
                        print("Texto de la pregunta: " + text)
                        query = "UPDATE questions SET text = %s WHERE link = %s AND site = 1"
                        params = [text, link[0]]
                        cursor.execute(query, params)
                        conn.commit()
                    else:               #Si no es la pregunta, es una respuesta
                        query = "SELECT * FROM answers WHERE answer_id = %s AND site = 1" #Miramos si la respuesta  ya está insertada en la BBDD
                        params = [postid]
                        cursor.execute(query,params)
                        conn.commit()
                        data = cursor.fetchall()
                        if len(data) == 0: #Si no está insertada, la metemos
                            print("Insertando respuesta.")
                            answers.append(id)
                            newanswer = ans.answer(link[0], postid, user, text, is_solution, score,date,out_time,"",1)
                            newanswer.insert()
                        else: print("Esta respuesta ya esta insertada.")

            totalScrolledHeight = driver.execute_script("return window.pageYOffset + window.innerHeight")
            if totalScrolledHeight+1000 >= last_height:
                driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height <= last_height:
                    break
                last_height = new_height
            else:
                # Scroll down to bottom
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(SCROLL_PAUSE_TIME)

        print(answers)
        print('ERRORES: '+ str(cont))


# Visita cada link de la base de datos y llama al resto de funciones
def visit_links_so():
    query = "SELECT link FROM questions WHERE site = 0 AND owner = 0"
    cursor.execute(query)
    data = cursor.fetchall()
    cont = 0
    print(data)
    for link in data:
        cont = cont + 1
        if cont == 50:
            print(link[0])
        url = "https://stackoverflow.com/questions/" + str(link[0])
        try:
            html_page = urllib.request.urlopen(url)
        except:
            flag = False
            break
        soup = BeautifulSoup(html_page, "html.parser")
        obtain_owners(soup, cont, link)
        obtain_text(soup, cont, link)
        obtain_answers(soup, link)
        obtain_tags(soup, cont, link)
        time.sleep(2)


# Obtiene la ID del dueño de la pregunta, la fecha y la hora y la guarda en la BD (Tabla Questions)
def obtain_owners(soup, cont, link):
    question_info = soup.find("div", {"class": "post-signature owner flex--item"})
    errors = 0
    if(question_info is None):
        errors = errors +1
        print("ERRORES: " + str(errors))
    if(question_info is not None):
        owner_info = question_info.find_all("a", href=True)
        date_info = question_info.find("span", {'class': 'relativetime'})
        date_info = date_info.contents[0]
        date_info = date_info.split('at')
        in_date = date_info[0].replace(',','').split()
        month_number = datetime.strptime(in_date[0], '%b').month
        if len(in_date) == 2:
            today = date.today()
            year = today.year
            out_date = datetime(year, month_number, int(in_date[1])).strftime("%Y-%m-%d")
        else:
            out_date = datetime(int(in_date[2]),month_number,int(in_date[1])).strftime("%Y-%m-%d")

        time= date_info[1]
        if len(time) == 5:
            time = "0"+time
            time = time.replace(' ','')
        print(out_date)
        r1 = re.findall("\/([0-9]*)\/", str(owner_info))
        if len(r1) != 0:
            print("Contador = " + str(cont) + " Link = " + str(link) + " Owner = " + str(r1[0]))
            # Link al perfil del owner de la pregunta. Ahora la guardamos en la BD

            query = 'UPDATE questions SET owner = %s, username = %s, date = %s, time = %s WHERE link = %s'
            params = [r1[0], owner_info[1].text,out_date, time, link]
            cursor.execute(query, params)
            conn.commit()
            # handleamos el error de que el usuario ya no existe. ID usuario eliminado: -1
        else:
            print("Contador = " + str(cont) + " Link = " + str(link) + " Owner = Eliminado")
            query = 'UPDATE questions SET owner = %s, date = %s, time = %s WHERE link = %s'
            params = [-1, out_date, time, link]
            cursor.execute(query, params)
            conn.commit()


# Obtiene el texto principal de la pregunta, el titulo y la puntuacion y la guarda en la BD (Tabla Questions)
# Obtiene el texto principal de los comentarios de esa pregunta, el titulo, la puntuacion etc de los comentarios de la pregunta y los guarda en la BD (Tabla Comments)
def obtain_text(soup, cont, link):
    question_info = soup.find("div", {"id": "question-header"})
    text_info = soup.find("div", {"class": "question js-question"})
    score = text_info.attrs['data-score']
    text_info = text_info.find("div", {"class": "s-prose js-post-body"})
    question_views = soup.find("div", {"class": "d-flex fw-wrap pb8 mb16 bb bc-black-075"})
    question_views = question_views.find("div", {"class": "flex--item ws-nowrap mb8"})
    if question_views is None:
        question_views = soup.find("div", {"class": "d-flex fw-wrap pb8 mb16 bb bc-black-075"})
        question_views = question_views.find("div", {"class": "flex--item ws-nowrap mb8 mr16"})

    question_views = question_views.attrs['title'].split()[1].replace(',','')

    header_info = question_info.contents[1]
    header_info = header_info.contents[0].text
    text_info = text_info.text


    query = 'UPDATE questions SET title = %s, text = %s, score = %s, views = %s WHERE link = %s '  # anadimos los nuevos datos de las preguntas en la BD
    params = [header_info, text_info, score, question_views, link]
    cursor.execute(query, params)
    conn.commit()


# Obtiene y guarda los datos de los comentarios y sus respuestas en la BD
def obtain_answers(soup, link):
    answers = soup.find_all("div",
                            {"class": ["answer js-answer", "answer js-answer accepted-answer js-accepted-answer"]})
    for answer in answers:
        userdetails = answer.find_all("div", {
            "class": ["post-signature flex--item fl0", "post-signature owner flex--item fl0"]})

        owner_id = userdetails[-1]
        owner_id = owner_id.find("a", href=True)

        if not owner_id:
            owner_id =[]
            owner_id.append(-1)
        else:
            #owner_id = owner_id.attrs['href']
            owner_id = str(owner_id)
            owner_id = re.findall("users\/([0-9]*).", owner_id)
            if not owner_id:
                owner_id =[]
                owner_id.append(-1)

        answerid = answer.attrs['data-answerid']
        score = answer.attrs['data-score']
        category = answer.attrs['itemprop']
        text = answer.find("div", {"class": "s-prose js-post-body"})
        text = text.text
        date = answer.find("span", {"class": "relativetime"})
        date = date.contents[0]
        date_info = date.split('at')
        date_info[0] = date_info[0].replace(',', '')
        time = date_info[1]
        if date_info is None:
            if len(time) == 5:
                time = "0"+time
                time = time.replace(' ','')
        date = date_info[0].split(' ')
        if date[2] == '':
            date[2] = str(datetime.now().year)
        month = datetime.strptime(date[0],'%b').month
        date = datetime(int(date[2]),month,int(date[1]))
        date = date.strftime("%Y-%m-%d")
        newanswer = ans.answer(link[0], answerid, owner_id[0], text,category, score,date,time,"",0)
        newanswer.insert()


# Obtiene y guarda los tags adicionales de cada pregunta en la BD (Tabla Questions)
def obtain_tags(soup, cont, link):
    question = soup.find("div", {"class": "question js-question"})
    tags = question.find_all("li", {"class": "d-inline mr4 js-post-tag-list-item"})
    for tag in tags:
        if tag.text != "app-inventor":
            query = 'UPDATE questions SET tags = CONCAT(tags,",", %s ) WHERE link = %s;'
            params = [tag.text, link]
            cursor.execute(query, params)
            conn.commit()

    print("FIN")

# Obtener nombres de usuario app inventor
def users_data_forum():
    query = "SELECT link FROM questions WHERE site = 1 AND username = '' AND text != ''"  # Seleccionamos los links de AppInventor community de la BD
    cursor.execute(query)
    questions = cursor.fetchall()

    for question in questions:

        flag = True
        url = "https://community.appinventor.mit.edu/t/" + str(question[0])
        print("Link: " + url)
        try:
            html_page = urllib.request.urlopen(url)
        except:
            print("Esa pagina ya no existe.")
            flag = False

        if flag:
            soup = BeautifulSoup(html_page, "html.parser")
            username = soup.find("span", {'class': 'creator'})
            username = username.find("span").text

            query = "UPDATE questions SET username = %s WHERE link = %s AND site = 1"
            params = [username,question[0]]
            cursor.execute(query,params)

            query = "SELECT username FROM users"
            cursor.execute(query)
            users = cursor.fetchall()

            if (any(username in i for i in users)):
                print("Ese usuario ya esta en la BBDD")
            else:
                query = "INSERT INTO users(username) VALUES (%s)"
                params = [username]
                cursor.execute(query, params)
                print("Usuario: " + username + " insertado.")

            conn.commit()

# visitar los perfiles de los usuarios para obtener su localización
def visit_users_profiles_forum():
    query = "SELECT username FROM users WHERE owner = 0"  # Seleccionamos los links de AppInventor community de la BD
    cursor.execute(query)
    usernames = cursor.fetchall()

    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))  # Inicializamos el driver web
    driver.set_window_size(700, 768)

    for username in usernames:

        flag = True
        url = "https://community.appinventor.mit.edu/u/"+ str(username[0])
        print("Profile link: " + url)
        try:
            html_page = urllib.request.urlopen(url)
        except:
            print("Ese perfil ya no existe.")
            flag = False

        if flag:
            driver.get(url)
            soup = BeautifulSoup(driver.page_source,"html.parser")
            data = soup.find("div", {"class": "ember-view"})
            location = data.find("div", {"class": "user-profile-location"})

            if location is None:
                location = ''
            else:
                location = location.text
            print("Usuario: " + str(username[0]) + " Location: " + location)


            query = "UPDATE users SET location = %s WHERE username = %s"
            params = [location, str(username[0])]
            cursor.execute(query, params)
            conn.commit()


        query = "SELECT owner FROM questions WHERE username = %s"
        params = [str(username[0])]
        cursor.execute(query, params)
        data = cursor.fetchone()

        query = "UPDATE users SET owner = %s WHERE username = %s"
        params = [data[0], str(username[0])]
        cursor.execute(query, params)
        conn.commit()

        print("Fin")
        time.sleep(1.5)


def main():
    obtain_questions_so()
    obtain_questions_forum()
    visit_links_so()
    visit_links_forum()
    users_data_forum()
    visit_users_profiles_forum()




