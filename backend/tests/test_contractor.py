import io
import uuid
from unittest.mock import patch
import types

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_with_smeta(auth_client: AsyncClient) -> str:
    """Create a project and upload a minimal smeta with one work item."""
    create_resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Contractor Test", "description": ""},
    )
    project_id = create_resp.json()["id"]

    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    wb.active.append(["№", "Код", "Наименование", "Ед.изм.", "Кол-во", "Цена", "Сумма"])
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    mock_item = types.SimpleNamespace(
        number=1,
        code="ГЭСН11-01-009-04",
        name="Штукатурка стен",
        unit="м²",
        quantity=120.0,
        unit_price=700.0,
        total_price=84000.0,
        item_type="work",
        section="",
    )
    mock_result = types.SimpleNamespace(items=[mock_item])

    with (
        patch("app.services.smeta_service.parse_excel", return_value=mock_result),
        patch("app.services.smeta_service.aggregate_materials", return_value=[]),
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
async def test_list_contractor_prices(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    resp = await auth_client.get(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Штукатурка стен"
    assert data[0]["price"] is None


@pytest.mark.asyncio
async def test_batch_update_contractor_prices(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_with_smeta}/smeta/items"
    )
    smeta_item_id = items_resp.json()["items"][0]["id"]

    resp = await auth_client.put(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices",
        json={"prices": [{"smeta_item_id": smeta_item_id, "price": 580.0}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["price"] == 580.0
    assert data[0]["total"] == pytest.approx(580.0 * 120.0)


@pytest.mark.asyncio
async def test_single_update_contractor_price(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_with_smeta}/smeta/items"
    )
    smeta_item_id = items_resp.json()["items"][0]["id"]

    resp = await auth_client.put(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices/{smeta_item_id}",
        json={"price": 620.0},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == 620.0


@pytest.mark.asyncio
async def test_price_syncs_to_library(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    """Setting a price in a project must create/update the library entry."""
    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_with_smeta}/smeta/items"
    )
    smeta_item_id = items_resp.json()["items"][0]["id"]

    await auth_client.put(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices/{smeta_item_id}",
        json={"price": 750.0},
    )

    # Create another project and upload same smeta — library price must be used
    create_resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Second Project", "description": ""},
    )
    new_project_id = create_resp.json()["id"]

    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    wb.active.append(["header"])
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    mock_item2 = types.SimpleNamespace(
        number=1,
        code="ГЭСН11-01-009-04",
        name="Штукатурка стен",
        unit="м²",
        quantity=80.0,
        unit_price=700.0,
        total_price=56000.0,
        item_type="work",
        section="",
    )
    mock_result2 = types.SimpleNamespace(items=[mock_item2])

    with (
        patch("app.services.smeta_service.parse_excel", return_value=mock_result2),
        patch("app.services.smeta_service.aggregate_materials", return_value=[]),
    ):
        await auth_client.post(
            f"/api/v1/projects/{new_project_id}/smeta/upload",
            files={
                "file": (
                    "smeta.xlsx",
                    io.BytesIO(xlsx_bytes),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    prices_resp = await auth_client.get(
        f"/api/v1/projects/{new_project_id}/contractor-prices"
    )
    assert prices_resp.status_code == 200
    prices = prices_resp.json()
    assert prices[0]["price"] == 750.0


@pytest.mark.asyncio
async def test_contractor_price_not_found(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    fake_id = str(uuid.uuid4())
    resp = await auth_client.put(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices/{fake_id}",
        json={"price": 100.0},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_project_progress_contractor_in_progress(
    auth_client: AsyncClient, project_with_smeta: str
) -> None:
    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_with_smeta}/smeta/items"
    )
    smeta_item_id = items_resp.json()["items"][0]["id"]

    await auth_client.put(
        f"/api/v1/projects/{project_with_smeta}/contractor-prices/{smeta_item_id}",
        json={"price": 500.0},
    )

    detail_resp = await auth_client.get(f"/api/v1/projects/{project_with_smeta}")
    progress = detail_resp.json()["progress"]
    assert progress["contractor"]["status"] == "completed"
    assert progress["contractor"]["filled"] == 1
    assert progress["margin"]["available"] is True
    assert progress["margin"]["margin_pct"] is not None
