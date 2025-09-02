# 📚 Bib-Readers Project

Projet de gestion et d’analyse des livres avec **FastAPI**, **SQLAlchemy**, **NLTK**, **scikit-learn** et **MLflow**.  
L’application inclut :  
- Une API REST pour gérer les livres et les adhérents.  
- Un module de classification basé sur **TF-IDF + Naive Bayes** pour la détection de spams/descriptions.  
- Un suivi des expérimentations avec **MLflow**.  

---

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/votre-repo/Bib-Readers-project.git
cd Bib-Readers-project
```

### 2. Créer et activer un environnement virtuel
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration de la base de données

Créer un fichier `.env` à la racine avec vos paramètres :

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=monmotdepasse
DB_NAME=bib_readers
```

---

## ▶️ Lancer l’API FastAPI

```bash
uvicorn main:app --reload
```

- L’API sera disponible sur : `http://127.0.0.1:8000`
- Documentation interactive : `http://127.0.0.1:8000/docs`

---

## 📄 Exemple d’API

### Créer un adhérent
```http
POST /api/register
Content-Type: application/json

{
  "nom": "Doe",
  "prenom": "John",
  "email": "john.doe@example.com"
}
```

### Ajouter un livre
```http
POST /api/livres
Content-Type: application/json

{
  "title": "1984",
  "description": "Un roman dystopique",
  "price": 12.99,
  "availability": "En stock",
  "rating": 5,
  "availability_num": 10
}
```

---

## 🤖 Machine Learning

### 1. Prétraitement du texte
- Tokenisation avec **NLTK**  
- Suppression des stopwords (FR + EN)  
- Lemmatisation / stemming  
- Vectorisation avec **TF-IDF**  

### 2. Entraînement
Exemple : Naive Bayes  
```python
from sklearn.naive_bayes import MultinomialNB
model = MultinomialNB(alpha=1.0)
model.fit(X_train, y_train)
```

### 3. Suivi MLflow
Lancer le serveur MLflow :
```bash
mlflow ui
```
Puis accéder à : `http://127.0.0.1:5000`

---

## 📂 Arborescence du projet

```
Bib-Readers-project/
│── main.py                # Point d’entrée FastAPI
│── database.py            # Connexion à la base
│── models.py              # Modèles SQLAlchemy
│── schemas.py             # Schémas Pydantic
│── ml/                    # Scripts ML (TF-IDF, MLflow…)
│── templates/             # Pages HTML (inscription.html, etc.)
│── static/                # CSS / JS
│── artifacts/             # Vectorizers sauvegardés
│── models/                # Modèles ML sauvegardés
│── requirements.txt
│── README.md
```

---

## ✅ Prérequis

- Python 3.9+  
- PostgreSQL (ou autre SGBD compatible SQLAlchemy)  
- Git  
- Navigateur pour accéder aux docs FastAPI et MLflow  

---

## 👤 Auteur

- **Salim MAJIDE**  
- Email : `salim.majide.officiel@gmail.com`  
- GitHub : [SalimM21]([https://github.com/votre-profil](https://github.com/SalimM21?tab=overview&from=2025-09-01&to=2025-09-02))
