# Reflexia

Reflexia és una aplicació web de suport al seguiment terapèutic entre pacients, terapeutes i organitzacions clíniques. El projecte ja està desplegat i funcionant en producció, amb backend Django, frontend React/Vite, autenticació amb JWT i 2FA, anàlisi emocional assistida per IA, alertes clíniques i fluxos diferenciats per rol.

L'anàlisi emocional és orientativa i està pensada per ajudar el terapeuta a revisar l'evolució del pacient. No substitueix el criteri professional ni la intervenció clínica.

## Funcionalitats

- Registre, inici de sessió i recuperació de contrasenya.
- Autenticació amb doble factor.
- Acceptació de consentiment informat i condicions legals.
- Rols de pacient, terapeuta i administrador de clínica.
- Organitzacions clíniques, invitacions i gestió de terapeutes.
- Entrades de journaling per part dels pacients.
- Anàlisi emocional automatitzada amb OpenAI.
- Evolució emocional i visualització de tendències.
- Preguntes de seguiment creades pel terapeuta.
- Notes privades del terapeuta.
- Contactes associats del pacient.
- Terapeutes de suport.
- Alertes clíniques per risc alt, validació professional i notificacions.
- Exportació i documentació de l'API.

## Arquitectura

```text
reflexia/
├── reflexia-backend/      # API Django + Django REST Framework
├── reflexia-frontend/     # Aplicació React + Vite
├── .github/workflows/     # CI del projecte
└── README.md
```

### Backend

El backend està desenvolupat amb Django 4.2 i Django REST Framework. Les aplicacions principals són:

- `users`: usuaris, rols, autenticació, 2FA, consentiment, organitzacions i invitacions.
- `entries`: entrades de journaling, preguntes terapèutiques, notes privades i exportacions.
- `analysis`: anàlisi emocional, evolució i correccions clíniques.
- `contacts`: contactes associats i terapeutes de suport.
- `alerts`: alertes clíniques, validació, escalat i notificacions.

La base de dades és PostgreSQL. Les tasques asíncrones i notificacions es gestionen amb Celery i Redis.

### Frontend

El frontend està desenvolupat amb React 19 i Vite. Inclou les pantalles principals de pacient, terapeuta i administrador de clínica, amb rutes protegides, formularis, taules, panells de detall, gràfics d'evolució emocional i integració amb l'API.

## Stack

- Python 3.13
- Django 4.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Gunicorn
- WhiteNoise
- OpenAI API
- React 19
- Vite
- PrimeReact
- Chart.js
- Vitest
- GitHub Actions

## Configuració local

### Backend

```bash
cd reflexia-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Després de copiar l'exemple, cal editar `.env` i definir com a mínim `DATABASE_URL`, `SECRET_KEY` i, si es vol executar l'anàlisi emocional, `OPENAI_API_KEY`.

Per defecte, l'API queda disponible a:

```text
http://127.0.0.1:8000
```

Variables importants del backend:

- `SECRET_KEY`
- `DEBUG`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `OPENAI_API_KEY`
- `OPENAI_ANALYSIS_MODEL`
- `REDISCLOUD_URL`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

Per executar les tasques asíncrones en local:

```bash
cd reflexia-backend
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

### Frontend

```bash
cd reflexia-frontend
npm install
cp .env.example .env
npm run dev
```

Després de copiar l'exemple, cal revisar `VITE_API_BASE_URL` perquè apunti a l'API local o de producció corresponent.

Per defecte, el frontend queda disponible a:

```text
http://localhost:5173
```

Variable principal del frontend:

- `VITE_API_BASE_URL`: URL base de l'API, per exemple `http://127.0.0.1:8000/api`.

## API

El backend exposa documentació OpenAPI amb `drf-spectacular`:

- Swagger UI: `/api/docs/`
- Redoc: `/api/redoc/`
- Schema OpenAPI: `/api/schema/`

L'endpoint arrel del backend retorna un missatge de salut bàsic:

```text
GET /
```

## Proves i qualitat

Backend:

```bash
cd reflexia-backend
python manage.py check
python manage.py test
```

Frontend:

```bash
cd reflexia-frontend
npm run lint
npm test
npm run build
```

La CI de GitHub Actions executa comprovacions del backend i del frontend sobre les branques `development` i `main`.

## Producció

El projecte està preparat per a producció i ja funciona correctament en un entorn desplegat.

### Backend en producció

El backend inclou un `Procfile` amb processos separats per a web, worker i beat:

```text
web: gunicorn config.wsgi --log-file -
worker: celery -A config worker --loglevel=info
beat: celery -A config beat --loglevel=info
```

En producció cal tenir configurat:

- PostgreSQL accessible mitjançant `DATABASE_URL`.
- Redis accessible mitjançant `REDISCLOUD_URL`.
- `DEBUG=False`.
- `SECRET_KEY` segura.
- `ALLOWED_HOSTS` amb el domini real de l'API.
- `FRONTEND_URL` amb el domini real del frontend.
- `CORS_ALLOWED_ORIGINS` i `CSRF_TRUSTED_ORIGINS` restringits al frontend.
- HTTPS i cookies segures activades.
- Credencials SMTP reals per a correus.
- `OPENAI_API_KEY` per a l'anàlisi emocional.

Abans de publicar una nova versió:

```bash
cd reflexia-backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

### Frontend en producció

El frontend està preparat per desplegar-se com a SPA. El fitxer `vercel.json` redirigeix totes les rutes cap a `index.html`, necessari perquè React Router funcioni correctament en navegació directa.

En producció cal definir:

```text
VITE_API_BASE_URL=https://api.exemple.com/api
```

Build de producció:

```bash
cd reflexia-frontend
npm run build
```

## Branques

- `development`: branca principal de desenvolupament i CI.
- `main`: branca estable.

## Avís clínic

Reflexia no és un sistema d'emergències ni una eina de diagnòstic automàtic. Les alertes, anàlisis i tendències han de ser revisades per professionals qualificats. Davant d'una situació de risc immediat, cal seguir els protocols clínics i d'emergència corresponents.
