from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates
from sqlalchemy import func
from database import get_db
from models import Livre, Emprunt, Reservation, User, Adherent
import models


router = APIRouter(tags=["admin"])

templates = Jinja2Templates(directory="templates")

# Fonction utilitaire pour vérifier l'authentification admin
def check_admin_auth(request: Request):
    """
    Vérifie si l'utilisateur est un administrateur authentifié.
    """
    return request.session.get("role") == "admin"

# Route pour le tableau de bord admin
@router.get("/admin/dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    # Vérifie l'authentification de l'administrateur
    if not check_admin_auth(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Récupérer les 5 livres les plus empruntés
        # On sélectionne le titre du Livre et on compte les emprunts
        top_livres_query = db.query(
            Livre.title,
            func.count(Emprunt.id).label('emprunt_count')
        ).join(Emprunt).group_by(Livre.id).order_by(func.count(Emprunt.id).desc()).limit(5)
        
        # Formater les résultats en une liste de dictionnaires pour le graphique
        top_livres_data = [
            {"titre": title, "count": count}
            for title, count in top_livres_query.all()
        ]

        # Calculer le taux de disponibilité des livres
        total_livres = db.query(Livre).count()
        livres_empruntes = db.query(Emprunt).filter(Emprunt.date_retour_prevue.is_(None)).count()
        
        # Éviter la division par zéro si aucun livre n'est enregistré
        if total_livres > 0:
            taux_disponibilite = ((total_livres - livres_empruntes) / total_livres) * 100
        else:
            taux_disponibilite = 0

        # Préparer les données pour le rendu du template
        data = {
            "request": request,
            "top_livres": top_livres_data,
            "taux_disponibilite": taux_disponibilite,
            "admin_name": request.session.get("email") # Vous pouvez utiliser le nom si c'est disponible
        }
        
        # Retourner le template avec les données
        return templates.TemplateResponse("admin/dashboard.html", data)

    except Exception as e:
        # En cas d'erreur, affichez-la dans la console pour le débogage
        print(f"Erreur lors du rendu du tableau de bord admin: {e}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue.")

# Route pour vérifier si l'utilisateur est un administrateur
@router.get("/admin/dashboard")
def check_admin(request: Request):
    """
    Vérifie si l'utilisateur est un administrateur authentifié.
    """
    if request.session.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return True


#----------------------------------------------Route FastAPI pour la page de gestion des adherents---------------------------------------
# 1 Route pour obtenir tous les adhérents

@router.get("/admin/gestion-adherents", response_class=HTMLResponse)
def get_gestion_adherents_page(request: Request, db: Session = Depends(get_db)):
    # Récupérer tous les adhérents pour les passer au template
    adherents = db.query(Adherent).all() 
    return templates.TemplateResponse(
        "admin/gestion-adherents.html", 
        {
            "request": request, 
            "adherents": adherents
        }
    )


# Utilisation de la méthode PUT pour une modification

@router.put("/api/adherents/modify/{adherent_id}")
def modify_adherent(adherent_id: int, nom: str, email: str, db: Session = Depends(get_db)):
    """
    Modifie le nom et l'email d'un adhérent par son ID.
    """
    adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()# Récupérer l'adhérent par son ID
    if not adherent:
        raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
    adherent.nom = nom
    adherent.email = email
    
    db.commit()
    db.refresh(adherent)
    
    return {"message": f"Adhérent ID {adherent_id} modifié avec succès."}


# --------------------------------------------
# 2 API pour suspendre ou réactiver un adhérent
# --------------------------------------------
# Utilisation de la méthode POST pour une action
@router.post("/api/adherents/suspend/{adherent_id}")
def suspend_adherent(adherent_id: int, db: Session = Depends(get_db)):
    """
    Change le rôle d'un adhérent entre 'adherent' et 'suspendu'.
    """
    adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
    if not adherent:
        raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
    # Inverser le rôle de l'adhérent
    if adherent.role == "adherent":
        adherent.role = "suspendu"
    else:
        adherent.role = "adherent"
    
    db.commit()
    db.refresh(adherent)
    
    return {"message": f"Statut de l'adhérent ID {adherent_id} mis à jour en '{adherent.role}'."}

# --------------------------------------------
# 3 API pour supprimer (désactiver) un adhérent
# --------------------------------------------
# Utilisation de la méthode DELETE pour la suppression logique
@router.delete("/api/adherents/delete/{adherent_id}")
def delete_adherent(adherent_id: int, db: Session = Depends(get_db)):
    """
    "Supprime" logiquement un adhérent en changeant son rôle en 'supprimé'.
    """
    adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
    if not adherent:
        raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
    adherent.role = "supprimé"
    
    db.commit()
    db.refresh(adherent)
    
    return {"message": f"Adhérent ID {adherent_id} a été logiquement supprimé (rôle 'supprimé')."}

# --------------------------------------------
# 4 API pour obtenir un adhérent par son ID
# --------------------------------------------
@router.get("/api/adherents/{adherent_id}")
def get_adherent(adherent_id: int, db: Session = Depends(get_db)):
    """
    Récupère les informations d'un adhérent par son ID.
    """
    adherent = db.query(models.Adherent).filter(models.Adherent.id == adherent_id).first()
    if not adherent:
        raise HTTPException(status_code=404, detail="Adhérent non trouvé")
    
    return adherent





#----------------------------------------------Route gestion des emprunts---------------------------------
# Route 1 : Affiche la page HTML pour la gestion des emprunts
@router.get("/admin/emprunts", response_class=HTMLResponse)
def page_emprunts(request: Request, db: Session = Depends(get_db)):
    """
    Affiche la page HTML en passant les données directement au template.
    Cette approche est simple, mais pour une API, il est souvent préférable de laisser
    le frontend faire des appels asynchrones.
    """
    adherents = db.query(Adherent).all()
    livres = db.query(Livre).filter(Livre.availability_num > 0).all()
    emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()

    return templates.TemplateResponse("admin/emprunts.html", {
        "request": request,
        "adherents": adherents,
        "livres": livres,
        "emprunts": emprunts
    })

# 1 Page HTML pour la gestion des emprunts
# --------------------------------------------
@router.get("/admin/emprunts", response_class=HTMLResponse)
def page_emprunts(request: Request, db: Session = Depends(get_db)):
    adherents = db.query(Adherent).all()
    livres = db.query(Livre).filter(Livre.availability_num > 0).all()
    emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()

    return templates.TemplateResponse("admin/emprunts.html", {
        "request": request,
        "adherents": adherents,
        "livres": livres,
        "emprunts": emprunts
    })

# --------------------------------------------
# 2 API pour enregistrer un nouvel emprunt
# --------------------------------------------
@router.post("/api/emprunts")
def creer_emprunt(
    adherent_id: int = Form(...),
    livre_id: int = Form(...),
    db: Session = Depends(get_db)
):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre or livre.availability_num <= 0:
        raise HTTPException(status_code=400, detail="Livre indisponible")

    nouvel_emprunt = Emprunt(
        id_adherent=adherent_id,
        id_livre=livre_id,
        date_emprunt=datetime.utcnow(),
        date_retour_prevue=datetime.utcnow() + timedelta(days=14)
    )
    db.add(nouvel_emprunt)
    livre.availability_num -= 1
    db.commit()
    db.refresh(nouvel_emprunt)

    return {"message": "Emprunt enregistré avec succès"}

# --------------------------------------------
# 3 API pour enregistrer un retour
# --------------------------------------------
@router.post("/api/retours")
def retour_emprunt(
    emprunt_id: int = Form(...),
    db: Session = Depends(get_db)
):
    emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt introuvable")

    if emprunt.date_retour_effectif is not None:
        raise HTTPException(status_code=400, detail="Cet emprunt a déjà été retourné")

    emprunt.date_retour_effectif = datetime.utcnow()
    livre = db.query(Livre).filter(Livre.id == emprunt.id_livre).first()
    if livre:
        livre.availability_num += 1

    db.commit()
    return {"message": "Retour enregistré avec succès"}

# --------------------------------------------
# 4 API pour récupérer les adhérents
# --------------------------------------------
@router.get("/api/adherents")
def get_adherents(db: Session = Depends(get_db)):
    adherents = db.query(Adherent).all()
    return [{"id": a.id, "nom": a.nom} for a in adherents]

# --------------------------------------------
# 5 API pour récupérer les livres disponibles
# --------------------------------------------
@router.get("/api/livres-disponibles")
def get_livres_disponibles(db: Session = Depends(get_db)):
    livres = db.query(Livre).filter(Livre.availability_num > 0).all()
    return [{"id": l.id, "title": l.title, "availability_num": l.availability_num} for l in livres]

# --------------------------------------------
# 6 API pour récupérer les emprunts en cours
# --------------------------------------------
@router.get("/api/emprunts-en-cours")
def get_emprunts_en_cours(db: Session = Depends(get_db)):
    emprunts = db.query(Emprunt).filter(Emprunt.date_retour_effectif == None).all()
    
    return [{
        "id": e.id,
        "livre_title": e.livre.title,
        "adherent_nom": e.adherent.nom
    } for e in emprunts]

# --------------------------------------------
# 7 API pour consulter un livre par son ID
# --------------------------------------------
@router.get("/api/livres/{livre_id}")
def get_livre_by_id(livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return {
        "id": livre.id,
        "title": livre.title,
        "description": livre.description,
        "availability_num": livre.availability_num
    }

#  Route ajoutée pour les emprunts d'un adhérent spécifique
@router.get("/api/emprunts/adherent/{adherent_id}")
def get_emprunts_by_adherent(adherent_id: int, db: Session = Depends(get_db)):
    """
    Récupère la liste des emprunts pour un adhérent donné.
    """
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == adherent_id).all()
    return [{
        "id": e.id,
        "livre_title": e.livre.title,
        "date_emprunt": e.date_emprunt,
        "date_retour_prevue": e.date_retour_prevue,
        "date_retour_effectif": e.date_retour_effectif
    } for e in emprunts]





# -----------------------
# ROUTES POUR LES LIVRES
# -----------------------
'''
@router.get("/admin/statistiques", response_class=HTMLResponse, summary="Page d'administration des statistiques")
def admin_stats_page(request: Request):
    return templates.TemplateResponse("admin/statistiques.html", {"request": request})

@router.get("/admin/gestion-livres", response_class=HTMLResponse, summary="Page d'administration des livres")
def admin_books_page(request: Request):
    return templates.TemplateResponse("admin/gestion-livres.html", {"request": request})

# -------------------------
# Routes API Livres
# -------------------------
@router.get("/api/livres", response_model=List[schemas.LivreResponse], summary="Récupérer tous les livres")
def get_livres(db: Session = Depends(get_db)):
    return db.query(models.Livre).all()

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
    }'''


# Gestion livres
@router.get("/admin/gestion-livres", response_class=HTMLResponse)
def gestion_livres(request: Request, db: Session = Depends(get_db)):
    if not check_admin(request):
        return check_admin(request)
    livres = db.query(Livre).all()
    return templates.TemplateResponse("admin/gestion-livres.html", {"request": request, "livres": livres})

# Gestion emprunts
@router.get("/admin/emprunts", response_class=HTMLResponse)
def gestion_emprunts(request: Request, db: Session = Depends(get_db)):
    if not check_admin(request):
        return check_admin(request)
    emprunts = db.query(Emprunt).all()
    return templates.TemplateResponse("admin/emprunts.html", {"request": request, "emprunts": emprunts})

# Gestion adhérents
@router.get("/admin/gestion-adherents", response_class=HTMLResponse)
def gestion_adherents(request: Request, db: Session = Depends(get_db)):
    if not check_admin(request):
        return check_admin(request)
    adherents = db.query(User).filter(User.role=="adherent").all()
    return templates.TemplateResponse("admin/gestion-adherents.html", {"request": request, "adherents": adherents})
