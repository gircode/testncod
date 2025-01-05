"""
Authentication Router
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

# Security configuration
SECRET_KEY = "your-secret-key-here"  # In production, use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        self._users = {  # Mock user storage
            "admin": {
                "username": "admin",
                "full_name": "Administrator",
                "email": "admin@example.com",
                "hashed_password": pwd_context.hash("admin"),
                "disabled": False,
            }
        }

    def _setup_routes(self):
        @self.router.post("/token")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            """Login to get access token"""
            user = self._authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token = self._create_access_token(data={"sub": user["username"]})
            return {"access_token": access_token, "token_type": "bearer"}

        @self.router.get("/users/me")
        async def get_current_user(token: str = Depends(oauth2_scheme)):
            """Get current user information"""
            credentials_exception = HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise credentials_exception
            except jwt.PyJWTError:
                raise credentials_exception

            user = self._users.get(username)
            if user is None:
                raise credentials_exception

            return user

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

    def _authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user"""
        user = self._users.get(username)
        if not user:
            return None
        if not self._verify_password(password, user["hashed_password"]):
            return None
        return user

    def _create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt


# Create global auth router instance
auth_router = AuthRouter().router
