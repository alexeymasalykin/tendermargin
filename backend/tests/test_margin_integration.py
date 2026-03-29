"""Integration tests for margin, contractor, materials, and project progress endpoints."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contractor import ContractorPrice
from app.models.material import Material
from app.models.project import Project
from app.models.smeta import SmetaItem, SmetaUpload
from app.models.user import User


async def _get_user_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one()
    return user.id


async def _create_project_with_margin_data(
    db: AsyncSession, user_id: uuid.UUID
) -> uuid.UUID:
    """Insert project + smeta upload + smeta items + contractor prices directly."""
    project = Project(user_id=user_id, name="Margin Test", description="")
    db.add(project)
    await db.flush()

    smeta_upload = SmetaUpload(
        project_id=project.id,
        filename="test.xlsx",
        file_path="/tmp/test.xlsx",
        parsed_at=datetime.now(timezone.utc),
    )
    db.add(smeta_upload)
    await db.flush()

    items = []
    for i, (name, price, qty) in enumerate(
        [
            ("Бетонные работы", Decimal("100000"), Decimal("1")),
            ("Кладка стен", Decimal("50000"), Decimal("2")),
            ("Штукатурка", Decimal("30000"), Decimal("3")),
        ],
        start=1,
    ):
        item = SmetaItem(
            project_id=project.id,
            number=i,
            code=f"ФСН-{i:03d}",
            name=name,
            unit="м2",
            quantity=qty,
            unit_price=price,
            total_price=price * qty,
            item_type="work",
            section="Раздел 1",
        )
        db.add(item)
        items.append(item)

    await db.flush()

    # Add contractor prices for first 2 items only (partial pricing)
    for item, cp_price in zip(items[:2], [Decimal("80000"), Decimal("20000")]):
        cp = ContractorPrice(
            project_id=project.id,
            smeta_item_id=item.id,
            fsnb_code=item.code,
            name=item.name,
            unit=item.unit,
            price=cp_price,
        )
        db.add(cp)

    await db.flush()
    return project.id


class TestMarginEndpoint:
    @pytest.mark.asyncio
    async def test_get_margin(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        resp = await auth_client.get(f"/api/v1/projects/{project_id}/margin")
        assert resp.status_code == 200
        data = resp.json()

        assert "total_ceiling" in data
        assert "total_cost" in data
        assert "total_margin" in data
        assert "items" in data
        assert len(data["items"]) == 3

        # Item 1: ceiling=100000, cost=80000*1=80000, margin=20% → green
        assert data["items"][0]["status"] == "green"
        assert data["items"][0]["ceiling_price"] == 100000.0
        assert data["items"][0]["cost_price"] == 80000.0
        assert data["items"][0]["margin"] == 20000.0
        assert data["items"][0]["margin_pct"] == 20.0

        # Item 2: ceiling=100000, cost=20000*2=40000, margin=60% → green
        assert data["items"][1]["status"] == "green"

        # Item 3: no contractor price → cost=ceiling, margin=0%
        assert data["items"][2]["cost_price"] == data["items"][2]["ceiling_price"]
        assert data["items"][2]["margin"] == 0.0
        assert data["items"][2]["status"] == "red"

        # Totals: ceiling=100000+100000+90000=290000
        assert data["total_ceiling"] == 290000.0

    @pytest.mark.asyncio
    async def test_margin_no_smeta(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/projects", json={"name": "Empty", "description": ""}
        )
        pid = resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/projects/{pid}/margin")
        assert resp.status_code == 400
        assert "smeta" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_margin_no_contractor_prices(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Smeta exists but no contractor prices at all → 400."""
        user_id = await _get_user_id(db_session)
        project = Project(user_id=user_id, name="No Prices", description="")
        db_session.add(project)
        await db_session.flush()

        smeta_upload = SmetaUpload(
            project_id=project.id,
            filename="test.xlsx",
            file_path="/tmp/test.xlsx",
            parsed_at=datetime.now(timezone.utc),
        )
        db_session.add(smeta_upload)
        await db_session.flush()

        item = SmetaItem(
            project_id=project.id,
            number=1,
            code="ФСН-001",
            name="Работы",
            unit="м2",
            quantity=Decimal("1"),
            unit_price=Decimal("10000"),
            total_price=Decimal("10000"),
            item_type="work",
            section="Раздел 1",
        )
        db_session.add(item)
        await db_session.commit()

        resp = await auth_client.get(f"/api/v1/projects/{project.id}/margin")
        assert resp.status_code == 400
        assert "contractor" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_margin_export(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        resp = await auth_client.post(
            f"/api/v1/projects/{project_id}/margin/export"
        )
        assert resp.status_code == 200
        assert (
            "spreadsheet" in resp.headers.get("content-type", "")
            or "octet" in resp.headers.get("content-type", "")
        )
        # Excel file should have meaningful content
        assert len(resp.content) > 100

    @pytest.mark.asyncio
    async def test_margin_export_no_data(self, auth_client: AsyncClient):
        """Export on empty project should also return 400."""
        resp = await auth_client.post(
            "/api/v1/projects", json={"name": "Empty Export", "description": ""}
        )
        pid = resp.json()["id"]

        resp = await auth_client.post(f"/api/v1/projects/{pid}/margin/export")
        assert resp.status_code == 400


class TestContractorEndpoints:
    @pytest.mark.asyncio
    async def test_list_contractor_prices(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        resp = await auth_client.get(
            f"/api/v1/projects/{project_id}/contractor-prices"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # Only 2 items have contractor prices
        # Each item should have required fields
        for item in data:
            assert "id" in item
            assert "smeta_item_id" in item
            assert "fsnb_code" in item
            assert "name" in item
            assert "price" in item
            assert "ceiling_total" in item

    @pytest.mark.asyncio
    async def test_list_contractor_prices_empty(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/projects", json={"name": "No CP", "description": ""}
        )
        pid = resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/projects/{pid}/contractor-prices")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_update_single_contractor_price(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        # Get existing prices
        resp = await auth_client.get(
            f"/api/v1/projects/{project_id}/contractor-prices"
        )
        prices = resp.json()
        smeta_item_id = prices[0]["smeta_item_id"]

        # Update price via single-item endpoint
        resp = await auth_client.put(
            f"/api/v1/projects/{project_id}/contractor-prices/{smeta_item_id}",
            json={"price": 75000},
        )
        assert resp.status_code == 200
        assert resp.json()["price"] == 75000.0

    @pytest.mark.asyncio
    async def test_batch_update_contractor_prices(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        # Get existing prices
        resp = await auth_client.get(
            f"/api/v1/projects/{project_id}/contractor-prices"
        )
        prices = resp.json()

        # Batch update both prices
        updates = [
            {"smeta_item_id": prices[0]["smeta_item_id"], "price": 70000},
            {"smeta_item_id": prices[1]["smeta_item_id"], "price": 25000},
        ]
        resp = await auth_client.put(
            f"/api/v1/projects/{project_id}/contractor-prices",
            json={"prices": updates},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["price"] == 70000.0
        assert data[1]["price"] == 25000.0

    @pytest.mark.asyncio
    async def test_update_nonexistent_contractor_price(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        fake_item_id = str(uuid.uuid4())
        resp = await auth_client.put(
            f"/api/v1/projects/{project_id}/contractor-prices/{fake_item_id}",
            json={"price": 999},
        )
        assert resp.status_code == 404


class TestMaterialsEndpoints:
    @pytest.mark.asyncio
    async def test_list_materials_empty(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/projects", json={"name": "No Materials", "description": ""}
        )
        pid = resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/projects/{pid}/materials")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_materials_with_data(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project = Project(user_id=user_id, name="Mat Test", description="")
        db_session.add(project)
        await db_session.flush()

        mat = Material(
            project_id=project.id,
            name="Цемент М500",
            unit="т",
            quantity=Decimal("10"),
            smeta_total=Decimal("50000"),
            codes=["ФСН-001"],
        )
        db_session.add(mat)
        await db_session.commit()

        resp = await auth_client.get(f"/api/v1/projects/{project.id}/materials")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Цемент М500"
        assert data[0]["unit"] == "т"
        assert data[0]["quantity"] == 10.0
        assert data[0]["smeta_total"] == 50000.0

    @pytest.mark.asyncio
    async def test_export_materials(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project = Project(user_id=user_id, name="Mat Export", description="")
        db_session.add(project)
        await db_session.flush()

        mat = Material(
            project_id=project.id,
            name="Кирпич",
            unit="шт",
            quantity=Decimal("1000"),
            smeta_total=Decimal("100000"),
            codes=[],
        )
        db_session.add(mat)
        await db_session.commit()

        resp = await auth_client.post(
            f"/api/v1/projects/{project.id}/materials/export"
        )
        assert resp.status_code == 200
        assert len(resp.content) > 100

    @pytest.mark.asyncio
    async def test_export_materials_empty(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/projects", json={"name": "Empty Mat Export", "description": ""}
        )
        pid = resp.json()["id"]

        resp = await auth_client.post(f"/api/v1/projects/{pid}/materials/export")
        assert resp.status_code == 200
        # Even empty export should produce valid Excel
        assert len(resp.content) > 50


class TestProjectProgress:
    @pytest.mark.asyncio
    async def test_progress_empty_project(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/projects",
            json={"name": "Progress Test", "description": ""},
        )
        assert resp.status_code == 201
        pid = resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/projects/{pid}")
        assert resp.status_code == 200
        progress = resp.json()["progress"]
        assert progress["smeta"]["status"] == "not_started"
        assert progress["materials"]["status"] == "not_started"
        assert progress["contractor"]["status"] == "not_started"
        assert progress["pricelist"]["status"] == "not_started"
        assert progress["margin"]["available"] is False
        assert progress["margin"]["margin_pct"] is None

    @pytest.mark.asyncio
    async def test_progress_with_smeta_and_contractor(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = await _get_user_id(db_session)
        project_id = await _create_project_with_margin_data(db_session, user_id)
        await db_session.commit()

        resp = await auth_client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        progress = resp.json()["progress"]

        # Smeta: uploaded and parsed with 3 items
        assert progress["smeta"]["status"] == "completed"
        assert progress["smeta"]["item_count"] == 3

        # Contractor: 2 records exist, both have prices → completed
        # (only items WITH ContractorPrice rows are counted)
        assert progress["contractor"]["status"] == "completed"
        assert progress["contractor"]["filled"] == 2
        assert progress["contractor"]["total"] == 2

        # Margin should be available (smeta done + at least one contractor price)
        assert progress["margin"]["available"] is True
        assert progress["margin"]["margin_pct"] is not None
