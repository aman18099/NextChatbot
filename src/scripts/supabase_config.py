from supabase import create_client
import os
from dotenv import load_dotenv
from jose import JWTError, jwt 
# from fastapi import HTTPException, status

# Error handling class
class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail



load_dotenv()

supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

def create_supabase_client():
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and Key must be set in environment variables.")
    return create_client(supabase_url, supabase_key)


def verify_jwt_token(token: str):
    try:
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET must be set in environment variables.")
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")