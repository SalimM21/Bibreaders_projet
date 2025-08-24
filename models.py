# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Adherent(Base):
    __tablename__ = "adherents"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default="adherent")
    date_inscription = Column(DateTime, default=datetime.utcnow)

    # Relations
    emprunts = relationship("Emprunt", back_populates="adherent")
    reservations = relationship("Reservation", back_populates="adherent")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)  # mot de passe haché
    role = Column(String)  # "admin" ou "adherent"

class Livre(Base):
    __tablename__ = "livres"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(6, 2))
    availability = Column(String(100))
    image_url = Column(Text)
    rating = Column(Integer)
    availability_num = Column(Integer)

    # Relations
    emprunts = relationship("Emprunt", back_populates="livre")
    reservations = relationship("Reservation", back_populates="livre")


class Emprunt(Base):
    __tablename__ = "emprunts"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    id_adherent = Column(Integer, ForeignKey("adherents.id"))
    id_livre = Column(Integer, ForeignKey("livres.id"))
    date_emprunt = Column(DateTime, default=datetime.utcnow)
    date_retour_prevue = Column(DateTime)
    date_retour_effectif = Column(DateTime, nullable=True)

    adherent = relationship("Adherent", back_populates="emprunts")
    livre = relationship("Livre", back_populates="emprunts")


class Reservation(Base):
    __tablename__ = "reservations"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    id_adherent = Column(Integer, ForeignKey("adherents.id"))
    id_livre = Column(Integer, ForeignKey("livres.id"))
    date_reservation = Column(DateTime, default=datetime.utcnow)
    statut = Column(String(50))

    adherent = relationship("Adherent", back_populates="reservations")
    livre = relationship("Livre", back_populates="reservations")


class HistoriqueEmprunt(Base):
    __tablename__ = "historique_emprunts"
    __allow_unmapped__ = True

    id_adherent = Column(Integer, ForeignKey("adherents.id"), primary_key=True)
    id_livre = Column(Integer, ForeignKey("livres.id"), primary_key=True)
    note = Column(Integer)
    date_emprunt = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    id_adherent = Column(Integer, ForeignKey("adherents.id"))
    message = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    lu = Column(Boolean, default=False)


