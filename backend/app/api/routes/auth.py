from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr


router = APIRouter(
    prefix="/api",
    tags=["Authentication"],
)


DEFAULT_EMAIL = "rodripereza8@gmail.com"
DEFAULT_PASSWORD = "qmi123"

active_tokens: set[str] = set()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    name: str
    email: EmailStr
    role: str
    workspace: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def default_user() -> UserResponse:
    return UserResponse(
        name="Rodri",
        email=DEFAULT_EMAIL,
        role="Founder / Investor",
        workspace="Quantum Market Intelligence",
    )


def get_current_token(
    authorization: str | None = Header(default=None),
) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token or token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )

    return token


@router.post(
    "/auth/login",
    response_model=LoginResponse,
)
def login(credentials: LoginRequest) -> LoginResponse:
    email = credentials.email.lower().strip()

    if email != DEFAULT_EMAIL or credentials.password != DEFAULT_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = uuid4().hex
    active_tokens.add(token)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=default_user(),
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    authorization: str | None = Header(default=None),
) -> None:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        active_tokens.discard(token)


@router.get(
    "/user",
    response_model=UserResponse,
)
def get_user(
    token: str = Depends(get_current_token),
) -> UserResponse:
    del token
    return default_user()