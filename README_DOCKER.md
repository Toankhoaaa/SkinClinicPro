Run with Docker Compose
1) Copy .env and set secrets (or rely on compose defaults).
2) Build and start:
   docker compose up --build -d
3) Apply migrations:
   docker compose exec web python manage.py migrate
4) Create superuser (optional):
   docker compose exec web python manage.py createsuperuser
5) Access API:
   http://localhost:8000/swagger/

CI (GitHub Actions)
- Runs flake8 and pytest on pushes/PRs using sqlite.
- Configure branch protections to require CI success before merge.

Testing locally
1) Install deps:
   pip install -r requirements.txt
2) Env for sqlite:
   export DB_ENGINE=django.db.backends.sqlite3
3) Run tests:
   pytest -q

Notes
- Switch DB via env: DB_ENGINE (sqlite/postgresql).
- Media files are persisted in mounted volume "mediafiles".

