"""
Tests de integración para los endpoints de consultas básicas.
Requieren una BD de test configurada en TEST_DATABASE_URL.
Ejecutar con: pytest tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_drivers(client):
    r = await client.get("/api/drivers?page_size=10")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_list_drivers_search(client):
    r = await client.get("/api/drivers?search=Hamilton")
    assert r.status_code == 200
    items = r.json()["items"]
    assert any("Hamilton" in (i.get("surname", "")) for i in items)


@pytest.mark.asyncio
async def test_driver_not_found(client):
    r = await client.get("/api/drivers/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_constructors(client):
    r = await client.get("/api/constructors?page_size=10")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_list_circuits(client):
    r = await client.get("/api/circuits")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_list_races_by_year(client):
    r = await client.get("/api/races?year=2023")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0


@pytest.mark.asyncio
async def test_driver_standings(client):
    r = await client.get("/api/standings/drivers/2023")
    assert r.status_code == 200
    standings = r.json()
    assert len(standings) > 0
    assert standings[0]["position"] == 1


@pytest.mark.asyncio
async def test_head_to_head_same_driver_error(client):
    r = await client.get("/api/analysis/head-to-head?driver_a=1&driver_b=1")
    assert r.status_code == 400
