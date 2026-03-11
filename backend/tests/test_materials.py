import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_with_materials(auth_client: AsyncClient) -> str:
    create_resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Materials Test", "description": ""},
    )
    project_id = create_resp.json()["id"]

    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    wb.active.append(["header"])
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    mock_item = SimpleNamespace(
        number=1, code="CODE-01", name="Кирпич",
        unit="шт", quantity=500.0, unit_price=50.0,
        total_price=25000.0, item_type="material", section="",
    )
    mock_material = SimpleNamespace(
        name="Кирпич керамический", unit="шт",
        quantity=500.0, smeta_total=25000.0, codes=["CODE-01"],
    )
    mock_result = SimpleNamespace(items=[mock_item])

    with (
        patch("app.services.smeta_service.parse_excel", return_value=mock_result),
        patch(
            "app.services.smeta_service.aggregate_materials",
            return_value=[mock_material],
        ),
    ):
        await auth_client.post(
            f"/api/v1/projects/{project_id}/smeta/upload",
            files={
                "file": (
                    "smeta.xlsx",
                    io.BytesIO(xlsx_bytes),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    return project_id


@pytest.mark.asyncio
async def test_list_materials(
    auth_client: AsyncClient, project_with_materials: str
) -> None:
    resp = await auth_client.get(
        f"/api/v1/projects/{project_with_materials}/materials"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Кирпич керамический"
    assert data[0]["quantity"] == 500.0
    assert data[0]["supplier_price"] is None


@pytest.mark.asyncio
async def test_export_materials(
    auth_client: AsyncClient, project_with_materials: str
) -> None:
    resp = await auth_client.post(
        f"/api/v1/projects/{project_with_materials}/materials/export"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(resp.content) > 0
