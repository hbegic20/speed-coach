import hashlib
import re
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.errors import ErrorCode

OWNER_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Owner:
    key_hash: str


def owner_from_token(token: str) -> Owner:
    return Owner(key_hash=hashlib.sha256(token.encode("ascii")).hexdigest())


def get_owner(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Owner:
    if credentials is None or not OWNER_TOKEN_PATTERN.fullmatch(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.OWNER_TOKEN_INVALID,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return owner_from_token(credentials.credentials)


CurrentOwner = Annotated[Owner, Depends(get_owner)]
