from fastapi.testclient import TestClient

import src.main as main


def test_health_endpoint_ok():
    client = TestClient(main.app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_endpoint_returns_503_when_not_connected():
    client = TestClient(main.app)

    main._nats_connection = None

    res = client.get("/ready")
    assert res.status_code == 503
