from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional,ClassVar
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, engine
from database import Base



# ---------------------
# Adherent
# ---------------------
class AdherentBase(BaseModel):
    nom: str
    email: EmailStr


class AdherentCreate(AdherentBase):
    """Schéma utilisé lors de la création d'un adhérent (POST)."""
    pass


class Adherent(AdherentBase):
    """Schéma utilisé pour la lecture/retour (GET)."""
    id: int
    date_inscription: datetime = datetime.now()

    class Config:
        #orm_mode = True
        from_attributes = True




# ---------------------
# Livre
# ---------------------
class LivreBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    availability: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[int] = None
    availability_num: Optional[int] = None


class LivreCreate(LivreBase):
    """Schéma utilisé pour la création d’un livre (POST)."""
    pass


class Livre(LivreBase):
    """Schéma utilisé pour la lecture/retour (GET)."""
    id: int

    class Config:
        #orm_mode = True
        from_attributes = True



class LivreResponse(LivreBase):
    id: int

    class Config:
        #orm_mode = True
        from_attributes = True
        
# ---------------------
# Reservation
# ---------------------
class ReservationBase(BaseModel):
    id_adherent: int
    id_livre: int
    date_reservation: datetime
    statut: str


class ReservationCreate(ReservationBase):
    """Schéma utilisé pour la création d’une réservation (POST)."""
    pass


class Reservation(ReservationBase):
    """Schéma utilisé pour la lecture/retour (GET)."""
    id: int

    class Config:
        #orm_mode = True
        from_attributes = True







from pydantic import BaseModel
from typing import List

class TopLivre(BaseModel):
    title: str
    emprunts: int

class StatistiquesResponse(BaseModel):
    top_livres_empruntes: List[TopLivre]
    taux_disponibilite: float
    nombre_retards: int








   
# class LivreCreate(BaseModel):
#     title: str
#     description: Optional[str] = None
#     price: Optional[float] = None
#     availability: Optional[str] = None
#     image_url: Optional[str] = None
#     rating: Optional[int] = None
#     availability_num: Optional[int] = None

#     class Config:
#         orm_mode = True 
#         allow_population_by_field_name = True
#         use_enum_values = True
#         json_encoders = {
#             datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
#         }
#         schema_extra = {
#             "example": {
#                 "title": "Example Book",
#                 "description": "This is an example book description.",  
#                 "price": 19.99,
#                 "availability": "In Stock",
#                 "image_url": "http://example.com/image.jpg",
#                 "rating": 5,
#                 "availability_num": 10
#             }
#         }
# class LivreUpdate(BaseModel):
    # title: Optional[str] = None
    # description: Optional[str] = None
    # price: Optional[float] = None
    # availability: Optional[str] = None
    # image_url: Optional[str] = None
    # rating: Optional[int] = None
    # availability_num: Optional[int] = None
    # class Config:
    #     orm_mode = True
    #     allow_population_by_field_name = True
    #     use_enum_values = True
    #     json_encoders = {
    #         datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v 
    #     }
    #     schema_extra = {
    #         "example": {
    #             "title": "Updated Book Title",
    #             "description": "Updated description for the book.",
    #             "price": 24.99,
    #             "availability": "Out of Stock",
    #             "image_url": "http://example.com/updated_image.jpg",
    #             "rating": 4,
    #             "availability_num": 0
    #         }
    #     }

