import pytest
from httpx import AsyncClient


async def register(client: AsyncClient, email: str = "test@example.com", password: str = "TestPass1!", name: str = "Test User"):
    return await client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": name})


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        r = await register(client)
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
        assert "access_token" in r.cookies

    async def test_register_duplicate_email(self, client: AsyncClient):
        await register(client)
        r = await register(client)
        assert r.status_code == 409
        assert "already registered" in r.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "TestPass1!", "name": "Test"})
        assert r.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={"email": "x@x.com", "password": "short", "name": "Test"})
        assert r.status_code == 422

    async def test_register_short_name(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={"email": "x@x.com", "password": "TestPass1!", "name": "X"})
        assert r.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await register(client)
        r = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "TestPass1!"})
        assert r.status_code == 200
        assert "access_token" in r.cookies
        assert "refresh_token" in r.cookies

    async def test_login_wrong_password(self, client: AsyncClient):
        await register(client)
        r = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "wrongpass"})
        assert r.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "TestPass1!"})
        assert r.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient):
        await register(client)
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == "test@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401


class TestRefresh:
    async def test_refresh_rotates_token(self, client: AsyncClient):
        await register(client)
        old_refresh = client.cookies.get("refresh_token")
        r = await client.post("/api/v1/auth/refresh")
        assert r.status_code == 200
        new_refresh = client.cookies.get("refresh_token")
        assert new_refresh != old_refresh

    async def test_refresh_no_cookie(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/refresh")
        assert r.status_code == 401


class TestLogout:
    async def test_logout_clears_cookies(self, client: AsyncClient):
        await register(client)
        r = await client.post("/api/v1/auth/logout")
        assert r.status_code == 204
        assert client.cookies.get("access_token") is None

    async def test_me_after_logout(self, client: AsyncClient):
        await register(client)
        await client.post("/api/v1/auth/logout")
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401
