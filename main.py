from datetime import date, datetime, timedelta
from typing import List
from urllib import request
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal, engine, Base
from models import Adherent, Livre, Emprunt, Reservation,User
from starlette.middleware.sessions import SessionMiddleware
import models
from schemas import AdherentCreate, LivreBase, LivreCreate, StatistiquesResponse
import schemas
import secrets
from routes import auth, admin, adherent, livres, home, recommendation, reservation



app = FastAPI()

# Ajoute le middleware de session avec une clé secrète
secret_key = secrets.token_hex(32)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Inclure les routeurs
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(adherent.router)
app.include_router(livres.router)
app.include_router(home.router)
app.include_router(recommendation.router)
app.include_router(reservation.router)

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Configuration du contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration des templates Jinja2
templates = Jinja2Templates(directory="templates")

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
       db.close()


#----------------------------------------------Route pour reserver un livre---------------------------------------

#fonction pour obtenir l'utilisateur actuel (pour test, retourne le premier utilisateur)
# '''
# def get_current_user(db: Session = Depends(get_db)) -> Adherent:
#     # Ici tu retournes juste le premier utilisateur pour test
#     user = db.query(Adherent).first()#tu peux changer par exemple en db.query(Adherent).filter(Adherent.username == "test").first()
#     if not user:
#         raise HTTPException(status_code=404, detail="Pas d'utilisateur trouvé")
#     return user


# #route pour reserver un livre
# @app.post("/reserver/{livre_id}")
# def reserver_livre(
#     livre_id: int,
#     db: Session = Depends(get_db),
#     current_user: Adherent = Depends(get_current_user)
# ):
#     livre = db.query(Livre).filter(Livre.id == livre_id).first()
#     if not livre:
#         return RedirectResponse(url=f"/livre/{livre_id}?error=notfound", status_code=303)

#     if not livre.availability:
#         return RedirectResponse(url=f"/livre/{livre_id}?error=reserved", status_code=303)

#     # Marquer le livre comme réservé
#     livre.availability = False

#     # Créer la réservation
#     reservation = Reservation(
#         id_adherent=current_user.id,
#         id_livre=livre.id,
#         date_reservation=datetime.utcnow(),
#         statut="réservé"
#     )
#     db.add(reservation)
#     db.commit()

#     return RedirectResponse(url=f"/profil?success=1", status_code=303)


# #----------------------------------------------Route pour afficher les réservations d'un utilisateur---------------------------------------

# @app.post("/api/reservations")
# def reserver_livre(
#     request: Request,
#     id_livre: int = Form(...),
#     db: Session = Depends(get_db)
# ):
#     # Vérifier si l'utilisateur est connecté
#     email = request.session.get("email")
#     if not email:
#         return RedirectResponse(url=f"/livre/{id_livre}?error=notlogged", status_code=303)

#     # Récupérer l'adhérent
#     adherent = db.query(Adherent).filter(Adherent.email == email).first()
#     if not adherent:
#         return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=303)

#     # Récupérer le livre
#     livre = db.query(Livre).filter(Livre.id == id_livre).first()
#     if not livre:
#         return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=303)
    
#     if not livre.availability:
#         return RedirectResponse(url=f"/livre/{id_livre}?error=reserved", status_code=303)

#     # Vérifier si l'adhérent a déjà réservé ce livre
#     existing_emprunt = db.query(Emprunt).filter(
#         Emprunt.id_adherent == adherent.id,
#         Emprunt.id_livre == id_livre
#     ).first()
#     if existing_emprunt:
#         return RedirectResponse(url=f"/livre/{id_livre}?error=already", status_code=303)

#     # Créer l'emprunt
#     emprunt = Emprunt(
#         id_adherent=adherent.id,
#         id_livre=id_livre,
#         date_emprunt=datetime.utcnow(),
#         date_retour_prevue=datetime.utcnow() + timedelta(days=7),
#         statut="En cours"
#     )
#     db.add(emprunt)

#     # Marquer le livre comme réservé
#     livre.availability = False

#     db.commit()
#     db.refresh(emprunt)
#     db.refresh(livre)

#     # Redirection vers la page du livre avec message de succès
#     return RedirectResponse(url=f"/livre/{id_livre}?success=1", status_code=303)

