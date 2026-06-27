from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.api.deps import get_db
# Assuming your User model is here based on standard architecture:
from app.models.user import User 

router = APIRouter()

# -----------------------------------------
# Pydantic Schemas for Auth
# -----------------------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    # You can add phone_number, full_name, etc. here

class Token(BaseModel):
    access_token: str
    token_type: str

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

# -----------------------------------------
# Routes
# -----------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Creates a new user account and hashes the password securely.
    """
    # 1. Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
        
    # 2. Hash the password
    hashed_pw = get_password_hash(user_in.password)
    
    # 3. Save to database
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully. You can now log in."}

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Validates credentials against the database and returns a JWT.
    """
    # 1. Find user in the database
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Verify existence and password hash
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}