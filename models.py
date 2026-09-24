from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ExcludeConstraint, TSTZRANGE
from database import Base

class Cita(Base):
    __tablename__="citas"
    id: Mapped[int] = mapped_column(primary_key=True)
    recurso_id: Mapped[int] = mapped_column(ForeignKey("recursos.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    periodo: Mapped[datetime] = mapped_column(TSTZRANGE)
    estado: Mapped[str] = mapped_column(String(30), default="reservada")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ExcludeConstraint(
            ("recurso_id", "="),
            ("periodo", "&&"),
            using="gist",
            name="citas_no_traslapan",
        ),
    )
class Triaje(Base):
    __tablename__ = "triaje"

    id: Mapped[int] = mapped_column(primary_key=True)
    cita_id: Mapped[int] = mapped_column(ForeignKey("citas.id"), unique=True)  # unique = 1:1
    motivo: Mapped[str] = mapped_column(String(120))
    es_nino: Mapped[bool] = mapped_column(Boolean, default=False)
    hipertenso: Mapped[bool] = mapped_column(Boolean, default=False)
    diabetico: Mapped[bool] = mapped_column(Boolean, default=False)
                                   

class Usuario(Base):
    """Dentista / recepcionista / admin de la clínica."""
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[str] = mapped_column(String(30), default="dentista")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())


class Recurso(Base):
    """El consultorio: el recurso único que no puede traslapar citas."""
    __tablename__ = "recursos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)