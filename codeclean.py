from datetime import date, datetime, timedelta
from fastapi import Depends, FastAPI, Form, HTTPException, Request,Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
#from auth.jwt_handler import create_access_token
from database import SessionLocal, engine, Base
from models import Adherent, Livre, Emprunt, Reservation
from routes import 
from starlette.middleware.sessions import SessionMiddleware
from schemas import AdherentCreate, LivreCreate, EmpruntCreate, ReservationCreate
app = FastAPI()



# Ajoute le middleware de session avec une clé secrète
app.add_middleware(SessionMiddleware, secret_key="une_cle_secrete_tres_complexe")



# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

templates = Jinja2Templates(directory="templates")

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Pages HTML
# -----------------------------
#Inscription

@app.get("/api/register")
def show_register(request: Request):
    return templates.TemplateResponse("inscription.html", {"request": request})

#connection
@app.get("/api/login")
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

'''
@app.get("/home", response_class=HTMLResponse)
def show_home(request: Request, db: Session = Depends(get_db)):
    livres = db.query(Livre).all()
    return templates.TemplateResponse("home.html", {"request": request, "livres": livres})'''

# --- Route Home avec pagination ---
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    page: int = Query(1, ge=1),  # numéro de page (par défaut 1)
    db: Session = Depends(get_db)
):
    livres_par_page = 12  # nombre de livres par page

    # Compter le total des livres
    total_livres = db.query(Livre).count()

    # Calcul du nombre total de pages
    total_pages = (total_livres + livres_par_page - 1) // livres_par_page

    # Décalage pour pagination
    offset = (page - 1) * livres_par_page

    # Récupérer les livres paginés
    livres = db.query(Livre).offset(offset).limit(livres_par_page).all()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "livres": livres,
        "page": page,
        "total_pages": total_pages,
        "search":""
    })


# -----------------------------
# Routes API
# -----------------------------Inscription---------------------------------------------------

