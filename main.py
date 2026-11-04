from fastapi import FastAPI

app = FastAPI(
    title="Motor de reservas",
    description="API de citas para clinicas dentales: el traslape lo impide la base de datos.",
    version="0.1.0",
    
)


@app.get("/salud")
def salud():
    return {"estado": "ok"}