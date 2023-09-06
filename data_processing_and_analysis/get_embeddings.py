import openai
import pymysql
import tiktoken

import config
import pandas as pd
import numpy as np
import re
import nltk
import spacy
import string
import time
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
", ".join(stopwords.words('english'))

STOPWORDS = set(stopwords.words('english'))
PUNCT_TO_REMOVE = string.punctuation
lemmatizer = WordNetLemmatizer()
wordnet_map = {"N":wordnet.NOUN, "V":wordnet.VERB, "J":wordnet.ADJ, "R":wordnet.ADV}

openai.api_key = config.api_key
# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

def remove_punctuation(text):
   return text.translate(str.maketrans('', '', PUNCT_TO_REMOVE))

def remove_stopwords(text):
   return " ".join([word for word in str(text).split() if word not in STOPWORDS])

def lemmatize_words(text):
   pos_tagged_text = nltk.pos_tag(text.split())
   return " ".join([lemmatizer.lemmatize(word, wordnet_map.get(pos[0], wordnet.NOUN)) for word, pos in pos_tagged_text])

def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   embedding = openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']
   time.sleep(20)
   return embedding

def getemb_questions():
   query = "SELECT link,text FROM questions WHERE text != '' AND embedding ='' AND site = 1"
   cursor.execute(query)
   questions = cursor.fetchall()

   full_df = pd.DataFrame(questions, columns=['link', 'text'])
   full_df.head()

   # lower casing
   full_df["text_lower"] = full_df["text"].str.lower()

   # removal of punctuations
   full_df['text_wo_punct'] = full_df["text_lower"].apply(lambda text: remove_punctuation(text))

   # removal of stopwords
   full_df["text_wo_stop"] = full_df["text_wo_punct"].apply(lambda text: remove_stopwords(text))

   # lemmatization
   full_df["text_lemmatized"] = full_df["text_wo_stop"].apply(lambda text: lemmatize_words(text))

   # convert df to list and get embedding
   questions = full_df.values.tolist()
   for question in questions:
      encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
      tokens = encoding.encode(question[5])
      if len(tokens) < 4097:
         embedding = get_embedding(question[5])
         length = len(embedding)
         query = "UPDATE questions SET embedding = %s WHERE link = %s"
         params = [str(embedding),question[0]]
         cursor.execute(query,params)
         conn.commit()
         print("---------------------------------------------------------------------------")
         print("Question " + str(question[0]) + ": " + str(embedding))
         print("Dimension: " + str(length))
         print("---------------------------------------------------------------------------")
      else:
         print("---------------------------------------------------------------------------")
         print("Question "+ str(question[0]) + ": Too many tokens -> " + str(len(tokens)))
         print("---------------------------------------------------------------------------")

   print("end")

def getemb_answers():
   query = "SELECT answer_id,text FROM answers WHERE text != '' AND embedding ='' AND site = 1"
   cursor.execute(query)
   questions = cursor.fetchall()

   full_df = pd.DataFrame(questions, columns=['link', 'text'])
   full_df.head()

   # lower casing
   full_df["text_lower"] = full_df["text"].str.lower()

   # removal of punctuations
   full_df['text_wo_punct'] = full_df["text_lower"].apply(lambda text: remove_punctuation(text))

   # removal of stopwords
   full_df["text_wo_stop"] = full_df["text_wo_punct"].apply(lambda text: remove_stopwords(text))

   # lemmatization
   full_df["text_lemmatized"] = full_df["text_wo_stop"].apply(lambda text: lemmatize_words(text))

   # convert df to list and get embedding
   answers = full_df.values.tolist()
   for answer in answers:
      encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
      tokens = encoding.encode(answer[5])
      if len(tokens) < 4097:
         if answer[5] != '':
            embedding = get_embedding(answer[5])
            length = len(embedding)
            query = "UPDATE answers SET embedding = %s WHERE answer_id = %s"
            params = [str(embedding),answer[0]]
            cursor.execute(query,params)
            conn.commit()
            print("---------------------------------------------------------------------------")
            print("Answer " + str(answer[0]) + ": " + str(embedding))
            print("Dimension: " + str(length))
            print("---------------------------------------------------------------------------")
      else:
         print("---------------------------------------------------------------------------")
         print("Answer "+ str(answer[0]) + ": Too many tokens -> " + str(len(tokens)))
         print("---------------------------------------------------------------------------")

   print("end")

def main():
   getemb_questions()
   getemb_answers()