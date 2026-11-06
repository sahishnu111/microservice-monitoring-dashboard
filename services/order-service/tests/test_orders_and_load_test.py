"""Hardening tests for POST /orders and GET /load-test (issue #10)."""

from fastapi.testclient import TestClient

from app import main


def test_create_order_increments_counter_and_returns_201():
    client = TestClient(main.app)
    before = len(main.ORDERS)
    r = client.post("/orders", json={"user_id": 1, "total": 1499.5})
    assert r.status_code == 201
    body = r.json()
    assert body["user_id"] == 1
    assert body["total"] == 1499.5
    assert body["status"] == "pending"
    assert body["id"] == max(o["id"] for o in main.ORDERS)
    assert len(main.ORDERS) == before + 1
    metrics = client.get("/metrics").text
    assert "orders_created_total" in metrics


def test_create_order_rejects_non_positive_total():
    client = TestClient(main.app)
    r = client.post("/orders", json={"user_id": 1, "total": 0})
    assert r.status_code == 422


def test_load_test_rejects_delay_above_max():
    client = TestClient(main.app)
    r = client.get("/load-test", params={"delay_ms": 5001})
    assert r.status_code == 422


def test_load_test_always_errors_when_error_rate_is_one():
    client = TestClient(main.app)
    r = client.get("/load-test", params={"error_rate": 1})
    assert r.status_code == 500


def test_create_order_works_when_orders_list_is_empty(monkeypatch):
    monkeypatch.setattr(main, "ORDERS", [])
    client = TestClient(main.app)
    r = client.post("/orders", json={"user_id": 9, "total": 10.0})
    assert r.status_code == 201
    assert r.json()["id"] == 101
