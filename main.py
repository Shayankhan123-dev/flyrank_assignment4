import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# --- Stage 4: Security Scheme & Middleware ---

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware dependency to extract and verify the JWT."""
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        return {"token": token, "user": user_response.user}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )

# --- Stage 4: Protected Routes & Logout ---

@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def protected_profile(auth_data: dict = Depends(verify_token)):
    """Protected route using middleware"""
    return {
        "message": "Access granted", 
        "user": auth_data["user"]
    }

@app.get("/protected/dashboard", status_code=status.HTTP_200_OK)
def protected_dashboard(auth_data: dict = Depends(verify_token)):
    """Checkpoint: A second protected route proving the middleware is reusable"""
    return {"message": "Welcome to the secure dashboard!"}

@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(auth_data: dict = Depends(verify_token)):
    """Secure logout endpoint"""
    try:
        supabase.auth.sign_out()
        return
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))