import io
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(auth_client: AsyncClient) -> str:
    resp = await auth_client.post(
        "/api/v1/projects",
        json={"name": "Pricelist Test", "description": ""},
    )
    return resp.json()["id"]


def _make_xlsx_bytes() -> bytes:
    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.append(["Наименование", "Ед.изм.", "Цена"])
    ws.append(["Штукатурка", "кг", 85.0])
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_pricelist(auth_client: AsyncClient, project_id: str) -> None:
    xlsx_bytes = _make_xlsx_bytes()
    resp = await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/upload",
        files={
            "file": (
                "pricelist.xlsx",
                io.BytesIO(xlsx_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "upload_id" in data


@pytest.mark.asyncio
async def test_upload_pricelist_invalid_extension(
    auth_client: AsyncClient, project_id: str
) -> None:
    resp = await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/upload",
        files={"file": ("prices.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_detect_structure_no_upload(
    auth_client: AsyncClient, project_id: str
) -> None:
    resp = await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/detect-structure"
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_detect_structure_success(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_xlsx_bytes()
    await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/upload",
        files={
            "file": (
                "pricelist.xlsx",
                io.BytesIO(xlsx_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    # detect_structure in service will try to call core.pricelist_mapper which isn't available.
    # The service handles ImportError gracefully and returns empty structure.
    resp = await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/detect-structure"
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_start_mapping_returns_task_id(
    auth_client: AsyncClient, project_id: str
) -> None:
    xlsx_bytes = _make_xlsx_bytes()
    await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/upload",
        files={
            "file": (
                "pricelist.xlsx",
                io.BytesIO(xlsx_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    mock_task_id = str(uuid.uuid4())
    with patch(
        "app.routers.pricelist.start_mapping_task", return_value=mock_task_id
    ):
        resp = await auth_client.post(
            f"/api/v1/projects/{project_id}/pricelist/map",
            json={
                "structure": {
                    "name_column": "Наименование",
                    "unit_column": "Ед.изм.",
                    "price_column": "Цена",
                    "raw_columns": [],
                }
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["task_id"] == mock_task_id


@pytest.mark.asyncio
async def test_get_task_status(auth_client: AsyncClient, project_id: str) -> None:
    from app.services.pricelist_service import _TASK_REGISTRY
    from app.schemas.pricelist import PricelistMapStatus

    task_id = str(uuid.uuid4())
    _TASK_REGISTRY[task_id] = PricelistMapStatus(
        status="running", progress=5, total=10, matches=[]
    )

    resp = await auth_client.get(
        f"/api/v1/projects/{project_id}/pricelist/map/status?task_id={task_id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["progress"] == 5
    assert data["total"] == 10


@pytest.mark.asyncio
async def test_get_task_status_not_found(
    auth_client: AsyncClient, project_id: str
) -> None:
    resp = await auth_client.get(
        f"/api/v1/projects/{project_id}/pricelist/map/status?task_id=nonexistent"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_matches(auth_client: AsyncClient, project_id: str, db_session) -> None:
    """Directly insert a pricelist match and test manual correction."""
    import types
    from unittest.mock import patch
    import uuid as _uuid
    from openpyxl import Workbook

    buf = io.BytesIO()
    wb = Workbook()
    wb.active.append(["header"])
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    mock_item = types.SimpleNamespace(
        number=1, code="CODE", name="Кирпич",
        unit="шт", quantity=100.0, unit_price=50.0,
        total_price=5000.0, item_type="material", section="",
    )
    mock_material = types.SimpleNamespace(
        name="Кирпич", unit="шт", quantity=100.0, smeta_total=5000.0, codes=[],
    )
    mock_result = types.SimpleNamespace(items=[mock_item])

    with (
        patch("app.services.smeta_service.parse_excel", return_value=mock_result),
        patch("app.services.smeta_service.aggregate_materials", return_value=[mock_material]),
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

    # Upload pricelist
    pl_bytes = _make_xlsx_bytes()
    await auth_client.post(
        f"/api/v1/projects/{project_id}/pricelist/upload",
        files={
            "file": (
                "pricelist.xlsx",
                io.BytesIO(pl_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    # Seed a PricelistMatch via db_session
    from app.models.material import Material as _Mat
    from app.models.pricelist import PricelistMatch as _PM
    from sqlalchemy import select as _sel
    mat_res = await db_session.execute(_sel(_Mat).where(_Mat.project_id == _uuid.UUID(project_id)))
    mat = mat_res.scalar_one()
    pm = _PM(
        project_id=_uuid.UUID(project_id),
        material_id=mat.id,
        supplier_name="Старое название",
        supplier_price=70.0,
        confidence=0.6,
        status="pending",
    )
    db_session.add(pm)
    await db_session.commit()
    match_id = str(pm.id)

    resp = await auth_client.put(
        f"/api/v1/projects/{project_id}/pricelist/matches",
        json={
            "updates": [
                {"id": match_id, "supplier_price": 95.0, "status": "accepted"}
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["supplier_price"] == 95.0
    assert data[0]["status"] == "accepted"

    # Verify price was saved to supplier library
    from app.models.pricelist import SupplierPriceLibrary as _SPL
    lib_res = await db_session.execute(_sel(_SPL))
    lib_entries = lib_res.scalars().all()
    assert len(lib_entries) == 1
    assert lib_entries[0].normalized_name == "кирпич"
    assert float(lib_entries[0].price) == 95.0
