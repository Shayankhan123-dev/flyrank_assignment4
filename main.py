import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

# Load variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env file")

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth API")

@app.on_event("startup")
async def startup_event():
    # Stage 0 Checkpoint requirement
    print("Server running and connected to Supabase")

@app.get("/")
def health_check():
    return {"status": "Server is running"}