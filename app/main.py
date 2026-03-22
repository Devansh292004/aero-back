from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.inspections import router as inspections_router
from app.routes.reports import router as reports_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AeroOps Backend", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inspections_router, prefix="/api")
app.include_router(reports_router)


@app.get("/")
def root():
    return {"message": "AeroOps backend is running"}