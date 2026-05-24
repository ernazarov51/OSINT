from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username kamida 3 ta belgi bo'lishi kerak")
        if len(v) > 50:
            raise ValueError("Username 50 ta belgidan oshmasligi kerak")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgi bo'lishi kerak")
        return v

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class MeResponse(BaseModel):
    authenticated: bool
    username: str | None = None
    email: str | None = None
