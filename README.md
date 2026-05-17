# Reflexia

Reflexia és una aplicació web orientada al seguiment terapèutic entre pacients i terapeutes. El projecte permet que els pacients escriguin entrades, que el sistema generi una anàlisi emocional orientativa i que el terapeuta pugui revisar l'evolució, afegir notes privades i crear preguntes de seguiment.

## Estructura

- `reflexia-backend/`: API desenvolupada amb Django i Django REST Framework.
- `reflexia-frontend/`: interfície web desenvolupada amb React i Vite.
- `postman/`: col·lecció de peticions per provar els endpoints principals.

## Backend

El backend organitza la lògica en aplicacions Django:

- `users`: registre, autenticació, rols, organitzacions, consentiment informat i 2FA.
- `entries`: entrades de journaling, preguntes del terapeuta i notes privades.
- `analysis`: anàlisi emocional automatitzada i revisió posterior per part del terapeuta.
- `contacts`: contactes associats i terapeutes de suport.

La base de dades és PostgreSQL. La configuració es llegeix des de variables d'entorn, definides al fitxer `.env` del backend.

### Execució del backend

```bash
cd reflexia-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Frontend

El frontend implementa les pantalles principals per a pacients, terapeutes i administradors de clínica. Inclou:

- inici de sessió i verificació en dos factors;
- registre de pacients i terapeutes;
- edició i consulta d'entrades;
- visualització de l'anàlisi emocional;
- gestió de pacients, preguntes i notes privades;
- panell de clínica per a organitzacions.

### Execució del frontend

```bash
cd reflexia-frontend
npm install
npm run dev
```

## Proves

El projecte inclou proves automatitzades tant al backend com al frontend.

```bash
cd reflexia-backend
python manage.py test
```

```bash
cd reflexia-frontend
npm test
```

També es pot validar manualment l'API amb la col·lecció de Postman inclosa al repositori.

## AVÍS

L'anàlisi emocional s'ha d'interpretar com una ajuda orientativa. No substitueix el criteri professional del terapeuta, i per aquest motiu l'aplicació manté la revisió professional com a part del flux.
