
from fastapi import APIRouter, Depends, Query, Form, HTTPException
from datetime import date, datetime, timedelta
from typing import List
from urllib import request
from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from passlib.context import CryptContext
#from auth.jwt_handler import create_access_token
from database import SessionLocal, engine, Base, get_db
from models import Adherent, Livre, Emprunt, Reservation,User
from starlette.middleware.sessions import SessionMiddleware
import models
from schemas import AdherentCreate, LivreBase, LivreCreate, StatistiquesResponse
import schemas
import secrets


router = APIRouter()
templates = Jinja2Templates(directory="templates")


#-----------------------------------Route pour afficher le catalogue de livres (avec pagination et recherche)---------------------------------------

@router.get("/catalogue", response_class=HTMLResponse)
def catalogue(
    request: Request,
    page: int = Query(1, ge=1),        # Page minimum = 1
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db)
):
    PER_PAGE = 20

    # Sélection uniquement des colonnes utiles
    query = db.query(
        Livre.id,
        Livre.title,
        Livre.description,
        Livre.price,
        Livre.availability_num,
        Livre.image_url
    )

    # Filtre si recherche
    #query = query.filter(Livre.title.isnot(None))
    if search:
        query = query.filter(Livre.title.ilike(f"%{search}%"))

    total_livres = query.count()
    total_pages = max((total_livres + PER_PAGE - 1) // PER_PAGE, 1)

    # Pagination
    livres = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    # Conversion en dictionnaire pour Jinja
    livres_data = [
        {
            "id": l.id,
            "title": l.title,
            "description": l.description or "Pas de description",
            "price": l.price,
            "availability_num": l.availability_num,
            "image_url": l.image_url or "/static/images/interfaces/carte_template.png"
        }
        for l in livres
    ]

    return templates.TemplateResponse(
        "catalogue.html",
        {
            "request": request,
            "livres": livres_data,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )








#-----------------------------------Route pour afficher les détails d'un livre(bouton detail)---------------------------------------

@router.get("/livre/{livre_id}", response_class=HTMLResponse)
def lire_livre(request: Request, livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    return templates.TemplateResponse(
        "livre.html",
        {"request": request, "livre": livre}
    )



#-------------------------------------------------Route API pour récupérer les livres (avec recherche)--------------------------------------------

@router.get("/api/livres")
def get_livres(search: str = Query(default=""), db: Session = Depends(get_db)):#, limit: int = Query(default=20, le=50)
    # Requête de base pour récupérer les livres
    #query = query.filter(Livre.title.isnot(None))
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
            "availability_num": livre.availability_num,
            "image_url": livre.image_url,
            "rating": livre.rating
        }
        for livre in livres# Retourne seulement les 20 premiers résultats
    ]


# Redirection de /livre/ vers /catalogue
# @router.get("/livre/")
# def livre_default():
#     return RedirectResponse(url="/catalogue")














#-------------------------------------------Route gestion de livres et d'emprunts pour les adhérents--------------------------------------------
# -----------------------
# ROUTES POUR LES LIVRES
# -----------------------

@router.get("/admin/statistiques", response_class=HTMLResponse, summary="Page d'administration des statistiques")
def admin_stats_page(request: Request):
    return templates.TemplateResponse("admin/statistiques.html", {"request": request})

@router.get("/admin/gestion-livres", response_class=HTMLResponse, summary="Page d'administration des livres")
def admin_books_page(request: Request):
    return templates.TemplateResponse("admin/gestion-livres.html", {"request": request})

# -------------------------
# Routes API Livres
# -------------------------
# @router.get("/api/livres", response_model=List[schemas.LivreResponse], summary="Récupérer tous les livres")
# def get_livres(db: Session = Depends(get_db)):
#     return db.query(models.Livre).all()

@router.post("/api/livres", response_model=schemas.LivreResponse, status_code=status.HTTP_201_CREATED, summary="Ajouter un nouveau livre")
def add_livre(livre_data: schemas.LivreCreate, db: Session = Depends(get_db)):
    new_livre = models.Livre(**livre_data.dict())
    db.add(new_livre)
    db.commit()
    db.refresh(new_livre)
    return new_livre

@router.get("/api/livres/{livre_id}", response_model=schemas.LivreResponse, summary="Récupérer un livre par ID")
def get_livre_par_id(livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if livre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
    return livre

@router.put("/api/livres/{livre_id}", response_model=schemas.LivreResponse, summary="Mettre à jour un livre")
def update_livre(livre_id: int, livre_data: schemas.LivreCreate, db: Session = Depends(get_db)):
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if livre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
    for field, value in livre_data.dict(exclude_unset=True).items():
        setattr(livre, field, value)
    db.commit()
    db.refresh(livre)
    return livre

@router.delete("/api/livres/{livre_id}", status_code=status.HTTP_200_OK, summary="Supprimer un livre")
def delete_livre(livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if livre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
    db.delete(livre)
    db.commit()
    return {"message": "Livre supprimé avec succès."}

# -------------------------
# Routes statistiques API
# -------------------------
@router.get("/api/statistiques", response_model=schemas.StatistiquesResponse, summary="Obtenir les statistiques de la bibliothèque")
def get_statistiques(db: Session = Depends(get_db)):
    top_livres = db.query(
        models.Livre.titre.label("title"),
        func.count(models.Emprunt.id).label("emprunts")
    ).join(models.Emprunt).group_by(models.Livre.id).order_by(func.count(models.Emprunt.id).desc()).limit(5).all()

    top_livres_list = [{"title": l.title, "emprunts": l.emprunts} for l in top_livres]

    total_books = db.query(models.Livre).count() or 1
    total_available_books = db.query(models.Livre).filter(models.Livre.availability_num > 0).count()
    taux_disponibilite = (total_available_books / total_books) * 100

    nombre_retards = db.query(models.Emprunt).filter(
        and_(
            models.Emprunt.date_retour_effectif.is_(None),
            models.Emprunt.date_retour_prevue < datetime.now()
        )
    ).count()

    return {
        "top_livres_empruntes": top_livres_list,
        "taux_disponibilite": taux_disponibilite,
        "nombre_retards": nombre_retards,
    }















