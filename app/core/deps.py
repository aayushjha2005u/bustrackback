"""
This is the gatekeeper. Any endpoint that adds
    current_user: User = Depends(get_current_user)
to its arguments is now a PROTECTED endpoint - FastAPI will:
  1. Pull the "Authorization: Bearer <token>" header from the request
  2. Decode it and check it's valid / not expired
  3. Look up that user in the database
  4. Hand the User object to the endpoint

This is where "authorization enforced by the backend" actually
happens - every protected endpoint gets the REAL logged-in user
from the token, never from something the client claims in the request.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user
