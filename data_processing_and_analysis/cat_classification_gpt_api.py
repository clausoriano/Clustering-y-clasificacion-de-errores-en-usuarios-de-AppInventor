import os
import time
import openai
import pymysql
import tiktoken
import config
import json

#DESCRIPCION: Asigna a cada pregunta de StackOverflow una categoría de las existentes en el Foro Oficial de App Inventor
def cat_classification_gpt():
    # creamos la conexion con la API
    openai.api_key = config.api_key
    # creamos la conexion con la BD
    conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
    cursor = conn.cursor()

    # explicacion tarea para chatGPT
    duty_explanation = '''I'm gonna provide you with some category definitions, i need you to memorise them and then categorize some text based on the category definitions i explained you earlier.'''
    category_1 = '''Category 5 description: MIT App Inventor Help. This is a place for MIT App Inventor Programmers to ask questions or report problems using MIT App Inventor.'''
    category_2 = '''Category 20 description: Bugs and Other Issues. Report potential issues with App Inventor in this category.'''
    category_3 = '''Category 11 description: General discussion. This category is for general discussion of app development, not necessarily related to a specific part of App Inventor. It may include topics of interest to the larger app development community for discussion in the context of MIT App Inventor'''
    category_4 = '''Category 17 description: Extensions. Propose new extensions, get help with extensions, or share your extensions here.'''
    category_5 = '''Category 10 description: Open Source Development. This category is used for sharing development progress for those building on the MIT App Inventor open source repository at https://github.com/mit-cml/appinventor-sources. Anyone interested in extending core App Inventor or writing extensions should join this group and share their experiences.'''
    category_6 = '''Category 19 description: App Inventor for iOS. Learn more about development of MIT App Inventor for iOS. Beta testing participants should discuss iOS specific functionality here.'''
    category_7 = '''Category 12 description: Tutorials and Guides. Post useful tutorials and helpful guides to this category.'''
    category_8 = '''Category 18 description: App Showcase. Showcase your finished apps and get feedback from other app inventors.'''
    category_9 = '''Category 14 description: Data Storage. Discuss ways of storing and processing data in apps as well as making cross platform applications using components like CloudDB.'''
    category_10 = '''Category 24 description: Frequently Asked Questions. Look here first for the best answers. Tired of retyping answers to common questions?'''
    category_11 = '''Category 3 description: Site Feedback. Discussion about this site, its organization, how it works, and how we can improve it.'''
    category_12 = '''Category 21 description: Work for Hire. Freelancers and people looking for someone to help build apps should use this category to get connected.'''
    category_13 = '''Category 13 description: User Interface and Graphics. This category is for asking questions or offering help on good user interface design for App Inventor apps. Share your tips and tricks with other users to provide the best user experience and visuals with the community.'''
    category_14 = '''Category 27 description: Appathon. Use this category to discuss topics related to the MIT App Inventor Appathon. MIT will also use this category to make occasional announcements.'''
    category_15 = '''Category 7 description: Community. Informational posts about MIT App Inventor and the community, such as best practices, posting guidelines, and other information are placed here.'''
    category_16 = '''Category 9 description: News and Announcements.MIT uses this category to announce new App Inventor features and releases.'''
    category_17 = '''Category 16 description: Artificial Intelligence. App Inventor provides opportunities to incorporate artificial intelligence into mobile apps using frameworks like Google’s TensorFlow.js. Share extensions, tutorials, and projects that showcase the power of mobile-enabled AI.'''
    category_18 = '''Category 29 description: MIT App Inventor Alexa. This category is intended for posts related to supporting the MIT App Inventor for Alexa platform at https://alexa.appinventor.mit.edu/.'''
    category_19 = '''Category 28 description: Translating App Inventor. App Inventor relies on the community to provide translations in a wide variety of languages. If your language is missing or incomplete, please consider signing up to be a translator!'''
    question = '''Based on the description of the 19 previous categories, where would you categorise this text?'''
    final_instruction = '''Answer with the category number in json format'''

    # seleccionamos las preguntas de stackoverflow porque son las unicas que no tienen categoria asignada.
    query = "SELECT link,text,site FROM questions WHERE about = '' AND site = 0"
    cursor.execute(query)
    uncategorized = cursor.fetchall()

    #numero de tokens del enunciado
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    firstEncoding = encoding.encode(category_1 + category_2 + category_3 + category_4 + category_5 + category_6 + category_7 + category_8 + category_9 + category_10 + category_11 + category_12 + category_13 + category_14 + category_15 + category_16 + category_17 + category_18 + category_19 + question + final_instruction)


    # tarea y llamada a la api de chatGPT, por cada pregunta hacemos llamada a la api
    for quest in uncategorized:
      question = '''Based on the description of the 19 previous categories, where would you categorise this text?'''
      text_to_categorize = quest[1]

      #numero de tokens de la pregunta
      encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
      secondEncoding = encoding.encode(text_to_categorize + question)

    # controlamos que el numero de tokens no supere el maximo permitido por el modelo
      trimmedString = ''
      flag = False
      while (len(firstEncoding)+len(secondEncoding)) > 4097:
        flag = True
        for i in range(0, len(text_to_categorize)):
          if i <= len(text_to_categorize) // 2 - 1:
            trimmedString = trimmedString + text_to_categorize[i]
            secondEncoding = encoding.encode(trimmedString)
      if flag:
        text_to_categorize = trimmedString


      completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", temperature = 0,
        messages=[
          {"role": "user", "content": duty_explanation},
          {"role": "user", "content": category_1},
          {"role": "user", "content": category_2},
          {"role": "user", "content": category_3},
          {"role": "user", "content": category_4},
          {"role": "user", "content": category_5},
          {"role": "user", "content": category_6},
          {"role": "user", "content": category_7},
          {"role": "user", "content": category_8},
          {"role": "user", "content": category_9},
          {"role": "user", "content": category_10},
          {"role": "user", "content": category_11},
          {"role": "user", "content": category_12},
          {"role": "user", "content": category_13},
          {"role": "user", "content": category_14},
          {"role": "user", "content": category_15},
          {"role": "user", "content": category_16},
          {"role": "user", "content": category_17},
          {"role": "user", "content": category_18},
          {"role": "user", "content": category_19},
          {"role": "user", "content": question},
          {"role": "user", "content": text_to_categorize},
          {"role": "user", "content": final_instruction}
        ]
      )

      #respuesta de cada pregunta
      solution = completion.choices[0].message.content
      solution = json.loads(solution)
      category = solution['category']
      print(solution)

      #guardamos la respuesta en la BBDD
      query = 'UPDATE questions SET about = %s WHERE site = 0 AND link = %s;'
      params = [category,quest[0]]
      cursor.execute(query,params)
      conn.commit()

      time.sleep(20)

def main():
    cat_classification_gpt()