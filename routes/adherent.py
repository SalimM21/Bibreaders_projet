from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Adherent, Emprunt, Livre
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Vérification session adhérent
def check_adherent(request: Request):
    role = request.session.get("role")
    if role != "adherent":
        return False
    return True

# Dashboard adhérent / catalogue
@router.get("/catalogue", response_class=HTMLResponse)
def catalogue(request: Request, db: Session = Depends(get_db)):
    if not check_adherent(request):
        return HTMLResponse("Accès interdit", status_code=403)
    livres = db.query(Livre).all()
    return templates.TemplateResponse("catalogue.html", {"request": request, "livres": livres})

# Réserver un livre (exemple)
@router.post("/reserver/{livre_id}")
def reserver_livre(livre_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_adherent(request):
        return HTMLResponse("Accès interdit", status_code=403)
    
    livre = db.query(Livre).filter(Livre.id==livre_id).first()
    if livre and livre.availability_num > 0:
        livre.availability_num -= 1
        db.commit()
        return {"success": True, "message": f"Le livre '{livre.title}' a été réservé."}
    else:
        return {"success": False, "message": "Livre indisponible."}

# ---------------------------
# Route Profil avec emprunts
# ---------------------------
@router.get("/profil", response_class=HTMLResponse)
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
@router.get("/api/mes-emprunts/{id_adherent}")
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

@router.get("/profil/{id_adherent}", response_class=HTMLResponse)
def profil(id_adherent: int, request: Request, db: Session = Depends(get_db)):
    adherent = db.query(Adherent).filter(Adherent.id == id_adherent).first()
    emprunts = db.query(Emprunt).filter(Emprunt.id_adherent == id_adherent).all()
    return templates.TemplateResponse("profil.html", {
        "request": request,
        "adherent": adherent,
        "emprunts": emprunts,
        "now": datetime.utcnow()
    })