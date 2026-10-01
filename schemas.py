

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from clasificador import DESCRIPCION_URGENCIA


# ============================================================== ENTRADA ====


class TriajeEntrada(BaseModel):
    """Lo que la recepcionista contesta en el formulario del triaje."""

    motivo: str = Field(min_length=3, max_length=120)
    es_nino: bool = False
    hipertenso: bool = False
    diabetico: bool = False


class CitaCreate(BaseModel):
    

    recurso_id: int = Field(gt=0)
    usuario_id: int = Field(gt=0)
    inicio: datetime
    fin: datetime
    triaje: TriajeEntrada

    @model_validator(mode="after")
    def revisar_orden_del_periodo(self):
        if self.fin <= self.inicio:
            raise ValueError("fin debe ser posterior a inicio")
        return self

    @model_validator(mode="after")
    def revisar_zona_horaria(self):
        if self.inicio.tzinfo is None or self.fin.tzinfo is None:
            raise ValueError(
                
            )
        return self


# ============================================================== SALIDA =====


class RecursoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool


class TriajeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    motivo: str
    urgencia: str
    descripcion_urgencia: str
    es_nino: bool
    hipertenso: bool
    diabetico: bool

    @classmethod
    def desde_triaje(cls, triaje) -> "TriajeOut":
        """Construye la respuesta a partir de la fila de la base.

        'urgencia' viene GUARDADA (la calculo el clasificador al crear el
        triaje) y 'descripcion_urgencia' se arma AQUI, con las reglas del
        clasificador. Esa es la diferencia entre un dato y un dato derivado:
        el primero vive en la tabla, el segundo se calcula al responder, y
        por eso no puede quedar viejo.
        """
        return cls(
            id=triaje.id,
            motivo=triaje.motivo,
            urgencia=triaje.urgencia,
            descripcion_urgencia=DESCRIPCION_URGENCIA[triaje.urgencia],
            es_nino=triaje.es_nino,
            hipertenso=triaje.hipertenso,
            diabetico=triaje.diabetico,
        )

class CitaOut(BaseModel):
    """Una cita ya guardada, con su triaje adentro.

    En la base 'periodo' es UNA columna que es un rango. Aqui sale como dos
    fechas, porque para el cliente dos fechas si son dos datos.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    recurso_id: int
    usuario_id: int
    inicio: datetime
    fin: datetime
    estado: str
    creado_en: datetime
    triaje: TriajeOut

    @classmethod
    def desde_cita(cls, cita, triaje) -> "CitaOut":
        """Construye la respuesta a partir de las dos filas de la base.

        El truco del dia: 'periodo' es un tstzrange, y un rango tiene borde
        inferior y borde superior -> .lower es el inicio, .upper es el fin.
        Esa traduccion vive en esta fabrica y en ningun otro lado, para que
        los endpoints que listan citas no la repitan una vez por endpoint.
        """
        return cls(
            id=cita.id,
            recurso_id=cita.recurso_id,
            usuario_id=cita.usuario_id,
            inicio=cita.periodo.lower,
            fin=cita.periodo.upper,
            estado=cita.estado,
            creado_en=cita.creado_en,
            triaje=TriajeOut.desde_triaje(triaje),
        )


class UsuarioOut(BaseModel):
    """Un usuario de la clinica. NUNCA el password_hash.

    No hace falta acordarse de no devolverlo: el campo no esta declarado y
    Pydantic solo serializa lo declarado. Un schema de salida es la ultima
    linea de defensa contra filtrar un secreto por accidente.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nombre: str
    rol: str


# ============================================================== PRUEBAS =====
# Mismo estilo que en clasificador.py: casos, se corre el archivo, te dice
# que paso. Aqui todavia no hay base de datos, asi que 'desde_cita' se prueba
# con objetos falsos. Python no pide que sean de cierta clase: si el objeto
# tiene los atributos, sirve (eso se llama tipado pato / duck typing).

