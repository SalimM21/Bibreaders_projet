
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Query
from recommendations import get_recommendations, recommend_by_description
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["recommendation"])

templates = Jinja2Templates(directory="templates")


@router.get("/recommandation-par-description", response_class=HTMLResponse) 
def page_recommandation(request: Request):
    return templates.TemplateResponse("recommandation-par-description.html", {"request": request})

@router.post("/api/recommandation-par-description", response_class=HTMLResponse)
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





















