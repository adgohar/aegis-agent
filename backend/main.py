from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI()

app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the aegis API"}
