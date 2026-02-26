# Task API (Prueba Técnica Backend)

API REST para gestionar una lista de tareas (ToDo) con **Python + Django + Django REST Framework + PostgreSQL**, usando **soft delete**, control de estados, filtros, documentación OpenAPI (Swagger) y colección Postman lista para ejecutar.

---

##  Funcionalidades

-  Crear tarea
-  Listar tareas (por defecto excluye eliminadas)
-  Consultar tarea por `id`
-  Actualizar tarea (PUT/PATCH)
-  Eliminar tarea (soft delete)
-  Cambiar estado (endpoint dedicado)
-  Listar tareas próximas a vencer (`upcoming`)
-  (Opcional) Filtros por estado, fechas y búsqueda

---

##  Modelo de tarea

Campos principales:

- `id` (autoincremental)
- `title` (requerido)
- `description` (opcional)
- `status`: `pending | completed | postponed`
- `due_date` (opcional)
- auditoría: `created_at`, `updated_at`, `created_by_name`
- eliminación lógica: `deleted_at`

---

##  Tecnologías

- Python 3.x
- Django
- Django REST Framework
- PostgreSQL
- drf-spectacular (OpenAPI/Swagger)
- django-filter (filtros)
- Postman collection

---

## Requisitos previos

1. **Python 3.11+** (recomendado)
2. **PostgreSQL** instalado y corriendo
3. Un usuario + base de datos creados (o usar uno existente)
4. (Opcional) Postman para probar rápido

---

##  Instalación y configuración

### 1) Clonar y entrar al proyecto

```bash
git clone <TU_REPO>
cd task_api
```

### 2) Crear y activar entorno virtual

**Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Instalar dependencias

Si usas `pip`:

```bash
pip install -r requirements.txt
```

Si el proyecto está con `pyproject.toml` / `uv`:

```bash
uv sync
```

---

## 🗄️ Configuración del `.env`

Crea un archivo `.env` en la raíz del proyecto:

`.env`
```env

DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="root"
DB_NAME="postgres"

```

> Importante: si falta `DB_NAME` (o cualquier variable), Django lanza `ImproperlyConfigured`.

---

##  Crear base de datos en PostgreSQL

Ejemplo con SQL:

```sql
CREATE DATABASE task_db;
```

---

##  Migraciones

Ejecuta:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

##  Ejecutar el proyecto

```bash
python manage.py runserver
```

Servidor local:
- `http://127.0.0.1:8000/`

---

## Documentación Swagger / OpenAPI

- Swagger UI:  
  `http://127.0.0.1:8000/api/docs/`

- Schema OpenAPI JSON:  
  `http://127.0.0.1:8000/api/schema/`

---

## Endpoints principales

Base URL: `http://127.0.0.1:8000/api`

### 1) Crear tarea
**POST** `/tasks/`

Body ejemplo:
```json
{
  "title": "Comprar mercado",
  "description": "Leche, huevos, café",
  "status": "pending",
  "due_date": "2026-02-26T10:00:00-05:00",
  "created_by_name": "Yerlys"
}
```

---

### 2) Listar tareas
**GET** `/tasks/`

 Por defecto **excluye eliminadas**.

Query params útiles:
- `include_deleted=true` → incluye eliminadas
- `search=texto` → busca en title/description/created_by_name
- `ordering=due_date` o `ordering=-created_at`
- filtros (si están habilitados): `status=...`, `due_date_after=...`, etc.

Ejemplo:
```
GET /api/tasks/?status=pending&search=mercado&ordering=due_date
```

---

### 3) Consultar tarea por ID
**GET** `/tasks/{id}/`

---

### 4) Actualizar tarea completa
**PUT** `/tasks/{id}/`

---

### 5) Actualizar tarea parcial
**PATCH** `/tasks/{id}/`

Ejemplo:
```json
{
  "title": "Actualizar título"
}
```

---

### 6) Eliminar tarea (soft delete)
**DELETE** `/tasks/{id}/`

 Marca `deleted_at`, no borra físico.

---

### 7) Cambiar estado
**PATCH** `/tasks/{id}/status/`

Body ejemplo:
```json
{
  "status": "completed"
}
```

Estados permitidos:
- `pending`
- `completed`
- `postponed`

---

##  Endpoint: Upcoming tasks (tareas próximas a vencer)

**GET** `/tasks/upcoming/`

###  Criterio definido (importante para la prueba)
Este endpoint retorna tareas:

- No eliminadas (`deleted_at IS NULL`)
- Con `due_date` definido (`due_date IS NOT NULL`)
- No vencidas (`due_date >= now`)
- Dentro del rango (`due_date <= now + within_days`)
- No completadas (`status != completed`)

### Query param
- `within_days` (int, default `7`)

Ejemplos:
- próximas **24h**:  
  `GET /api/tasks/upcoming/?within_days=1`

- próximas **7 días**:  
  `GET /api/tasks/upcoming/?within_days=7`

Validaciones:
- si `within_days` no es entero → `400 Bad Request`
- si `within_days` es negativo → `400 Bad Request`

---

## probar (rápido)

### Opción A: Swagger UI
1. Abre: `http://127.0.0.1:8000/api/docs/`
2. Ve a **POST /api/tasks/**
3. Crea tareas con `due_date` futuro
4. Luego prueba **GET /api/tasks/upcoming/**

---

## Postman (colección incluida)

En la carpeta `docs/` están los archivos:
- `docs/postman_collection.json`
- `docs/postman_environment.json`

### Importar
1. Abre Postman
2. **Import** → selecciona `postman_collection.json`
3. Importa también `postman_environment.json`
4. Selecciona el environment y ejecuta requests

### Variables de entorno
- `base_url` = `http://127.0.0.1:8000`

---

##  Respuestas y manejo de errores

- `201 Created` al crear
- `200 OK` en list/retrieve/update
- `204 No Content` al eliminar lógico
- `400 Bad Request` para validaciones (ej: `within_days=-1`)
- `404 Not Found` si el recurso no existe o está soft deleted sin `include_deleted=true`

---
