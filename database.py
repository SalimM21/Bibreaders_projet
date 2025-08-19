import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse
import os
from sqlalchemy.orm import sessionmaker, declarative_base


# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Encoder le mot de passe pour l'URL
# password_encoded = urllib.parse.quote_plus(DB_PASSWORD)

# Créer la chaîne de connexion PostgreSQL
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Créer l'engine SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Création de la table si elle n’existe pas
create_table_sql = """
CREATE TABLE IF NOT EXISTS livres (
    id INT SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(6,2),
    availability VARCHAR(100),
    image_URL TEXT,
    rating INT,
    availability_num INT
)
"""

# ===============================
# 4. Importer le CSV avec Pandas
# ===============================

#df = pd.read_csv('dataset/livres_bruts.csv') 

# Renommer les colonnes
'''
df.rename(columns={
    'Title': 'title',
    'Description': 'description',
    'Price': 'price',
    'Availability': 'availability',
    'Image_URL': 'image_url',
    'Rating': 'rating',
    'availability_num': 'availability_num'
}, inplace=True)'''


# ===============================
# 5. Insérer les données en base
# ===============================

#df.to_sql("livres", con=engine, if_exists="append", index=False)

