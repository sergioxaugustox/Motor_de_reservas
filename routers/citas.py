from fastapi import APIRouter

from schemas import CitaCreate

router = APIRouter(prefix="/citas", tags=["citas"])


@router.post("", status_code=201)
def crear_cita(datos: CitaCreate):
    return {"recibido": datos.model_dump(mode="json")}