import pytest

@pytest.mark.asyncio
async def test_health_endpoints(client):
    res_live = await client.get("/api/v1/health/liveness")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "ok"

    res_ready = await client.get("/api/v1/health/readiness")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"

@pytest.mark.asyncio
async def test_demo_login_and_document_listing(client):
    # 1-Click Demo Login
    res = await client.post("/api/v1/auth/demo-login")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user_email"] == "recruiter@tech.com"
    token = data["access_token"]

    # Verify protected document listing
    res_docs = await client.get(
        "/api/v1/documents/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_docs.status_code == 200
    doc_data = res_docs.json()
    assert doc_data["total"] >= 2  # Seeded sample docs

@pytest.mark.asyncio
async def test_chat_stream_and_metrics(client):
    # Demo login
    res = await client.post("/api/v1/auth/demo-login")
    token = res.json()["access_token"]

    # Chat query
    chat_res = await client.post(
        "/api/v1/chat/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Qual a política de MFA e RTO?", "stream": True}
    )
    assert chat_res.status_code == 200
    assert "text/event-stream" in chat_res.headers["content-type"]
    assert "X-RateLimit-Limit" in chat_res.headers

    # Check metrics
    metrics_res = await client.get(
        "/api/v1/chat/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_documents"] >= 2
