"""本地真实 HTTP 冒烟：写入一件明确标识的自制样例，不调用模型。"""

import re
from uuid import uuid4

import httpx

with httpx.Client(base_url="http://127.0.0.1:8000", follow_redirects=False) as client:
    assert client.get("/").status_code == 200
    form = client.get("/products/new")
    assert form.status_code == 200
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text)[1]
    sku = f"DEMO-M1-{uuid4().hex[:8]}"
    sample = {
        "csrf_token": token,
        "sku": sku,
        "name": "自制演示衬衫（非客户资料）",
        "colors": "白色\n蓝色",
        "sizes": "M\nL",
        "material": "",
        "selling_points": "自制样例：有胸前口袋",
    }
    created = client.post("/products", data=sample)
    assert created.status_code == 303
    detail = client.get(created.headers["location"])
    assert detail.status_code == 200
    assert "未确认（留空）" in detail.text
    assert "生成服务未配置" in detail.text
    assert client.post("/products", data=sample).status_code == 409
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/products/99999").status_code == 404
    print("HTTP: list=200, form=200, create=303, detail=200, duplicate=409, CSS=200, missing=404")
    print(f"Self-authored sample: {sku}, {created.headers['location']}; material remains empty")