@app.post("/api/register")
def register_adherent(
    nom: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'email existe déjà
    existing_user = db.query(Adherent).filter(Adherent.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    hashed_password = pwd_context.hash(password)
    adherent = Adherent(nom=nom, email=email, password_hash=hashed_password)
    db.add(adherent)
    db.commit()
    db.refresh(adherent)
    return RedirectResponse(url="/api/login", status_code=302)

from fastapi import Form, Request
from fastapi.responses import RedirectResponse

@app.post("/api/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Vérifier l'utilisateur
    user = db.query(Adherent).filter(Adherent.email == email).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Identifiants incorrects"}
        )

    # Stocker l'email dans la session
    request.session["email"] = user.email

    # Redirection vers la page d'accueil
    return RedirectResponse(url="/profil", status_code=303)




'''
@app.post("/api/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
   # Vérifier l'utilisateur
    user = db.query(Adherent).filter(Adherent.email == email).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Identifiants incorrects")

    # Générer le token JWT
    token = create_access_token({"user_id": user.id, "role": user.role})

    # Redirection vers /home après connexion
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response '''


#-------------------------------------------------Route API pour récupérer les livres (avec recherche)--------------------------------------------

@app.get("/api/livres")
def get_livres(search: str = Query(default=""), db: Session = Depends(get_db)):
    query = db.query(Livre)
    if search:
        query = query.filter(Livre.title.ilike(f"%{search}%")).limit(4)  # Limite à 20 résultats
    livres = query.all()

    # Retourne les livres en JSON
    return [
        {
            "id": livre.id,
            "title": livre.title,
            "description": livre.description,
            "price": float(livre.price) if livre.price else None,
            "availability": livre.availability,
            "availability_num": livre.availability_num,
            "image_url": livre.image_url,
            "rating": livre.rating
        }
        for livre in livres
    ]


#------------------------------------------Route FastAPI pour la page catalogue--------------------------------------
'''
PER_PAGE = 20  # livres par page

@app.get("/catalogue", response_class=HTMLResponse)
def catalogue(request: Request, page: int = 1, search: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Livre)
    if search:
        query = query.filter(models.Livre.title.ilike(f"%{search}%")).limit(4)  # Limite à 20 résultats

    
    total_livres = query.count()
    total_pages = (total_livres + PER_PAGE - 1) // PER_PAGE

    livres = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return templates.TemplateResponse(
        "catalogue.html",
        {
            "request": request,
            "livres": livres,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )'''

PER_PAGE = 20  # livres par page

@app.get("/catalogue", response_class=HTMLResponse)
def catalogue(
    request: Request,
    page: int = 1,
    search: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(models.Livre)

    if search:
        # Filtrer par titre et retourner seulement le premier résultat correspondant
        query = query.filter(models.Livre.title.ilike(f"%{search}%"))
        total_livres = query.count()
        total_pages = 1  # Une seule page pour la recherche
        livres = query.limit(1).all()  # retourne uniquement 1 livre
    else:
        # Pagination normale si pas de recherche
        total_livres = query.count()
        total_pages = (total_livres + PER_PAGE - 1) // PER_PAGE
        livres = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return templates.TemplateResponse(
        "catalogue.html",
        {
            "request": request,
            "livres": livres,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )

#--------------------------------------------------------Route pour reserver un livre-----------------------------------



#----------------------------------------------Route pour afficher les détails d'un livre---------------------------------------
@app.get("/livre/{livre_id}", response_class=HTMLResponse)
def lire_livre(request: Request, livre_id: int, db: Session = Depends(get_db)):
    # Récupérer le livre depuis la base
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    # Retourner le template livre.html avec le livre
    return templates.TemplateResponse("livre.html", {"request": request, "livre": livre})

@app.get("/livre/")
def livre_default():
    return {"message": "Veuillez préciser l'id du livre."}

#--------------------------------------------------resever livre
'''
@app.post("/reserver/{livre_id}")
def reserver_livre(livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        # Redirection avec paramètre error
        return RedirectResponse(url=f"/livre/{livre_id}?error=notfound", status_code=303)
    
    if not livre.availability:
        # Livre déjà réservé
        return RedirectResponse(url=f"/livre/{livre_id}?error=reserved", status_code=303)
    
    # Réservation réussie
    livre.availability = False
    db.commit()
    return RedirectResponse(url=f"/livre/{livre_id}?success=1", status_code=303)'''
def get_current_user(db: Session = Depends(get_db)) -> Adherent:
    # Ici tu retournes juste le premier utilisateur pour test
    user = db.query(Adherent).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pas d'utilisateur trouvé")
    return user



@app.post("/reserver/{livre_id}")
def reserver_livre(
    livre_id: int,
    db: Session = Depends(get_db),
    current_user: Adherent = Depends(get_current_user)
):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        return RedirectResponse(url=f"/livre/{livre_id}?error=notfound", status_code=303)

    if not livre.availability:
        return RedirectResponse(url=f"/livre/{livre_id}?error=reserved", status_code=303)

    # Marquer le livre comme réservé
    livre.availability = False

    # Créer la réservation
    reservation = Reservation(
        id_adherent=current_user.id,
        id_livre=livre.id,
        date_reservation=datetime.utcnow(),
        statut="réservé"
    )
    db.add(reservation)
    db.commit()

    return RedirectResponse(url=f"/profil?success=1", status_code=303)


#----------------------------------------------Route pour afficher les réservations d'un utilisateur---------------------------------------


def get_current_adherent(request: Request, db: Session = Depends(get_db)):
    # Récupérer l'email de l'adhérent depuis la session (ou cookie)
    email = request.session.get("email")  # ex : stocké lors du login
    if not email:
        raise HTTPException(status_code=401, detail="Adhérent non authentifié")
    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    if not adherent:
        raise HTTPException(status_code=401, detail="Adhérent non trouvé")
    return adherent
    

#------------------------------------------------Route de reservation ----------------------------------

'''
from schemas import ReservationCreate
from models import Reservation as ReservationModel

@app.post("/api/reservations")
def reserver_livre(
    request: Request,
    id_livre: int = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l’utilisateur est connecté
    email = request.session.get("email")
    if not email:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "❌ Vous devez être connecté pour réserver."}
        )

    # Vérifier que l’adhérent existe
    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    if not adherent:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "❌ Adhérent introuvable. Veuillez créer un compte."}
        )

    # Vérifier que le livre existe
    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre:
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "error": "❌ Livre introuvable."}
        )

    # Vérifier disponibilité
    if not livre.availability:
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "error": "⚠️ Ce livre est déjà réservé."}
        )

    # Vérifier si déjà réservé par cet adhérent
    existing_reservation = db.query(ReservationModel).filter(
        ReservationModel.id_adherent == adherent.id,
        ReservationModel.id_livre == id_livre
    ).first()

    if existing_reservation:
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "error": "⚠️ Vous avez déjà réservé ce livre."}
        )

    # Créer une réservation
    reservation_data = ReservationCreate(
        id_adherent=adherent.id,
        id_livre=id_livre,
        date_reservation=datetime.utcnow(),
        statut="en cours"
    )

    reservation = ReservationModel(**reservation_data.dict())
    db.add(reservation)

    # Mettre le livre comme non disponible
    livre.availability = False
    db.commit()
    db.refresh(reservation)

    # ✅ Succès
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "success": "✅ Réservation réussie !"}
    )'''

from schemas import ReservationCreate
from models import Reservation  # SQLAlchemy model

'''
@app.post("/api/reservations")
def reserver_livre(request: Request, id_livre: int = Form(...), db: Session = Depends(get_db)):
    email = request.session.get("email")
    if not email:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Vous devez être connecté."})
    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre or not livre.availability:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Livre indisponible."})
    existing_emprunt = db.query(Emprunt).filter(Emprunt.id_adherent == adherent.id, Emprunt.id_livre == id_livre).first()
    if existing_emprunt:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Vous avez déjà réservé ce livre."})
    emprunt = Emprunt(
        id_adherent=adherent.id,
        id_livre=id_livre,
        date_emprunt=datetime.utcnow(),
        date_retour_prevue=datetime.utcnow() + timedelta(days=7),
        statut="En cours"
    )
    db.add(emprunt)
    livre.availability = False
    db.commit()
    db.refresh(emprunt)
    return RedirectResponse(url="/livre{livre_id}?success=1", status_code=303)'''

@app.post("/api/reservations")
def reserver_livre(
    request: Request,
    id_livre: int = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur est connecté
    email = request.session.get("email")
    if not email:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notlogged", status_code=303)

    # Récupérer l'adhérent
    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    if not adherent:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=303)

    # Récupérer le livre
    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=303)
    
    if not livre.availability:
        return RedirectResponse(url=f"/livre/{id_livre}?error=reserved", status_code=303)

    # Vérifier si l'adhérent a déjà réservé ce livre
    existing_emprunt = db.query(Emprunt).filter(
        Emprunt.id_adherent == adherent.id,
        Emprunt.id_livre == id_livre
    ).first()
    if existing_emprunt:
        return RedirectResponse(url=f"/livre/{id_livre}?error=already", status_code=303)

    # Créer l'emprunt
    emprunt = Emprunt(
        id_adherent=adherent.id,
        id_livre=id_livre,
        date_emprunt=datetime.utcnow(),
        date_retour_prevue=datetime.utcnow() + timedelta(days=7),
        statut="En cours"
    )
    db.add(emprunt)

    # Marquer le livre comme réservé
    livre.availability = False

    db.commit()
    db.refresh(emprunt)
    db.refresh(livre)

    # Redirection vers la page du livre avec message de succès
    return RedirectResponse(url=f"/livre/{id_livre}?success=1", status_code=303)

# ---------------------------
# Route Profil avec emprunts
# ---------------------------
@app.get("/profil", response_class=HTMLResponse)
def page_profil(request: Request, db: Session = Depends(get_db)):
    email = request.session.get("email")
    if not email:
        return RedirectResponse(url="/api/login", status_code=303)
    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    if not adherent:
        return RedirectResponse(url="/api/login", status_code=303)
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == adherent.id).all()
    result = []
    for e in emprunts:
        statut = "En retard" if e.date_retour_prevue < datetime.utcnow() else "À temps"
        result.append({
            "titre": e.livres.title,
            "date_emprunt": e.date_emprunt.strftime("%Y-%m-%d"),
            "date_retour_prevue": e.date_retour_prevue.strftime("%Y-%m-%d"),
            "statut": statut
        })
    return templates.TemplateResponse("profil.html", {
        "request": request,
        "adherent": adherent,
        "emprunts": result
    })



    

#----------------------------------------------Route FastAPI pour la page de recommandations par description---------------------------------------
'''
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# --- Charger les données
df = pd.read_csv("dataset/livres_bruts.csv")

# --- Charger vectorizer et matrice TF-IDF
import joblib

vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
cosine_sim = joblib.load("models/cosine_sim.pkl")


@app.get("/api/recommandation-par-description", response_class=HTMLResponse)
def form_page(request: Request):
    """Afficher le formulaire de recherche"""
    return templates.TemplateResponse("recommandation-par-description.html", {"request": request})

@app.post("/api/recommandation-par-description", response_class=HTMLResponse)
def recommander_par_description(request: Request, description: str = Form(...)):
    """Retourner les livres similaires à la description donnée"""
    # Transformer la description saisie
    desc_vec = vectorizer.transform([description])

    # Calculer similarité cosinus
    cosine_sim = cosine_similarity(desc_vec, cosine_sim).flatten()

    # Récupérer les 5 meilleurs résultats
    top_indices = cosine_sim.argsort()[-5:][::-1]
    suggestions = df.iloc[top_indices].to_dict(orient="records")

    return templates.TemplateResponse(
        "recommandation-par-description.html",
        {
            "request": request,
            "description": description,
            "suggestions": suggestions
        }
    )'''
#----------------------------------------------Route FastAPI pour la page de mes emprunts---------------------------------------

# ----- ROUTE : page profil -----

'''
@app.get("/profil", response_class=HTMLResponse)
def page_profil(request: Request, db: Session = Depends(get_db)):
    # Récupération de l'email depuis session ou cookie
    email = request.session.get("email")
    if not email:
        # redirige vers login si non connecté
        raise HTTPException(status_code=401, detail="Adhérent non connecté")

    adherent = db.query(Adherent).filter(Adherent.email == email).first()
    if not adherent:
        raise HTTPException(status_code=404, detail="Adhérent non trouvé")

    # Rendu du template avec les infos adhérent
    return templates.TemplateResponse("profil.html", {
        "request": request,
        "adherent": {
            "id": adherent.id,
            "nom": f"{adherent.nom}",
            "email": adherent.email,
            "role": adherent.role,
            "date_inscription": adherent.date_inscription.strftime("%Y-%m-%d")
        }
    })'''

# ----- ROUTE : récupérer les emprunts -----
@app.get("/api/mes-emprunts/{id_adherent}")
def get_emprunts(id_adherent: int, db: Session = Depends(get_db)):
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == id_adherent).all()
    result = []
    for e in emprunts:
        # Vérifier si retard
        statut = "En retard" if e.date_retour_prevue < datetime.utcnow() else "À temps"
        result.append({
            "titre": e.livres.title,
            "date_emprunt": e.date_emprunt.strftime("%Y-%m-%d"),
            "date_retour_prevue": e.date_retour_prevue.strftime("%Y-%m-%d"),
            "statut": statut
        })
    return result


    #get profil




@app.get("/profil/{id_adherent}", response_class=HTMLResponse)
def profil(id_adherent: int, request: Request, db: Session = Depends(get_db)):
    adherent = db.query(Adherent).filter(Adherent.id == id_adherent).first()
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == id_adherent).all()
    return templates.TemplateResponse("profil.html", {
        "request": request,
        "adherent": adherent,
        "emprunts": emprunts,
        "now": datetime.utcnow()
    })

