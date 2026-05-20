import io
import asyncio

CSV_BYTES = b"name,age\nAlice,30\nBob,25\n"


async def test_upload_single_csv_returns_source_id(client):
    response = await client.post(
        "/api/v1/sources/upload",
        files={"files": ("sales.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "source_ids" in data
    assert len(data["source_ids"]) == 1
    assert data["status"] == "processing"


async def test_upload_multiple_files(client):
    response = await client.post(
        "/api/v1/sources/upload",
        files=[
            ("files", ("a.csv", io.BytesIO(b"x\n1\n"), "text/csv")),
            ("files", ("b.csv", io.BytesIO(b"y\n2\n"), "text/csv")),
        ],
    )
    assert response.status_code == 200
    assert len(response.json()["source_ids"]) == 2


async def test_get_source_returns_status(client):
    up = await client.post(
        "/api/v1/sources/upload",
        files={"files": ("test.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    sid = up.json()["source_ids"][0]
    resp = await client.get(f"/api/v1/sources/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sid
    assert data["filename"] == "test.csv"
    assert data["processing_status"] in {"pending", "processing", "ready", "error"}


async def test_list_sources(client):
    await client.post(
        "/api/v1/sources/upload",
        files={"files": ("a.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    resp = await client.get("/api/v1/sources")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_upload_unsupported_type_rejected(client):
    resp = await client.post(
        "/api/v1/sources/upload",
        files={"files": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


async def test_source_preview(client):
    up = await client.post(
        "/api/v1/sources/upload",
        files={"files": ("test.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    sid = up.json()["source_ids"][0]
    await asyncio.sleep(0.2)
    resp = await client.get(f"/api/v1/sources/{sid}/preview")
    assert resp.status_code in {200, 425}  # 425 = not ready yet


async def test_get_source_404(client):
    resp = await client.get("/api/v1/sources/nonexistent-id")
    assert resp.status_code == 404


async def test_preview_source_404(client):
    resp = await client.get("/api/v1/sources/nonexistent-id/preview")
    assert resp.status_code == 404