ZONA_CDMX = timezone(timedelta(hours=-6))

CASOS_VALIDOS = [
    (
        "cita normal de 10:00 a 11:00",
        {
            "recurso_id": 1,
            "usuario_id": 1,
            "inicio": "2026-09-25T10:00:00-06:00",
            "fin": "2026-09-25T11:00:00-06:00",
            "triaje": {"motivo": "Dolor de muela desde hace 3 dias"},
        },
    ),
]

CASOS_INVALIDOS = [
    (
        "fin antes de inicio",
        {
            "recurso_id": 1,
            "usuario_id": 1,
            "inicio": "2026-09-25T11:00:00-06:00",
            "fin": "2026-09-25T10:00:00-06:00",
            "triaje": {"motivo": "Limpieza dental"},
        },
    ),
    (
        "horarios sin zona horaria",
        {
            "recurso_id": 1,
            "usuario_id": 1,
            "inicio": "2026-09-25T10:00:00",
            "fin": "2026-09-25T11:00:00",
            "triaje": {"motivo": "Limpieza dental"},
        },
    ),
    (
        "motivo de una sola letra",
        {
            "recurso_id": 1,
            "usuario_id": 1,
            "inicio": "2026-09-25T10:00:00-06:00",
            "fin": "2026-09-25T11:00:00-06:00",
            "triaje": {"motivo": "x"},
        },
    ),
    (
        "recurso_id en cero",
        {
            "recurso_id": 0,
            "usuario_id": 1,
            "inicio": "2026-09-25T10:00:00-06:00",
            "fin": "2026-09-25T11:00:00-06:00",
            "triaje": {"motivo": "Limpieza dental"},
        },
    ),
]


if __name__ == "__main__":
    fallos = 0

    for nombre, datos in CASOS_VALIDOS:
        try:
            cita = CitaCreate(**datos)
        except ValidationError as error:
            fallos += 1
            print(f"FALLA {nombre}: se debia aceptar y se rechazo")
            print("       ", error)
        else:
            print(f"OK    {nombre}: {cita.inicio.isoformat()} -> {cita.fin.isoformat()}")

    for nombre, datos in CASOS_INVALIDOS:
        try:
            CitaCreate(**datos)
        except ValidationError as error:
            problema = error.errors()[0]
            print(f"OK    {nombre}: rechazado en {problema['loc']} -> {problema['msg']}")
        else:
            fallos += 1
            print(f"FALLA {nombre}: se debia rechazar y se acepto")

    # Objetos falsos con los mismos atributos que tendrian las filas de la
    # base. Nada de SQL: aqui solo se prueba el contrato.
    cita_falsa = SimpleNamespace(
        id=7,
        recurso_id=1,
        usuario_id=1,
        estado="reservada",
        periodo=SimpleNamespace(
            lower=datetime(2026, 9, 25, 10, 0, tzinfo=ZONA_CDMX),
            upper=datetime(2026, 9, 25, 11, 0, tzinfo=ZONA_CDMX),
        ),
        creado_en=datetime(2026, 9, 24, 18, 30, tzinfo=timezone.utc),
    )
    triaje_falso = SimpleNamespace(
        id=3,
        motivo="Dolor de muela desde hace 3 dias",
        urgencia="alta",
        es_nino=False,
        hipertenso=False,
        diabetico=False,
    )

    salida = CitaOut.desde_cita(cita_falsa, triaje_falso)
    if (
        salida.inicio.hour == 10
        and salida.fin.hour == 11
        and salida.triaje.urgencia == "alta"
    ):
        print(
            f"OK    desde_cita: {salida.inicio.isoformat()} -> {salida.fin.isoformat()}"
        )
    else:
        fallos += 1
        print(f"FALLA desde_cita: {salida}")

    print()
    print("Asi se vera la cita en la respuesta de la API:")
    print(salida.model_dump_json(indent=2))
    print()
    print(f"{fallos} fallo(s)")




            