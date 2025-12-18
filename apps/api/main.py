from dotenv import load_dotenv
from fastapi import FastAPI
from routers import compliance, ingest, upload

load_dotenv()

app = FastAPI(title="AI Compliance Platform")

app.include_router(upload.router)
app.include_router(ingest.router)
app.include_router(compliance.router)


@app.get("/health")
def health():
    return {"status": "ok"}
