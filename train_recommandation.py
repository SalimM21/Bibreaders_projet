# train_recommendation.py
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer


df = pd.read_csv("dataset/livres_bruts.csv")


# Créer le vectorizer TF-IDF
vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

# Calculer la matrice TF-IDF
tfidf_matrix = vectorizer.fit_transform(df["Description"])

# Sauvegarder les objets pour FastAPI
joblib.dump(vectorizer, "models/tfidf_vectorizer.pkl")
joblib.dump(tfidf_matrix, "models/cosine_sim.pkl")
#joblib.dump(df, "models/livres_metadata.pkl")
