import pytest
from fastapi.testclient import TestClient

import app.main as main_module


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    public = tmp_path / "public"
    (public / "assets").mkdir(parents=True)
    (public / "index.html").write_text("<div id=root></div>", encoding="utf-8")
    (public / "assets" / "index-abc.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("não pode vazar", encoding="utf-8")
    monkeypatch.setattr(main_module, "PUBLIC_DIR", public)
    return TestClient(main_module.app)


@pytest.mark.parametrize("path", ["/", "/transacoes", "/financeiro/cartoes"])
def test_react_routes_get_index_html_without_cache(client, path):
    """F5 numa rota do React Router precisa devolver o app, não 404."""
    response = client.get(path)
    assert response.status_code == 200
    assert "<div id=root>" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_existing_static_file_is_served(client):
    response = client.get("/assets/index-abc.js")
    assert response.status_code == 200
    assert "console.log" in response.text


def test_missing_asset_is_404_not_index_html(client):
    """Chunk de um deploy anterior: devolver HTML com status 200 quebraria o carregamento."""
    assert client.get("/assets/index-antigo.js").status_code == 404


def test_unknown_api_route_stays_json_404(client):
    response = client.get("/api/v1/nao-existe")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


def test_api_and_health_routes_are_not_shadowed(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/v1/auth/me").status_code == 401


def test_path_traversal_outside_public_is_blocked(client):
    response = client.get("/..%2Fsegredo.txt")
    assert "não pode vazar" not in response.text
    assert response.status_code == 404


def test_without_frontend_build_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "PUBLIC_DIR", tmp_path / "nao-existe")
    assert TestClient(main_module.app).get("/transacoes").status_code == 404


def test_head_request_on_react_route_is_accepted(client):
    """Previews de link e monitores de uptime usam HEAD — antes dava 405."""
    response = client.head("/transacoes")
    assert response.status_code == 200
