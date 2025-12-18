from fastapi import FastAPI

app = FastAPI(title="AI Compliance Platform")


@app.get("/health")
def health():
    return {"status": "ok"}