# # ---------------------------
# # Route Profil avec emprunts
# # ---------------------------
# @app.get("/profil", response_class=HTMLResponse)
# def page_profil(request: Request, db: Session = Depends(get_db)):
#     email = request.session.get("email")
#     if not email:
#         return RedirectResponse(url="/api/login", status_code=303)
#     adherent = db.query(Adherent).filter(Adherent.email == email).first()
#     if not adherent:
#         return RedirectResponse(url="/api/login", status_code=303)
#     emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == adherent.id).all()
#     result = []
#     for e in emprunts:
#         statut = "En retard" if e.date_retour_prevue < datetime.utcnow() else "À temps"
#         result.append({
#             "titre": e.livres.title,
#             "date_emprunt": e.date_emprunt.strftime("%Y-%m-%d"),
#             "date_retour_prevue": e.date_retour_prevue.strftime("%Y-%m-%d"),
#             "statut": statut
#         })
#     return templates.TemplateResponse("profil.html", {
#         "request": request,
#         "adherent": adherent,
#         "emprunts": result
#     })
# #----------------------------------------------Route FastAPI pour la page de mes emprunts---------------------------------------
# # ----- ROUTE : récupérer les emprunts -----
# @app.get("/api/mes-emprunts/{id_adherent}")
# def get_emprunts(id_adherent: int, db: Session = Depends(get_db)):
#     emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == id_adherent).all()
#     result = []
#     for e in emprunts:
#         # Vérifier si retard
#         statut = "En retard" if e.date_retour_prevue < datetime.utcnow() else "À temps"
#         result.append({
#             "titre": e.livres.title,
#             "date_emprunt": e.date_emprunt.strftime("%Y-%m-%d"),
#             "date_retour_prevue": e.date_retour_prevue.strftime("%Y-%m-%d"),
#             "statut": statut
#         })
#     return result


# #----------------------------------------------Route FastAPI pour la page de profil---------------------------------------

# @app.get("/profil/{id_adherent}", response_class=HTMLResponse)
# def profil(id_adherent: int, request: Request, db: Session = Depends(get_db)):
#     adherent = db.query(Adherent).filter(Adherent.id == id_adherent).first()
#     emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == id_adherent).all()
#     return templates.TemplateResponse("profil.html", {
#         "request": request,
#         "adherent": adherent,
#         "emprunts": emprunts,
#         "now": datetime.utcnow()
#     })'''


# #----------------------------------------------Route FastAPI pour la page de gestion des adherents---------------------------------------
# # 1️⃣ Route pour obtenir tous les adhérents

# '''
# @app.get("/admin/gestion-adherents", response_class=HTMLResponse)
# def get_gestion_adherents_page(request: Request, db: Session = Depends(get_db)):
#     # Récupérer tous les adhérents pour les passer au template
#     adherents = db.query(Adherent).all()
#     return templates.TemplateResponse(
#         "admin/gestion-adherents.html", 
#         {
#             "request": request, 
#             "adherents": adherents
#         }
#     )

# # 1️⃣ API pour modifier un adhérent
# # --------------------------------------------
# # Utilisation de la méthode PUT pour une modification

# @app.put("/api/adherents/modify/{adherent_id}")
# def modify_adherent(adherent_id: int, nom: str, email: str, db: Session = Depends(get_db)):
#     """
#     Modifie le nom et l'email d'un adhérent par son ID.
#     """
#     adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
#     if not adherent:
#         raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
#     adherent.nom = nom
#     adherent.email = email
    
#     db.commit()
#     db.refresh(adherent)
    
#     return {"message": f"Adhérent ID {adherent_id} modifié avec succès."}


# # --------------------------------------------
# # 2️⃣ API pour suspendre ou réactiver un adhérent
# # --------------------------------------------
# # Utilisation de la méthode POST pour une action
# @app.post("/api/adherents/suspend/{adherent_id}")
# def suspend_adherent(adherent_id: int, db: Session = Depends(get_db)):
#     """
#     Change le rôle d'un adhérent entre 'adherent' et 'suspendu'.
#     """
#     adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
#     if not adherent:
#         raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
#     # Inverser le rôle de l'adhérent
#     if adherent.role == "adherent":
#         adherent.role = "suspendu"
#     else:
#         adherent.role = "adherent"
    
#     db.commit()
#     db.refresh(adherent)
    
#     return {"message": f"Statut de l'adhérent ID {adherent_id} mis à jour en '{adherent.role}'."}

# # --------------------------------------------
# # 3️⃣ API pour supprimer (désactiver) un adhérent
# # --------------------------------------------
# # Utilisation de la méthode DELETE pour la suppression logique
# @app.delete("/api/adherents/delete/{adherent_id}")
# def delete_adherent(adherent_id: int, db: Session = Depends(get_db)):
#     """
#     "Supprime" logiquement un adhérent en changeant son rôle en 'supprimé'.
#     """
#     adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
#     if not adherent:
#         raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
#     adherent.role = "supprimé"
    
#     db.commit()
#     db.refresh(adherent)
    
#     return {"message": f"Adhérent ID {adherent_id} a été logiquement supprimé (rôle 'supprimé')."}

