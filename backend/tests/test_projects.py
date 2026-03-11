import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_projects_empty(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_create_project(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Тест проект", "description": "Описание"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Тест проект"
    assert data["description"] == "Описание"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_missing_name(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/projects", json={"description": "x"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_project_detail(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Detail Test", "description": ""},
    )
    project_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert "progress" in data
    assert data["progress"]["smeta"]["status"] == "not_started"
    assert data["progress"]["materials"]["status"] == "not_started"
    assert data["progress"]["contractor"]["status"] == "not_started"
    assert data["progress"]["pricelist"]["status"] == "not_started"
    assert data["progress"]["margin"]["available"] is False


@pytest.mark.asyncio
async def test_get_project_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_other_user(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    create_resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Private", "description": ""},
    )
    project_id = create_resp.json()["id"]

    response = await other_auth_client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/api/v1/projects", json={"name": "Old Name", "description": ""}
    )
    project_id = create_resp.json()["id"]

    response = await auth_client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_soft_delete_project(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/api/v1/projects", json={"name": "To Delete", "description": ""}
    )
    project_id = create_resp.json()["id"]

    delete_resp = await auth_client.delete(f"/api/v1/projects/{project_id}")
    assert delete_resp.status_code == 204

    list_resp = await auth_client.get("/api/v1/projects")
    ids = [p["id"] for p in list_resp.json()]
    assert project_id not in ids

    get_resp = await auth_client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 404
