"""
Clasificador de urgencia odontologica.

REGLA DE ORO DEL PROYECTO: este archivo es el UNICO lugar donde viven las
reglas de triaje. Si manana la clinica cambia su politica, se cambia AQUI
y ningun endpoint se entera.

Es una funcion PURA: entra texto + banderas, sale texto.
Sin base de datos, sin red, sin FastAPI. Por eso se puede probar sola
en el REPL y con tests sin montar nada.
"""
import unicodedata


BAJA = "baja"
MEDIA = "media"
ALTA = "alta"
URGENTE = "urgente"

NIVELES = (BAJA, MEDIA, ALTA, URGENTE)

PALABRAS_URGENTE = (
    "espontaneo",
    "nocturno",
    "despierta de noche",
    "no puedo dormir",
    "throbbing",
    "trauma",
    "golpe",
    "accidente",
    "fractura",
    "hinchazon",
    "fiebre",
    "sangrado abundante",
    "no puedo abrir la boca",
)

PALABRAS_ALTA = (
    "dolor de muela",
    "dolor de diente",
    "dolor dental",
    "masticar",
    "sensibilidad",
    "caries profunda",
    "absceso",
    "infeccion",
    "gingivitis",
    "sangrado de encias",
    "muela del juicio",
)

PALABRAS_MEDIA = (
    "limpieza",
    "control",
    "revision",
    "blanqueamiento",
    "sellante",
    "profilaxis",
    "consulta",
)

INDICE = {nivel: posicion for posicion, nivel in enumerate(NIVELES)}

def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"

    )
    return " ".join(sin_acentos.split()) 

def _subir(nivel: str, escalones: int) -> str:
    posicion = min(INDICE[nivel] + escalones, INDICE[URGENTE])
    return NIVELES[posicion] 

def clasificar(
    motivo : str,
    *,
    es_nino: bool = False,
    hipertenso: bool = False,   
    diabetico: bool = False,
      
) -> str:
    texto = _normalizar(motivo)

    if any(palabra in texto for palabra in PALABRAS_URGENTE):
        nivel = URGENTE
    elif any(palabra in texto for palabra in PALABRAS_ALTA):
        nivel = ALTA
    elif any(palabra in texto for palabra in PALABRAS_MEDIA):
        nivel = MEDIA
    else:
        nivel = BAJA 

 # el mismo motivo puede escalar segun quien lo presenta: un niño con dolor de muela no puede esperar al mismo turno que un adulto sano.

    escalones = sum((es_nino, hipertenso, diabetico))
    return _subir(nivel, escalones) 

DESCRIPCION_URGENCIA = {
    BAJA: "rutina, sin dolor, puede esperar semanas",
    MEDIA: "dolor tolerable o control, espera de dias",
    ALTA : "dolor al masticar o infeccion, mismo dia",
    URGENTE: "dolor espontaneo, trauma, fiebre, atencion inmediata",
} 

#casos de prueba: la tabla de verdad del clasificador

CASOS = [
    # (motivo, es_nino, hipertenso, diabetico, esperando)
    ("Limpieza dental", False, False, False, MEDIA),
    ("consulta de control",True, False,False, ALTA),
    ("Dolor de muela desde hace 3 dias", False, False, False, ALTA),
    ("Caries profunda, dolor al masticar", False, False, False, ALTA),
    ("Caries profunda, dolor al masticar", False, False, True, URGENTE),
    ("Dolor espontaneo que me despierta en la noche", False, False, False, URGENTE),
    ("Golpe en el diente hoy", False, False, False, URGENTE),
    ("Grieta en el diente de hoy", False, True, False, MEDIA),
    ("Hinchazon en la cara", False, False, False, URGENTE),
    ("", False, False, False, BAJA),
]

if __name__ == "__main__":
    # Asi se prueba un clasificador sin framework de tests: tabla de casos,
    # se corre, y se ve que coincide. Si algo falla, el archivo te avisa.
    fallos = 0
    for motivo, es_nino, hipertenso, diabetico, esperado in CASOS:
        obtenido = clasificar(
            motivo,
            es_nino=es_nino,
            hipertenso=hipertenso,
            diabetico=diabetico,
        )
        ok = obtenido == esperado
        if not ok:
            fallos += 1
        print(
            f"{'OK  ' if ok else 'FALLA'} "
            f"motivo={motivo!r} nino={es_nino} hipert={hipertenso} diabet={diabetico} "
            f"-> {obtenido} (esperado {esperado})"
        )
    print()
    print(f"{len(CASOS) - fallos}/{len(CASOS)} casos OK")