# # --------------------------------------------
# # 4️⃣ API pour obtenir un adhérent par son ID
# # --------------------------------------------
# @app.get("/api/adherents/{adherent_id}")
# def get_adherent(adherent_id: int, db: Session = Depends(get_db)):
#     """
#     Récupère les informations d'un adhérent par son ID.
#     """
#     adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
#     if not adherent:
#         raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
#     return adherent





# #-----------------------------------------------------------------route gestion des emprunts
# #-----------------------------------------------
# # Route 1️⃣ : Affiche la page HTML pour la gestion des emprunts
# @app.get("/admin/emprunts", response_class=HTMLResponse)
# def page_emprunts(request: Request, db: Session = Depends(get_db)):
#     """
#     Affiche la page HTML en passant les données directement au template.
#     Cette approche est simple, mais pour une API, il est souvent préférable de laisser
#     le frontend faire des appels asynchrones.
#     """
#     adherents = db.query(Adherent).all()
#     livres = db.query(Livre).filter(Livre.availability_num > 0).all()
#     emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()

#     return templates.TemplateResponse("admin/emprunts.html", {
#         "request": request,
#         "adherents": adherents,
#         "livres": livres,
#         "emprunts": emprunts
#     })

# # 1️⃣ Page HTML pour la gestion des emprunts
# # --------------------------------------------
# @app.get("/admin/emprunts", response_class=HTMLResponse)
# def page_emprunts(request: Request, db: Session = Depends(get_db)):
#     adherents = db.query(Adherent).all()
#     livres = db.query(Livre).filter(Livre.availability_num > 0).all()
#     emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()

#     return templates.TemplateResponse("admin/emprunts.html", {
#         "request": request,
#         "adherents": adherents,
#         "livres": livres,
#         "emprunts": emprunts
#     })

# # --------------------------------------------
# # 2️⃣ API pour enregistrer un nouvel emprunt
# # --------------------------------------------
# @app.post("/api/emprunts")
# def creer_emprunt(
#     adherent_id: int = Form(...),
#     livre_id: int = Form(...),
#     db: Session = Depends(get_db)
# ):
#     livre = db.query(Livre).filter(Livre.id == livre_id).first()
#     if not livre or livre.availability_num <= 0:
#         raise HTTPException(status_code=400, detail="Livre indisponible")

#     nouvel_emprunt = Emprunt(
#         id_adherent=adherent_id,
#         id_livre=livre_id,
#         date_emprunt=datetime.utcnow(),
#         date_retour_prevue=datetime.utcnow() + timedelta(days=14)
#     )
#     db.add(nouvel_emprunt)
#     livre.availability_num -= 1
#     db.commit()
#     db.refresh(nouvel_emprunt)

#     return {"message": "Emprunt enregistré avec succès"}

# # --------------------------------------------
# # 3️⃣ API pour enregistrer un retour
# # --------------------------------------------
# @app.post("/api/retours")
# def retour_emprunt(
#     emprunt_id: int = Form(...),
#     db: Session = Depends(get_db)
# ):
#     emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
#     if not emprunt:
#         raise HTTPException(status_code=404, detail="Emprunt introuvable")

#     if emprunt.date_retour_effectif is not None:
#         raise HTTPException(status_code=400, detail="Cet emprunt a déjà été retourné")

#     emprunt.date_retour_effectif = datetime.utcnow()
#     livre = db.query(Livre).filter(Livre.id == emprunt.id_livre).first()
#     if livre:
#         livre.availability_num += 1

#     db.commit()
#     return {"message": "Retour enregistré avec succès"}

# # --------------------------------------------
# # 4️⃣ API pour récupérer les adhérents
# # --------------------------------------------
# @app.get("/api/adherents")
# def get_adherents(db: Session = Depends(get_db)):
#     adherents = db.query(Adherent).all()
#     return [{"id": a.id, "nom": a.nom} for a in adherents]

# # --------------------------------------------
# # 5️⃣ API pour récupérer les livres disponibles
# # --------------------------------------------
# @app.get("/api/livres-disponibles")
# def get_livres_disponibles(db: Session = Depends(get_db)):
#     livres = db.query(Livre).filter(Livre.availability_num > 0).all()
#     return [{"id": l.id, "title": l.title, "availability_num": l.availability_num} for l in livres]

# # --------------------------------------------
# # 6️⃣ API pour récupérer les emprunts en cours
# # --------------------------------------------
# @app.get("/api/emprunts-en-cours")
# def get_emprunts_en_cours(db: Session = Depends(get_db)):
#     emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()
    
#     return [{
#         "id": e.id,
#         "livre_title": e.livre.title,
#         "adherent_nom": e.adherent.nom
#     } for e in emprunts]

