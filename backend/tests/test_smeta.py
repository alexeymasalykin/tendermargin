import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(auth_client: AsyncClient) -> str:
    resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Smeta Test Project", "description": ""},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_invalid_extension(
    auth_client: AsyncClient, project_id: str
) -> None:
    content = b"fake content"
    response = await auth_client.post(
        f"/api/v1/projects/{project_id}/smeta/upload",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_wrong_mime(auth_client: AsyncClient, project_id: str) -> None:
    content = b"not an excel file at all"
    response = await auth_client.post(
        f"/api/v1/projects/{project_id}/smeta/upload",
        files={
            "file": (
                "test.xlsx",
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 400


def _make_fake_xlsx() -> bytes:
    import io as _io
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["№", "Код", "Наименование", "Ед.изм.", "Кол-во", "Цена", "Сумма"])
    ws.append([1, "ГЭСН11-01-009-04", "Штукатурка стен", "м²", 120.0, 700.0, 84000.0])
    buf = _io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


_item = SimpleNamespace(
    number=1,
    code="ГЭСН11-01-009-04",
    name="Штукатурка стен",
    unit="м²",
    quantity=120.0,
    unit_price=700.0,
    total_price=84000.0,
    item_type="work",
    section="Раздел 1",
)
MOCK_PARSE_RESULT_ITEMS = [_item]
MOCK_PARSE_RESULT = SimpleNamespace(items=MOCK_PARSE_RESULT_ITEMS)
MOCK_MATERIAL = SimpleNamespace(
    name="Штукатурка", unit="кг", quantity=240.0, smeta_total=5000.0, codes=[]
)


@pytest.mark.asyncio
async def test_upload_excel_success(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_fake_xlsx()

    with (
        patch("app.services.smeta_service.parse_excel", return_value=MOCK_PARSE_RESULT),
        patch(
            "app.services.smeta_service.aggregate_materials",
            return_value=[MOCK_MATERIAL],
        ),
    ):
        response = await auth_client.post(
            f"/api/v1/projects/{project_id}/smeta/upload",
            files={
                "file": (
                    "smeta.xlsx",
                    io.BytesIO(xlsx_bytes),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 1
    assert data["total_sum"] == 84000.0


@pytest.mark.asyncio
async def test_upload_creates_smeta_items(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_fake_xlsx()

    with (
        patch("app.services.smeta_service.parse_excel", return_value=MOCK_PARSE_RESULT),
        patch(
            "app.services.smeta_service.aggregate_materials",
            return_value=[MOCK_MATERIAL],
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

    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_id}/smeta/items"
    )
    assert items_resp.status_code == 200
    data = items_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Штукатурка стен"


@pytest.mark.asyncio
async def test_reupload_cascades_delete(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_fake_xlsx()

    with (
        patch("app.services.smeta_service.parse_excel", return_value=MOCK_PARSE_RESULT),
        patch(
            "app.services.smeta_service.aggregate_materials",
            return_value=[MOCK_MATERIAL],
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
        resp = await auth_client.post(
            f"/api/v1/projects/{project_id}/smeta/upload",
            files={
                "file": (
                    "smeta2.xlsx",
                    io.BytesIO(xlsx_bytes),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    assert resp.status_code == 200
    items_resp = await auth_client.get(
        f"/api/v1/projects/{project_id}/smeta/items"
    )
    assert items_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_smeta_items_pagination(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_fake_xlsx()
    mock_items = [
        SimpleNamespace(
            number=i,
            code=f"CODE-{i:03d}",
            name=f"Item {i}",
            unit="шт",
            quantity=1.0,
            unit_price=100.0,
            total_price=100.0,
            item_type="work",
            section="",
        )
        for i in range(1, 11)
    ]
    mock_result = SimpleNamespace(items=mock_items)

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

    resp = await auth_client.get(
        f"/api/v1/projects/{project_id}/smeta/items?page=1&page_size=5"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert len(data["items"]) == 5
    assert data["pages"] == 2


@pytest.mark.asyncio
async def test_project_progress_after_upload(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_fake_xlsx()

    with (
        patch("app.services.smeta_service.parse_excel", return_value=MOCK_PARSE_RESULT),
        patch(
            "app.services.smeta_service.aggregate_materials",
            return_value=[MOCK_MATERIAL],
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

    detail_resp = await auth_client.get(f"/api/v1/projects/{project_id}")
    assert detail_resp.status_code == 200
    progress = detail_resp.json()["progress"]
    assert progress["smeta"]["status"] == "completed"
    assert progress["smeta"]["item_count"] == 1
    assert progress["smeta"]["total_sum"] == 84000.0
