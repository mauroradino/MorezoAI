from fastapi import FastAPI, Request
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Tus credenciales de Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)
app = FastAPI()

class Plato(BaseModel):
    id: int
    pedido: str

@app.post("/nueva_orden")
def nueva_orden(plato: Plato):
    # Convertir el modelo a dict para insertar en Supabase
    response = supabase.table("Ordenes").insert(plato.model_dump()).execute()
    return {"status": "ok", "data": response.data}