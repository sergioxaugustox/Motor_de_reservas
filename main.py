from fastapi import FastAPI
from routers import citas

app = FastAPI(
    title="Motor de reservas",
    description="API de citas para clinicas dentales: el traslape lo impide la base de datos.",
    version="0.1.0",
)

app.include_router(citas.router)


@app.get("/salud")
def salud():
    return {"estado": "ok"}