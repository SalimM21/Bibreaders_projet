

#Charger le modèle pré-calculé
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Livre
from sklearn.metrics.pairwise import cosine_similarity


# Charger le TF-IDF Vectorizer et la matrice de similarité
with open("models/tfidf_vectorizer.pkl", "rb") as f:
    tfidf = joblib.load(f)

with open("models/cosine_sim.pkl", "rb") as f:
    cosine_sim = joblib.load(f)

# Charger les livres depuis la DB pour récupérer titre/id
#session = SessionLocal()
#books = session.query(Livre).all()
#df_books = pd.DataFrame([{"id": b.id, "titre": b.titre} for b in books])
#session.close()
# Charger la liste des livres si nécessaire pour les titres
df_livres = pd.read_csv("dataset/livres_bruts.csv") 

#Fonction de recommandation par livre

def get_recommendations(title, top_n=5):
    # Vérifie si le titre existe
    if title not in df_livres['title'].values:
        return []

    # Index du livre
    idx = df_livres.index[df_livres['title'] == title][0]
    
    # Scores de similarité
    sim_scores = list(enumerate(cosine_sim[idx]))
    
    # Trier les scores par similarité (descendant)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Prendre les top_n + 1 (le premier sera le livre lui-même)
    top_indices = [i[0] for i in sim_scores[1:top_n+1]]
    
    return df_livres.iloc[top_indices].to_dict(orient="records")


# Fonction de recommandation par description (texte libre)

def recommend_by_description(desc, df=df_livres, tfidf=tfidf, sim_matrix=cosine_sim, top_n=5):
    # Transformer la description en vecteur TF-IDF
    desc_vec = tfidf.transform([desc])
    
    # Calculer la similarité cosinus avec tous les livres
    sim_scores = cosine_similarity(desc_vec, sim_matrix)[0]
    
    # Trier par score décroissant
    top_indices = sim_scores.argsort()[-top_n:][::-1]
    
    return df.iloc[top_indices].to_dict(orient="records")