# # --------------------------------------------
# # 7️⃣ API pour consulter un livre par son ID
# # --------------------------------------------
# @app.get("/api/livres/{livre_id}")
# def get_livre_by_id(livre_id: int, db: Session = Depends(get_db)):
#     livre = db.query(Livre).filter(Livre.id == livre_id).first()
#     if not livre:
#         raise HTTPException(status_code=404, detail="Livre non trouvé")
    
#     return {
#         "id": livre.id,
#         "title": livre.title,
#         "description": livre.description,
#         "availability_num": livre.availability_num
#     }

# # 🆕 Route ajoutée pour les emprunts d'un adhérent spécifique
# @app.get("/api/emprunts/adherent/{adherent_id}")
# def get_emprunts_by_adherent(adherent_id: int, db: Session = Depends(get_db)):
#     """
#     Récupère la liste des emprunts pour un adhérent donné.
#     """
#     emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == adherent_id).all()
#     return [{
#         "id": e.id,
#         "livre_title": e.livre.title,
#         "date_emprunt": e.date_emprunt,
#         "date_retour_prevue": e.date_retour_prevue,
#         "date_retour_effectif": e.date_retour_effectif
#     } for e in emprunts]'''





# # -----------------------
# # ROUTES POUR LES LIVRES
# # -----------------------
# '''
# @app.get("/admin/statistiques", response_class=HTMLResponse, summary="Page d'administration des statistiques")
# def admin_stats_page(request: Request):
#     return templates.TemplateResponse("admin/statistiques.html", {"request": request})

# @app.get("/admin/gestion-livres", response_class=HTMLResponse, summary="Page d'administration des livres")
# def admin_books_page(request: Request):
#     return templates.TemplateResponse("admin/gestion-livres.html", {"request": request})

# # -------------------------
# # Routes API Livres
# # -------------------------
# @app.get("/api/livres", response_model=List[schemas.LivreResponse], summary="Récupérer tous les livres")
# def get_livres(db: Session = Depends(get_db)):
#     return db.query(models.Livre).all()

# @app.post("/api/livres", response_model=schemas.LivreResponse, status_code=status.HTTP_201_CREATED, summary="Ajouter un nouveau livre")
# def add_livre(livre_data: schemas.LivreCreate, db: Session = Depends(get_db)):
#     new_livre = models.Livre(**livre_data.dict())
#     db.add(new_livre)
#     db.commit()
#     db.refresh(new_livre)
#     return new_livre

# @app.get("/api/livres/{livre_id}", response_model=schemas.LivreResponse, summary="Récupérer un livre par ID")
# def get_livre_par_id(livre_id: int, db: Session = Depends(get_db)):
#     livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
#     if livre is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
#     return livre

# @app.put("/api/livres/{livre_id}", response_model=schemas.LivreResponse, summary="Mettre à jour un livre")
# def update_livre(livre_id: int, livre_data: schemas.LivreCreate, db: Session = Depends(get_db)):
#     livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
#     if livre is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
#     for field, value in livre_data.dict(exclude_unset=True).items():
#         setattr(livre, field, value)
#     db.commit()
#     db.refresh(livre)
#     return livre

# @app.delete("/api/livres/{livre_id}", status_code=status.HTTP_200_OK, summary="Supprimer un livre")
# def delete_livre(livre_id: int, db: Session = Depends(get_db)):
#     livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
#     if livre is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livre non trouvé.")
#     db.delete(livre)
#     db.commit()
#     return {"message": "Livre supprimé avec succès."}

# # -------------------------
# # Routes statistiques API
# # -------------------------
# @app.get("/api/statistiques", response_model=schemas.StatistiquesResponse, summary="Obtenir les statistiques de la bibliothèque")
# def get_statistiques(db: Session = Depends(get_db)):
#     top_livres = db.query(
#         models.Livre.titre.label("title"),
#         func.count(models.Emprunt.id).label("emprunts")
#     ).join(models.Emprunt).group_by(models.Livre.id).order_by(func.count(models.Emprunt.id).desc()).limit(5).all()

#     top_livres_list = [{"title": l.title, "emprunts": l.emprunts} for l in top_livres]

#     total_books = db.query(models.Livre).count() or 1
#     total_available_books = db.query(models.Livre).filter(models.Livre.availability_num > 0).count()
#     taux_disponibilite = (total_available_books / total_books) * 100

#     nombre_retards = db.query(models.Emprunt).filter(
#         and_(
#             models.Emprunt.date_retour_effectif.is_(None),
#             models.Emprunt.date_retour_prevue < datetime.now()
#         )
#     ).count()

#     return {
#         "top_livres_empruntes": top_livres_list,
#         "taux_disponibilite": taux_disponibilite,
#         "nombre_retards": nombre_retards,
#     }'''