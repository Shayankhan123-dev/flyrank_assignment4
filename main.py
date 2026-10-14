import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Request
from supabase import create_client, Client
from pydantic import BaseModel

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

# --- Pydantic Models ---
class AuthRequest(BaseModel):
    email: str
    password: str

# --- Stage 1: Sign Up & Log In ---

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: AuthRequest):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    try:
        # Send credentials to Supabase for registration
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"message": "User created successfully", "user": response.user}
    except Exception as e:
        # Catches duplicate emails or weak passwords
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(credentials: AuthRequest):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    try:
        # Authenticate with Supabase and receive the JWT
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user
        }
    except Exception:
        # If authentication fails, Supabase throws an exception
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})
    

# --- Stage 2 & 3: Public and Protected Gates ---

@app.get("/public/info", status_code=status.HTTP_200_OK)
def public_info():
    """Stage 2: A public endpoint that requires no authentication"""
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def protected_profile(request: Request):
    """Stage 2 & 3: A protected endpoint that manually verifies the token"""
    
    # 1. Extract the Authorization header (Stage 2)
    auth_header = request.headers.get("Authorization")
    
    # Check if header exists and is formatted correctly ("Bearer <token>")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Isolate just the token string
    token = auth_header.split(" ")[1]
    
    # 2. Verify the token with Supabase (Stage 3)
    try:
        # get_user validates the JWT cryptographically on the Supabase server
        user_response = supabase.auth.get_user(token)
        
        # If valid, return the user's secure metadata
        return {
            "message": "Access granted", 
            "user": user_response.user
        }
    except Exception:
        # Catches expired, forged, or malformed tokens
        raise HTTPException(status_code=401, detail="Invalid or expired token")