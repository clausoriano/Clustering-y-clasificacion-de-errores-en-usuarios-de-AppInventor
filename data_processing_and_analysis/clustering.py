from collections import Counter
import config
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pymysql
import seaborn as sb
from numpy.linalg import norm
#from pasta.augment import inline
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
from sympy.physics.quantum.circuitplot import matplotlib
#%matplotlib inline
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams['figure.figsize'] = (16, 9)
plt.style.use('ggplot')

# creamos la conexion con la BD
conn = pymysql.connect(user=config.user, password=config.password, host=config.host, database=config.database)
cursor = conn.cursor()

#Funcion auxiliar que sirve para formatear los embeddings
def ready_data():
    query = "SELECT embedding FROM questions WHERE embedding != ''"
    cursor.execute(query)
    data = cursor.fetchall()

    vec = []
    for d in data:
        aux = d[0].replace("[","")
        aux = aux.replace("]","")
        vec.append(np.fromstring(aux,dtype=float,sep=','))

    array = np.array(vec)
    return array


#Funcion que nos ayuda a elegir la K que vamos a aplicar a kmeans
def get_k():

    X = ready_data()

    Nc = range(1, 100)
    kmeans = [KMeans(n_clusters=i) for i in Nc]

    score = [kmeans[i].fit(X).score(X) for i in range(len(kmeans))]

    plt.plot(Nc, score)
    plt.xlabel('Number of Clusters')
    plt.ylabel('Score')
    plt.title('Elbow Curve')
    plt.show()

def apply_kmeans():

    X = ready_data()

    #Obtener los centroides
    kmeans = KMeans(n_clusters=20,max_iter=1000,random_state=3).fit(X)
    centroids = kmeans.cluster_centers_
    print(centroids)

    #Ejecutar kmeans
    labels = kmeans.predict(X)
    C = kmeans.cluster_centers_

    df = pd.DataFrame(labels,columns=['label'])

    colores=['red','green','blue','cyan','yellow','orange','indigo','coral','slategray','palegreen']

    colores=['red','green','blue','cyan','yellow','orange','indigo','coral','slategray','palegreen','lime','navy','turquoise','tan','olive','pink','cadetblue','deeppink','palevioletred','darkslateblue']
    asignar=[]
    for row in labels:
        asignar.append(colores[row])

    plt.scatter(X[:,0], X[:,1], c=asignar, s=70)
    plt.scatter(C[:, 0], C[:, 1], marker='*', c=colores, s=1000)
    plt.show()

    return(labels)

def update_similar_questions():
    query = "SELECT link,embedding,cluster FROM questions WHERE cluster != 'NULL'"
    cursor.execute(query)
    questions = cursor.fetchall()

    for question in questions:
        query = "SELECT link,embedding,cluster FROM questions WHERE cluster = %s"
        params = [question[2]]
        cursor.execute(query,params)
        in_same_cluster = cursor.fetchall()
        a_embedding = question[1]
        a_embedding = a_embedding.replace("[","")
        a_embedding = a_embedding.replace("[","")
        A = np.fromstring(a_embedding, dtype=float, sep=',')
        links = []
        similarities = []
        for q in in_same_cluster:
            b_embedding = q[1]
            b_embedding = b_embedding.replace("[", "")
            b_embedding = b_embedding.replace("[", "")
            B = np.fromstring(b_embedding, dtype=float, sep=',')
            cosine_similarity = np.dot(A,B)/(norm(A)*norm(B))
            links.append(q[0])
            similarities.append(cosine_similarity)
        results = pd.DataFrame({'link':links, 'similarity':similarities})
        results = results.sort_values(by='similarity',ascending=False)
        results = results.tail(-1)
        print(results.head())
        head = results.head()
        head = head['link']
        head = str(head.values.tolist())
        head = head.replace('[','')
        head = head.replace(']', '')
        head = head.replace("'", "")
        query = "UPDATE questions SET similars = %s WHERE link = %s"
        params = [head,question[0]]
        cursor.execute(query,params)
        conn.commit()
        print("Insertando similares a: " + str(question[0]))

    print("Fin")



def process():
    query = "SELECT about,link,text FROM questions WHERE embedding != ''"
    cursor.execute(query)
    data = cursor.fetchall()
    links = []
    abouts = []
    texts = []
    for d in data:
        abouts.append(d[0])
        links.append(d[1])
        texts.append(d[2])

    abouts = np.array(abouts)
    labels = apply_kmeans()
    df = pd.DataFrame({'links':links,'abouts': abouts, 'labels': labels,'texts':texts})
    cat_labels = {'5': 'MIT App Inventor Help', '20': 'Bugs and Other Issues', '11': 'General Discussion',
                  '17': 'Extensions', '10': 'Open Source Development', '19': 'App Inventor for iOS',
                  '12': 'Tutorials and Guides', '18': 'App Showcase', '14': 'Data Storage',
                  '24': 'Frequently Asked Questions', '3': 'Site Feedback', '21': 'Work for Hire',
                  '13': 'User Interface and Graphics',
                  '27': 'Appathon', '7': 'Community', '9': 'News/Announcements', '16': 'Artificial Intelligence',
                  '29': 'MIT App Inventor Alexa', '28': 'Translating App Inventor'}
    df['abouts'] = df['abouts'].map(cat_labels)

    results = df.values.tolist()
    for result in results:
        query = "UPDATE questions SET cluster = %s WHERE link = %s"
        params = [result[2],result[0]]
        cursor.execute(query,params)
        conn.commit()

    update_similar_questions()

