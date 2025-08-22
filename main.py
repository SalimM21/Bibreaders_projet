from datetime import date, datetime, timedelta
from fastapi import Depends, FastAPI, Form, HTTPException, Request,Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
#from auth.jwt_handler import create_access_token
from database import SessionLocal, engine, Base
from models import Adherent, Livre, Emprunt, Reservation
from starlette.middleware.sessions import SessionMiddleware
import models




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


# ----------------------------------- Route Home avec pagination ----------------------------------------------
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

#-----------------------------------Route pour afficher les détails d'un livre(bouton detail)---------------------------------------
@app.get("/livre/{livre_id}", response_class=HTMLResponse)
def lire_livre(request: Request, livre_id: int, db: Session = Depends(get_db)):
    # Récupérer le livre depuis la base
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    # Retourner le template livre.html avec le livre
    return templates.TemplateResponse("livre.html", {"request": request, "livre": livre})

from fastapi.responses import RedirectResponse

@app.get("/livre/")
def livre_default():
    # Rediriger vers le catalogue
    return RedirectResponse(url="/catalogue")


#----------------------------------------------Route pour reserver un livre---------------------------------------

#fonction pour obtenir l'utilisateur actuel (pour test, retourne le premier utilisateur)
def get_current_user(db: Session = Depends(get_db)) -> Adherent:
    # Ici tu retournes juste le premier utilisateur pour test
    user = db.query(Adherent).first()#tu peux changer par exemple en db.query(Adherent).filter(Adherent.username == "test").first()
    if not user:
        raise HTTPException(status_code=404, detail="Pas d'utilisateur trouvé")
    return user


#route pour reserver un livre
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
#----------------------------------------------Route FastAPI pour la page de mes emprunts---------------------------------------
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


#----------------------------------------------Route FastAPI pour la page de profil---------------------------------------

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

@app.get("/recommandation-par-description", response_class=HTMLResponse)
def page_recommandation(request: Request):
    return templates.TemplateResponse("recommandation-par-description.html", {"request": request})

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

#----------------------------------------------Route FastAPI pour la page de gestion des adherents---------------------------------------

# Affichage des adhérents
@app.get("/admin/gestion-adherents")
def gestion_adherents(request: Request, db: Session = Depends(get_db)):
    adherents = db.query(Adherent).all()
    return templates.TemplateResponse("admin/gestion-adherents.html", {"request": request, "adherents": adherents})

# Modifier un adhérent (affiche un formulaire)
@app.get("/modify/{id}")
def show_modify_form(id: int, request: Request, db: Session = Depends(get_db)):
    adherent = db.query(Adherent).filter(Adherent.id == id).first()
    return templates.TemplateResponse("admin/gestion-adherents.html", {"request": request, "adherent": adherent})

@app.post("/modify/{id}")
def modify_adherent(id: int, nom: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):
    adherent = db.query(Adherent).filter(Adherent.id == id).first()
    if adherent:
        adherent.nom = nom
        adherent.email = email
        db.commit()
    return RedirectResponse("/admin/gestion-adherents", status_code=303)

# Suspendre un adhérent
@app.get("/delete/{id}")
def suspend_adherent(id: int, db: Session = Depends(get_db)):
    adherent = db.query(Adherent).filter(Adherent.id == id).first()
    if adherent:
        adherent.statut = "Suspendu"
        db.commit()
    return RedirectResponse("/admin/gestion-adherents", status_code=303)

#======-------------ajouter un adherent
@app.get("/add-adherent", response_class=HTMLResponse)
def page_add_adherent(request: Request):
    return templates.TemplateResponse("admin/add-adherent.html", {"request": request})


@app.post("/api/adherents")
def creer_adherent(
    nom: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),   #  récupéré depuis formulaire
    db: Session = Depends(get_db)
):
    # Hachage du mot de passe
    hashed_password = pwd_context.hash(password)

    nouvel_adherent = Adherent(
        nom=nom,
        email=email,
        password_hash=hashed_password,
        role="adherent"
    )
    db.add(nouvel_adherent)
    db.commit()
    db.refresh(nouvel_adherent)
    return {"message": "Adhérent ajouté", "id": nouvel_adherent.id}

#-----------------------------------------------------------------route gestion des emprunts
@app.get("/admin/emprunts", response_class=HTMLResponse)
def page_emprunts(request: Request, db: Session = Depends(get_db)):
    adherents = db.query(Adherent).all()
    livres = db.query(Livre).all()
    emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()  # emprunts en cours
    return templates.TemplateResponse("admin/emprunts.html", {
        "request": request,
        "adherents": adherents,
        "livres": livres,
        "emprunts": emprunts
    })


@app.post("/api/emprunts")
def creer_emprunt(
    id_adherent: int = Form(...),
    id_livre: int = Form(...),
    db: Session = Depends(get_db)
):
    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre or livre.stock <= 0:
        return {"error": "Livre indisponible"}

    # Créer l'emprunt
    nouvel_emprunt = Emprunt(
        id_adherent=id_adherent,
        id_livre=id_livre,
        date_emprunt=datetime.utcnow(),
        date_retour_prevue=datetime.utcnow() + timedelta(days=14)
    )
    db.add(nouvel_emprunt)

    # Diminuer stock
    livre.stock -= 1

    db.commit()
    return {"message": "Emprunt enregistré avec succès"}

@app.post("/api/retours")
def retour_emprunt(
    id_emprunt: int = Form(...),
    db: Session = Depends(get_db)
):
    emprunt = db.query(Emprunt).filter(Emprunt.id == id_emprunt).first()
    if not emprunt:
        return {"error": "Emprunt introuvable"}

    # Marquer le retour
    emprunt.date_retour_effectif = datetime.utcnow()

    # Augmenter stock du livre
    livre = db.query(Livre).filter(Livre.id == emprunt.id_livre).first()
    if livre:
        livre.stock += 1

    db.commit()
    return {"message": "Retour enregistré avec succès"}
#---------------------------------ROUTES GESTION ADHERENTS ------------------------------------------------------


# 🔹 Route pour récupérer tous les adhérents
@app.get("/api/adherent")
def get_adherents(db: Session = Depends(get_db)):
    adherents = db.query(Adherent).all()
    result = []
    for a in adherents:
        result.append({
            "id": a.id,
            "nom": a.nom,
            # si tu as un champ prénom, tu peux l'ajouter ici
            # "prenom": a.prenom
        })
    return result

# 🔹 Route pour récupérer les livres disponibles (stock > 0)
@app.get("/api/livres-disponibles")
def get_livres_disponibles(db: Session = Depends(get_db)):
    livres = db.query(Livre).filter(Livre.availability_num > 0).all()
    result = []
    for l in livres:
        result.append({
            "id": l.id,
            "title": l.title,
            "stock": l.availability_num
        })
    return result

#  Route pour récupérer les emprunts en cours
@app.get("/api/emprunts-en-cours")
def get_emprunts_en_cours(db: Session = Depends(get_db)):
    emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()
    result = []
    for e in emprunts:
        result.append({
            "id": e.id,
            "livre_title": e.livre.title,
            "adherent_nom": e.adherent.nom
        })
    return result
