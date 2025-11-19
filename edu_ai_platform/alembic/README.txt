This is a minimal Alembic scaffold for the prototype.
To use Alembic locally you can:

1. Install alembic in your environment:
   pip install alembic

2. Initialize migrations (if not already):
   alembic init alembic

3. Edit alembic.ini sqlalchemy.url to point to your DB (already set to sqlite:///data/edu_ai.db)

4. Generate an autogenerate revision (after installing alembic and running from project root):
   alembic revision --autogenerate -m "initial"

5. Apply migrations:
   alembic upgrade head

Note: This scaffold uses SQLModel.metadata in alembic/env.py for autogeneration.
In CI/production prefer deterministic migrations created and reviewed by hand.
