import pytest
from unittest.mock import AsyncMock, patch
from dataclasses import make_dataclass

from app.services.user import UserService
from app.schemas import UserCreate, UserAuth, UserOut
from app.core.security import get_password_hash
from app.exceptions.service_errors import (
    EntityAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
)


async def make_fake_user(
    id: int, email: str, name: str, raw_password: str, role: str
):

    FakeUser = make_dataclass(
        "FakeUser",
        [
            ("id", int),
            ("email", str),
            ("name", str),
            ("hashed_password", str),
            ("role", str),
        ],
        frozen=True,
    )
    return FakeUser(
        id, email, name, await get_password_hash(raw_password), role
    )


@pytest.mark.asyncio
class TestUserServiceRegister:

    async def test_register_success(self):
        fake_repo = AsyncMock()
        fake_repo.get_user_by_email.return_value = None

        orm_user = await make_fake_user(
            1,
            "a@b.com",
            "nice",
            "secret123",
            "USER",
        )
        fake_repo.create.return_value = orm_user

        svc = UserService(repository=fake_repo)
        payload = UserCreate(
            email="a@b.com", name="nice", password="secret123"
        )

        out = await svc.register(payload)

        # Обновляем название метода здесь тоже
        fake_repo.get_user_by_email.assert_awaited_once_with("a@b.com")
        fake_repo.create.assert_awaited_once()
        assert isinstance(out, UserOut)
        assert out.id == 1
        assert out.email == "a@b.com"
        assert out.name == "nice"
        assert out.role == "USER"

    async def test_register_conflict(self):
        fake_repo = AsyncMock()
        # Существующий пользователь
        fake_repo.get_by_email.return_value = await make_fake_user(
            1, "a@b.com", "nice", "secret123", "user"
        )

        svc = UserService(repository=fake_repo)
        payload = UserCreate(email="a@b.com", name="123", password="secret123")

        with pytest.raises(EntityAlreadyExistsError):
            await svc.register(payload)


@pytest.mark.asyncio
class TestUserServiceAuthenticate:
    pass
    # async def test_authenticate_success(self):
    #     fake_repo = AsyncMock()
    #
    #     # Создаём пользователя с любым хешем (он не будет проверяться)
    #     orm_user = await make_fake_user(
    #         2, "x@y.com", "nice", "any_hash", "USER"
    #     )
    #     fake_repo.get_by_email.return_value = orm_user
    #
    #     # Патчим проверку пароля
    #     with patch("app.core.security.pwd_context", return_value=True):
    #         svc = UserService(repository=fake_repo)
    #         creds = UserAuth(email="x@y.com", password="passw0rd")
    #         out = await svc.authenticate(creds)
    #
    #     # Проверки
    #     fake_repo.get_by_email.assert_awaited_once_with("x@y.com")
    #     assert isinstance(out, UserOut)
    #     assert out.id == 2
    #     assert out.email == "x@y.com"
    #     assert out.name == "nice"
    #     assert out.role == "USER"
    #
    # async def test_authenticate_not_found(self):
    #     fake_repo = AsyncMock()
    #     fake_repo.get_by_email.return_value = None
    #
    #     svc = UserService(repository=fake_repo)
    #     creds = UserAuth(email="no@user.com", password="whatever")
    #
    #     with pytest.raises(UserNotFoundError):
    #         await svc.authenticate(creds)
    #
    # async def test_authenticate_bad_password(self):
    #     fake_repo = AsyncMock()
    #     orm_user = await make_fake_user(
    #         3, "u@v.com", "nice", "correctpwd", "user"
    #     )
    #     fake_repo.get_by_email.return_value = orm_user
    #
    #     svc = UserService(repository=fake_repo)
    #     creds = UserAuth(email="u@v.com", password="wrongpass")
    #
    #     with pytest.raises(InvalidCredentialsError):
    #         await svc.authenticate(creds)


@pytest.mark.asyncio
class TestUserServiceGetUser:

    async def test_get_user_success(self):
        fake_repo = AsyncMock()

        orm_user = await make_fake_user(
            42, "z@z.com", "nice", "mypassword", "USER"
        )
        fake_repo.get_by_id.return_value = orm_user

        svc = UserService(repository=fake_repo)

        out = await svc.get_user(42)

        fake_repo.get_by_id.assert_awaited_once_with(42)
        assert isinstance(out, UserOut)
        assert out.id == 42
        assert out.email == "z@z.com"
        assert out.name == "nice"
        assert out.role == "USER"

    async def test_get_user_not_found(self):
        fake_repo = AsyncMock()
        fake_repo.get_by_id.return_value = None

        svc = UserService(repository=fake_repo)

        with pytest.raises(UserNotFoundError) as exc:
            await svc.get_user(99)
        assert "ID=99" in str(exc.value)
