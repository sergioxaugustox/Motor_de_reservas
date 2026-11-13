from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from schemas import CitaCreate

from clasificador import clasificar
from database import get_db
from models import Cita, Triaje
from schemas import CitaCreate, CitaOut

router = APIRouter(prefix="/citas", tags=["citas"])


@router.post("", status_code=201, response_model=CitaOut)
def crear_cita(datos: CitaCreate, db: Session = Depends(get_db)):
    urgencia = clasificar(
        datos.triaje.motivo,
        es_nino=datos.triaje.es_nino,
        hipertenso=datos.triaje.hipertenso,
        diabetico=datos.triaje.diabetico,
    )
    cita = Cita(
        recurso_id=datos.recurso_id,
        usuario_id=datos.usuario_id,
        periodo=Range(datos.inicio, datos.fin),
    )
    try:
        db.add(cita)
        db.flush()
        triaje = Triaje(
            cita_id=cita.id,
            motivo=datos.triaje.motivo,
            urgencia=urgencia,
            es_nino=datos.triaje.es_nino,
            hipertenso=datos.triaje.hipertenso,
            diabetico=datos.triaje.diabetico,
        )
        db.add(triaje)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        codigo = e.orig.pgcode
        if codigo == "23P01":
            raise HTTPException(
                status_code=409,
                detail="Ese horario ya esta ocupado en este consultorio",
            )
        if codigo == "23503":
            raise HTTPException(
                status_code=422,
                detail="El consultorio o el paciente no existe",
            )
        if codigo == "23514":
            raise HTTPException(
                status_code=422,
                detail=f"Valor no permitido ({e.orig.diag.constraint_name})",
            )
        raise
    db.refresh(cita)
    db.refresh(triaje)
    return CitaOut.desde_cita(cita, triaje)    
        
