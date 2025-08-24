from fastapi import APIRouter, Form, Request, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette.templating import Jinja2Templates
from database import SessionLocal, get_db
from models import User

router = APIRouter()

# Initialisation du contexte de hachage de mot de passe
# 'bcrypt' est l'algorithme recommandé.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

templates = Jinja2Templates(directory="templates")

# Fonction pour hacher un mot de passe
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Fonction pour vérifier un mot de passe
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Route pour afficher la page de connexion (GET)
@router.get("/login")
def show_login(request: Request):
    # Récupère le message d'erreur s'il est dans la session
    error = request.session.get("error")
    # Supprime le message d'erreur de la session pour ne pas l'afficher à nouveau
    if error:
        del request.session["error"]
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

# Route pour afficher la page d'inscription (GET)
@router.get("/register")
def show_register(request: Request):
    return templates.TemplateResponse("inscription.html", {"request": request})

# Route pour traiter la connexion (POST)
@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Recherche l'utilisateur par email dans la base de données
    user = db.query(User).filter(User.email == email).first()

    # Vérifie si l'utilisateur existe et si le mot de passe est correct
    if user and verify_password(password, user.password_hash):
        # Si la connexion est réussie, stocke l'email et le rôle dans la session
        request.session["email"] = user.email # Stocke l'email dans la session
        request.session["role"] = user.role  # Stocke le rôle dans la session

        # Redirige l'utilisateur en fonction de son rôle
        if user.role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER) # Redirige vers le tableau de bord admin 
        else:
            return RedirectResponse(url="/catalogue", status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Si la connexion échoue, stocke un message d'erreur et redirige
        request.session["error"] = "Identifiants incorrects."
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# Route pour traiter l'inscription (POST)
@router.post("/register")
def register(nom: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        # Lève une exception si l'email est déjà utilisé
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà utilisé.")
    
    # Hache le mot de passe avant de le stocker
    hashed_password = hash_password(password)
    
    new_user = User(nom=nom, email=email, password_hash=hashed_password, role="adherent")
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# --- ROUTE TEMPORAIRE POUR CRÉER UN COMPTE ADMINISTRATEUR ---
@router.post("/create-admin-account")
def create_admin_account(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Route temporaire pour créer un compte administrateur.
    À utiliser une seule fois et à supprimer ensuite.
    """
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="L'utilisateur existe déjà.")
    
    hashed_password = pwd_context.hash(password)
    
    new_admin = User(
        nom="Admin", 
        email=email, 
        password_hash=hashed_password, 
        role="admin"
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {"message": "Compte administrateur créé avec succès !", "email": new_admin.email}


def create_admin_user(email: str, password: str, db: Session):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print("Erreur : Un utilisateur avec cet email existe déjà.")
        return

    hashed_password = hash_password(password)
    new_admin = User(
        nom="SuperAdmin", 
        email=email, 
        password_hash=hashed_password, 
        role="admin"
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    print(f"Compte administrateur pour '{email}' créé avec succès.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Remplacez l'email et le mot de passe ci-dessous
        create_admin_user("nouvel.admin@gmail.com", "votre_mot_de_passe_super_secret", db)
    finally:
        db.close()

#route de deconnexion
@router.get("/logout")
def logout_get(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


