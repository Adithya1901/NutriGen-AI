from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import family, member, mealplan, grocery, recipe
from app.database import engine, Base
import migrate

Base.metadata.create_all(bind=engine)
try:
    migrate.run_migrations()
except Exception as e:
    print("Migration on startup note:", e)

app = FastAPI(
    title="NutriGen AI API",
    description="AI Powered Family Meal Planning and Grocery Optimization Backend API",
    version="1.0.0"
)

# Enable CORS for GitHub Pages and local development
origins = [
    "https://adithya1901.github.io",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(family.router)
app.include_router(member.router)
app.include_router(mealplan.router)
app.include_router(grocery.router)
app.include_router(recipe.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "NutriGen AI Backend API",
        "documentation": "/docs"
    }