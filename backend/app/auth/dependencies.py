from __future__ import annotations

import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer_scheme = HTTPBearer()


class AuthenticatedUser:
    def __init__(self, id: str, email: str) -> None:
        self.id = uuid.UUID(id)
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthenticatedUser:
    settings = get_settings()
    url = f"{settings.supabase_url}/auth/v1/user"
    headers = {"apiKey": settings.supabase_anon_key, "Authorization": f"Bearer {credentials.credentials}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    data = response.json()
    return AuthenticatedUser(id=data["id"], email=data.get("email", ""))
