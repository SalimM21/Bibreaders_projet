from datetime import date, datetime, timedelta
from typing import List
from urllib import request
from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from streamlit import status
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

#route pour gerer la pagination et recherche en meme temps 
@router.get("/", response_class=HTMLResponse)
@router.get("/home", response_class=HTMLResponse)
def home(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db)
):
    livres_par_page = 12
    query = db.query(Livre)

    # Filtre par titre si recherche
    if search:
        query = query.filter(Livre.title.ilike(f"%{search}%"))

    total_livres = query.count()
    total_pages = max((total_livres + livres_par_page - 1) // livres_par_page, 1)
    offset = (page - 1) * livres_par_page

    livres = query.offset(offset).limit(livres_par_page).all()

    livres_data = [
        {
            "id": l.id,
            "title": l.title,
            "availability_num": l.availability_num,
            "image_url": l.image_url or "/static/images/interfaces/carte_template.png"
        }
        for l in livres
    ]

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "livres": livres_data,
            "page": page,
            "total_pages": total_pages,
            "search": search
        }
    )
