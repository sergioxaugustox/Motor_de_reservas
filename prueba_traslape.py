"""Prueba en vivo del motor de reservas: 8 etapas contra la base real."""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, func, select
from database import SessionLocal
from models import Cita, Recurso, Triaje, Usuario


def rango(h1, m1, h2, m2):
    """Periodo [inicio, fin) del 12-oct-2026 en UTC."""
    inicio = datetime(2026, 10, 12, h1, m1, tzinfo=timezone.utc)
    fin = datetime(2026, 10, 12, h2, m2, tzinfo=timezone.utc)
    return Range(inicio, fin)


def insertar(cita):
    """Intenta guardar una cita. Devuelve 'OK id=N' o 'RECHAZADA <codigo>'."""
    db.add(cita)
    try:
        db.commit()
        return f"OK id={cita.id}"
    except IntegrityError as e:
        db.rollback()
        return f"RECHAZADA {e.orig.pgcode}"

def limpiar():
    """ borra TODO en las 4 tablas (hijos -> padres) y devuelve el conteo. SOLO base de pruebas"""
    for modelo in (Triaje, Cita, Recurso, Usuario):
        db.execute(delete(modelo))
    db.commit()
    return [db.scalar(select(func.count()).select_from(m)) for m in (Usuario, Recurso, Cita, Triaje)]

db = SessionLocal()   
print("Limpieza inicial:", limpiar())

#datos de prueba
usuario = Usuario(email="test@test.com", password_hash ="no-es-un-hash", nombre="Dra prueba")
recurso = Recurso(nombre="Consultorio prueba")
db.add_all([usuario, recurso])
db.commit()
print("setup = usuario", usuario.id, "| recurso", recurso.id)

# --- Etapa 1: cita base 10:00-11:00 (debe pasar) ---
cita_base = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(10, 0, 11, 0))
db.add(cita_base)
db.commit()
print("Etapa 1 OK: cita", cita_base.id, "|", cita_base.estado, "|", cita_base.periodo)
# --- Etapa 2: traslape 10:30-11:30 (debe rechazarse con 23P01) ---
traslape = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(10, 30, 11, 30))
print("Etapa 2:", insertar(traslape))

# --- Etapa 3: caso límite 11:00-12:00 (debe pasar: bounds [) ) ---
limite = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(11, 0, 12, 0))
print("Etapa 3:", insertar(limite))

# --- Etapa 4: cancelar la cita base libera su horario ---
cita_base.estado = "cancelada"
db.commit()
print("Etapa 4a: cita", cita_base.id, "->", cita_base.estado)
reinsercion = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(10, 30, 11, 0))
print("Etapa 4b:", insertar(reinsercion))

# --- Etapa 5: dos canceladas que se traslapan no chocan ---
cancelada_a = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(14, 0, 15, 0), estado="cancelada")
cancelada_b = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(14, 30, 15, 30), estado="cancelada")
print("Etapa 5a:", insertar(cancelada_a))
print("Etapa 5b:", insertar(cancelada_b))

# --- Etapa 6: estado fuera de la lista blanca (debe rechazarse con 23514) ---
invalida = Cita(recurso_id=recurso.id, usuario_id=usuario.id, periodo=rango(16, 0, 17, 0), estado="pendiente")
print("Etapa 6:", insertar(invalida))

# --- Eyapa 7: Triaje 1:1 con la cita del caso limite, la urgencia se guarda y se relee ---
triaje = Triaje(cita_id=limite.id, motivo="Dolor intenso en la muela", urgencia= "alta", hipertenso = True)
db.add(triaje)
db.commit()
db.refresh(triaje)
print("Etapa 7: triaje", triaje.id, "| cita", triaje.cita_id,"| urgencia", triaje.urgencia, "| hipertenso", triaje.hipertenso, "| es_nino", triaje.es_nino) 

# --- Etapa 8: limpieza final (la base queda como la encontramos) ---
print("Etapa 8: limpieza final", limpiar())

db.close()
