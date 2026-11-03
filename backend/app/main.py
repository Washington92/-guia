from fastapi import FastAPI

app = FastAPI(title="Águia Gestão CRM", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "aguia-gestao-crm"}
