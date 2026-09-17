import re

import pytest
from fastapi.testclient import TestClient

from app.database import make_engine
from app.main import create_app
from app.models import Base


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'web.db'}")
    Base.metadata.create_all(engine)
    with TestClient(create_app(engine)) as client:
        yield client
    engine.dispose()


def form_token(client):
    response = client.get("/products/new")
    assert response.status_code == 200
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text)[1]


def test_create_view_and_escape_untrusted_input(client):
    token = form_token(client)
    response = client.post(
        "/products", data={"csrf_token": token, "sku": "S001", "name": "<script>alert(1)</script>"}
    )
    assert response.status_code == 200
    assert "/products/" in str(response.url)
    assert "&lt;script&gt;" in response.text
    assert "<script>alert(1)</script>" not in response.text
    assert "未确认" in response.text
    assert "生成服务未配置" in response.text
    assert "S001" in client.get("/").text


def test_invalid_form_retains_values_and_shows_chinese_error(client):
    token = form_token(client)
    response = client.post("/products", data={"csrf_token": token, "sku": "KEEP", "name": " "})
    assert response.status_code == 422
    assert 'value="KEEP"' in response.text
    assert "名称：" in response.text


def test_duplicate_submission_does_not_create_second_product(client):
    token = form_token(client)
    data = {"csrf_token": token, "sku": "S001", "name": "测试衬衫"}
    assert client.post("/products", data=data).status_code == 200
    response = client.post("/products", data=data)
    assert response.status_code == 409
    assert "该款号已存在" in response.text


def test_reject_missing_csrf_and_unknown_product(client):
    assert client.post("/products", data={"sku": "S001", "name": "衬衫"}).status_code == 403
    assert client.get("/products/999").status_code == 404


def test_reject_nonlocal_host(client):
    assert client.get("/", headers={"host": "example.com"}).status_code == 400
