# Plan Fase 3 — Motor de Reservas

> Plan vivo del proyecto. Actualizar los checks al cerrar cada sesión.
> Tema central: **modelado de datos**. La regla anti-traslape vive en el esquema
> (rango `tstzrange` + `EXCLUDE USING gist`), no en `if` sueltos del código.

## Bloque 1 — Entorno y esquema (cerrado)

- [x] `venv/` con fastapi, sqlalchemy 2.0.54, psycopg2-binary, alembic, `bcrypt==4.3.0`
- [x] `.gitignore` (`.env`, `venv/`, `__pycache__/`, `AGENTS.md`)
- [x] `.env` con `DATABASE_URL` (Supabase) — **nunca se commitea**
- [x] `database.py`: `engine` con `pool_pre_ping=True, pool_recycle=300`, `SessionLocal`, `Base`, `get_db`
- [x] `models.py`: `Usuario`, `Recurso`, `Cita`, `Triaje`
- [x] `alembic init` + 1ª migración (`btree_gist` a mano, autogenerate no ve extensiones)
- [x] 4 tablas en Supabase + constraint `citas_no_traslapan`
- [x] **23P01 en vivo**: traslape rechazado por la base, no por el código

## Bloque 2 — Urgencia persistida y canceladas que no bloquean (cerrado)

- [x] `clasificador.py` — función pura, sin red, sin I/O. `10/10 casos OK`
- [x] `schemas.py` — contratos Pydantic v2. `CitaCreate` con triaje anidado,
      rechaza datetimes sin zona horaria, **no acepta `estado` ni `urgencia`**
- [x] `models.py` — `Triaje.urgencia` + `CheckConstraint` de estados válidos +
      `ExcludeConstraint` con `where= text("estado <> 'cancelada'")`
- [x] 2ª migración Alembic `3fb05b6732d6` generada **y editada a mano**
- [x] Sintaxis verificada con `ast.parse` (4 ops en `upgrade`, 4 en `downgrade`)
- [x] `requirements.txt` regenerado en UTF-8 (venía en UTF-16, `>` de PowerShell 5.1)

### Pendiente del bloque 2 (arranca la próxima sesión)

- [ ] `alembic upgrade head` — **lo corre el autor**, no el agente
- [ ] Verificar 3 cosas por `pg_get_constraintdef`: columna `triaje.urgencia`,
      `WHERE (estado <> 'cancelada')` en el EXCLUDE, `CHECK` con `'reservada'`
- [ ] Prueba en vivo de 5 etapas (ver abajo)
- [ ] Cosméticos en `models.py`: `name = "..."` → `name="..."`,
      `where= text ("...")` → `where=text("...")`, dos líneas en blanco entre clases

## Bloque 3 — Prueba en vivo de la regla (5 etapas)

Semilla temporal de `usuarios` + `recursos` (FK), y al final `DELETE` de todo.

| # | Acción | Resultado esperado |
|---|--------|--------------------|
| 1 | `INSERT` cita A `[10:00, 11:00)` estado `reservada` | OK |
| 2 | `INSERT` cita B `[10:30, 11:30)` mismo recurso | **23P01** traslape rechazado |
| 3 | `UPDATE` cita A → `cancelada` | OK |
| 4 | `INSERT` cita B `[10:00, 11:00)` (mismo slot que A) | **OK** — la cancelada liberó el horario |
| 5 | `UPDATE` B → `cancelada`; `INSERT` C `[10:00, 11:00)` | **OK** — dos canceladas no se bloquean |
| 6 | `SELECT` de `triaje.urgencia` en la cita C | persiste el valor del clasificador |
| 7 | Estados inválidos: `UPDATE` → `'pendiente'` | **23514** `check_violation` |
| 8 | `DELETE` de A, B, C + sus triajes; `SELECT count(*)` | 0 filas residuales |

## Bloque 4 — API (pendiente)

- [ ] `main.py` con `FastAPI()` y `include_router`
- [ ] `routers/citas.py` — la regla NO se reimplementa: se traduce el `23P01`
      a un `HTTPException(409, ...)` para que el cliente entienda el conflicto
- [ ] `routers/recursos.py` — listado + disponibilidad por rango
- [ ] Auth: `password_hash` con bcrypt, `Depends` de usuario actual
- [ ] Manejo de errores: 422 formato · 401 sin auth · 409 conflicto de horario

## Bloque 5 — README y deploy (pendiente)

- [ ] README con el molde SOURCE / SYSTEM / ENGINEERING / ROLE
- [ ] Diagrama ER (dbdiagram.io)
- [ ] `render.yaml` + deploy en Render
- [ ] Commit y push con URL viva

## Decisiones de diseño (no tocar sin justificar)

1. **La regla de traslape está en la base.** El `EXCLUDE` con GiST es lo que
   garantiza la invariante. El código solo traduce el error a una respuesta HTTP.
2. **`cancelada` sí libera horario; `atendida` y `no_asistio` no.** De ahí el
   `WHERE estado <> 'cancelada'` en el `EXCLUDE`.
3. **`urgencia` se persiste en `triaje`, no se calcula al leer.** Se calcula una
   vez al crear la cita y se guarda: la urgencia de una cita no cambia sola.
4. **`CitaCreate` no acepta `estado` ni `urgencia`.** El estado lo decide el
   motor; la urgencia la decide el clasificador a partir del triaje.
5. **Los datetimes deben traer zona horaria.** Se guarda en `tstzrange` para que
   el traslape se compare en tiempo absoluto, no en hora local.

## Pendientes fuera del código

- [ ] Rotar el password de Supabase (se expuso en una sesión de chat)
- [ ] Verificar que el README no mencione la URL de la API APU por error
