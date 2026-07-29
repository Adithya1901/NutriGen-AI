from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import family, member, mealplan, grocery, recipe
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

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