#----------------------------------------------Route FastAPI pour la page de recommandations---------------------------------------
from recommendation import get_recommendations, recommend_by_description
import pandas as pd

df_livres = pd.read_csv("dataset/livres_bruts.csv") 
'''
@app.get("/recommandation/{title}", response_class=HTMLResponse)
def page_recommandation(request: Request, title: str, db: Session = Depends(get_db)):
    # Vérifier si le livre existe
    if title not in df_livres['title'].values:
        return templates.TemplateResponse("recommandation.html", {
            "request": request,
            "error": "Livre non trouvé"
        })
    # Obtenir les recommandations
    recommendations = get_recommendations(title)
    return templates.TemplateResponse("recommandation.html", {
        "request": request,
        "title": title,
        "recommendations": recommendations
    })'''


@app.get("/recommandation-par-description", response_class=HTMLResponse)
def page_recommandation(request: Request):
    return templates.TemplateResponse("recommandation-par-description.html", {"request": request})
'''
@app.get("/api/recommander-par-titre")
def recommander_par_titre(title: str, top_n: int = 5):
    results = recommendation.get_recommendations(title, top_n=top_n)
    return JSONResponse(content={"suggestions": results})


# Route: recommander à partir d'une description
@app.post("/api/recommander-par-description")
def recommander_par_description(description: str = Form(...), top_n: int = 5):
    results = recommendation.recommend_by_description(description, top_n=top_n)
    return JSONResponse(content={"suggestions": results})'''


@app.post("/api/recommandation-par-description", response_class=HTMLResponse)
def recommandation_par_description(
    request: Request,
    description: str = Form(...)
):
    # Obtenir les suggestions
    suggestions = recommend_by_description(description)

    # Rendre la même page avec les résultats
    return templates.TemplateResponse("recommandation-par-description.html", {
        "request": request,
        "suggestions": suggestions,
        "description": description
    })















#----------------------------------------------Route FastAPI pour la page de recommandations---------------------------------------
