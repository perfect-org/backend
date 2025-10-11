import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.core.types import UserType


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str]


class UserBase(BaseModel):
    name: str = Field("Шмекит", min_length=2, max_length=50)
    email: EmailStr

    @field_validator("name")
    @staticmethod
    def validate_russian_name(value: str) -> str:
        value = " ".join(value.strip().split())

        if not re.fullmatch(r"^[а-яА-ЯёЁ\s-]+$", value):
            raise ValueError(
                "Имя должно содержать только русские буквы, пробелы и дефисы"
            )

        if not value.replace("-", "").strip():
            raise ValueError(
                "Имя не может состоять только из пробелов или дефисов"
            )

        if len(value) < 2:
            raise ValueError("Имя слишком короткое (минимум 2 символа)")

        if len(value) > 50:
            raise ValueError("Имя слишком длинное (максимум 50 символов)")

        parts = []
        for part in value.split():
            if part.startswith("-"):
                part = "-" + part[1:].capitalize() if len(part) > 1 else part
            else:
                part = part.capitalize()
            parts.append(part)

        return " ".join(parts)


class UserOut(UserBase):
    id: int
    role: UserType

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    model_config = ConfigDict(
        json_schema_extra={
            "name": {
                "description": "Только имя (2-50 символов, только русские буквы)",
                "example": "Никита",
            }
        }
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Имя пользователя (2-50 символов, только русские буквы)",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Новый email пользователя",
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="Новый пароль (минимум 8 символов)",
    )
    role: Optional[UserType] = Field(
        UserType.USER,
        description="Роль пользователя",
    )

    @field_validator("name")
    @classmethod
    def validate_russian_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        value = " ".join(value.strip().split())

        if not re.fullmatch(r"^[а-яА-ЯёЁ\s-]+$", value):
            raise ValueError(
                "Имя должно содержать только русские буквы, пробелы и дефисы"
            )

        if not value.replace("-", "").strip():
            raise ValueError(
                "Имя не может состоять только из пробелов или дефисов"
            )

        parts = []
        for part in value.split():
            if part.startswith("-"):
                part = "-" + part[1:].capitalize() if len(part) > 1 else part
            else:
                part = part.capitalize()
            parts.append(part)

        return " ".join(parts)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Иван",
                "email": "ivan.new@example.com",
                "password": "newPassword123",
                "role": "user",
            }
        }
    )


class AdminCreate(UserCreate):
    role: UserType


class UserAuth(BaseModel):
    email: EmailStr
    password: str
