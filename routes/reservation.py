
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from database import get_db
from models import Adherent, User, Livre, Emprunt, Reservation

router = APIRouter(tags=["reservation"])

templates = Jinja2Templates(directory="templates")



# Fonction utilitaire pour récupérer l'utilisateur de la session
def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
    """
    Récupère l'objet utilisateur (Adherent) à partir de l'email stocké dans la session.
    """
    email = request.session.get("email")
    if not email:
        return None
    # J'ai mis Adherent au lieu de User pour correspondre à votre code
    user = db.query(User).filter(User.email == email).first()
    return user

# ---------------------------
# Route pour la réservation d'un livre
# ---------------------------
@router.post("/api/reservations", response_class=RedirectResponse)
def create_reservation(request: Request, id_livre: int = Form(...), db: Session = Depends(get_db)):
    """
    Gère la création d'une nouvelle réservation pour un livre.
    Cette route est appelée lorsque l'utilisateur clique sur le bouton "Réserver".
    """
    # 1. Vérifier si l'utilisateur est connecté
    user = get_current_user_from_session(request, db)
    if not user:
        # Redirection avec un message d'erreur si l'utilisateur n'est pas connecté
        return RedirectResponse(url=f"/livre/{id_livre}?error=notlogged", status_code=status.HTTP_303_SEE_OTHER)

    # 2. Récupérer les informations du livre
    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre:
        # Redirection si le livre n'existe pas
        return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=status.HTTP_303_SEE_OTHER)
    
    # 3. Vérifier si le livre est disponible pour la réservation
    if not livre.availability:
        return RedirectResponse(url=f"/livre/{id_livre}?error=reserved", status_code=status.HTTP_303_SEE_OTHER)

    # 4. Vérifier si l'utilisateur a déjà une réservation ou un emprunt en cours pour ce livre
    existing_reservation = db.query(Reservation).filter(
        Reservation.id_adherent == user.id,
        Reservation.id_livre == id_livre
    ).first()
    
    existing_emprunt = db.query(Emprunt).filter(
        Emprunt.id_adherent == user.id,
        Emprunt.id_livre == id_livre,
        Emprunt.date_retour_effectif == None
    ).first()

    if existing_reservation or existing_emprunt:
        return RedirectResponse(url=f"/livre/{id_livre}?error=already", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # 5. Créer la réservation
        new_reservation = Reservation(
            id_adherent=user.id,
            id_livre=livre.id,
            date_reservation=date.today()
        )
        db.add(new_reservation)
        
        # 6. Mettre à jour la disponibilité du livre
        livre.availability = False
        db.commit()
        
        # 7. Redirection avec un message de succès
        return RedirectResponse(url=f"/livre/{id_livre}?success=true", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # Gérer les erreurs et revenir en arrière si quelque chose se passe mal
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réservation : {str(e)}")

































'''
def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
    email = request.session.get("email")
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()

@router.post("/api/reservation")
def reserver_livre(
    request: Request,
    id_livre: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_session(request, db)
    if not user:
        # Si pas connecté → reste sur la page livre
        return RedirectResponse(url=f"/livre/{id_livre}?error=notlogged", status_code=status.HTTP_303_SEE_OTHER)

    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=status.HTTP_303_SEE_OTHER)

    if livre.availability_num <= 0:
        return RedirectResponse(url=f"/livre/{id_livre}?error=reserved", status_code=status.HTTP_303_SEE_OTHER)

    # Vérifier si déjà réservé
    existing = db.query(Reservation).filter(
        Reservation.id_adherent == user.id,
        Reservation.id_livre == id_livre
    ).first()
    if existing:
        return RedirectResponse(url=f"/livre/{id_livre}?error=already", status_code=status.HTTP_303_SEE_OTHER)

    # Créer la réservation
    reservation = Reservation(
        id_adherent=user.id,
        id_livre=id_livre,
        date_reservation=datetime.utcnow(),
        statut="réservé"
    )
    db.add(reservation)
    livre.availability_num -= 1
    db.commit()

    return RedirectResponse(url=f"/livre/{id_livre}?success=true", status_code=status.HTTP_303_SEE_OTHER)'''


# Route pour gérer la réservation d'un livre
'''
@router.post("/api/reservations")
def reserver_livre(
    request: Request,
    id_livre: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Route pour gérer la réservation d'un livre.
    """
    user = get_current_user_from_session(request, db)
    if not user:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notlogged", status_code=status.HTTP_303_SEE_OTHER)

    livre = db.query(Livre).filter(Livre.id == id_livre).first()
    if not livre:
        return RedirectResponse(url=f"/livre/{id_livre}?error=notfound", status_code=status.HTTP_303_SEE_OTHER)
    
    # Vérifier si l'adhérent a déjà réservé ce livre
    existing_reservation = db.query(Reservation).filter(
        Reservation.id_adherent == user.id,
        Reservation.id_livre == id_livre
    ).first()
    if existing_reservation:
        return RedirectResponse(url=f"/livre/{id_livre}?error=already_reserved", status_code=status.HTTP_303_SEE_OTHER)

    # Créer la réservation
    reservation = Reservation(
        id_adherent=user.id,
        id_livre=id_livre,
        date_reservation=datetime.now()
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return RedirectResponse(url=f"/profil?success=reservation_ok", status_code=status.HTTP_303_SEE_OTHER)'''



#route pour reserver un livre
'''
@router.post("/reserver/{livre_id}")
def reserver_livre(
    livre_id: int,
    db: Session = Depends(get_db),
    current_user: Adherent = Depends(get_current_user_from_session)
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

    return RedirectResponse(url=f"/profil?success=1", status_code=303)'''




























# Route pour gérer la suppression d'une réservation
@router.get("/profil", response_class=HTMLResponse)
def page_profil(request: Request, db: Session = Depends(get_db)):
    """
    Affiche la page de profil de l'adhérent avec ses emprunts.
    """
    user = get_current_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Récupérer tous les emprunts de l'utilisateur
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == user.id).all()
    
    # Préparer les données pour le template, en ajoutant le statut
    emprunts_formatted = []
    for emprunt in emprunts:
        # Assurez-vous d'avoir une relation 'livre' dans votre modèle Emprunt
        livre = emprunt.livre if hasattr(emprunt, 'livre') else None
        
        statut = "À temps"
        is_late = False
        if emprunt.date_retour_effectif is None and emprunt.date_retour_prevue < date.today():
            statut = "En retard"
            is_late = True

        emprunts_formatted.append({
            "titre_livre": livre.titre if livre else "Titre inconnu",
            "date_emprunt": emprunt.date_emprunt,
            "date_retour_prevue": emprunt.date_retour_prevue,
            "statut": statut,
            "is_late": is_late
        })
    
    return templates.TemplateResponse("profil.html", {
        "request": request,
        "adherent": user,
        "emprunts": emprunts_formatted
    })

