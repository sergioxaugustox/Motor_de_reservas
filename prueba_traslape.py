"""Prueba en vivo del motor de reservas: 8 etapas contra la base real."""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import Cita, Recurso, Triaje, Usuario


def rango(h1, m1, h2, m2):
    """Periodo [inicio, fin) del 12-oct-2026 en UTC."""
    inicio = datetime(2026, 10, 12, h1, m1, tzinfo=timezone.utc)
    fin = datetime(2026, 10, 12, h2, m2, tzinfo=timezone.utc)
    return Range(inicio, fin)


db = SessionLocal()