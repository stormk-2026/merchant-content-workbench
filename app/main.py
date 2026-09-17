"""HTTP 适配层：解析表单、调用服务、渲染页面，不在这里决定业务审批。"""

import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.database import database_url, make_engine, session_factory
from app.domain import ProductInput
from app.services import DuplicateSku, create_product, get_product, list_products

ROOT = Path(__file__).parent
LABELS = {
    "sku": "款号",
    "name": "名称",
    "colors": "颜色",
    "sizes": "尺码",
    "material": "已确认材质",
    "selling_points": "已确认卖点",
}


def create_app(engine=None):
    app = FastAPI(title="商品内容制作与审核工作台", docs_url=None, redoc_url=None)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    sessions = session_factory(engine if engine is not None else make_engine(database_url()))
    templates = Jinja2Templates(directory=ROOT / "templates")
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'none'; frame-ancestors 'none'; "
            "form-action 'self'; base-uri 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def render(request, template, status=200, **values):
        return templates.TemplateResponse(
            request=request, name=template, context=values, status_code=status
        )

    def product_form(request, status=200, values=None, errors=None):
        token = request.cookies.get("csrf_token") or secrets.token_urlsafe(32)
        response = render(
            request,
            "product_form.html",
            status=status,
            values=values or {},
            errors=errors or [],
            csrf_token=token,
        )
        response.set_cookie("csrf_token", token, httponly=True, samesite="strict")
        return response

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        with sessions() as session:
            return render(request, "products.html", products=list_products(session))

    @app.get("/products/new", response_class=HTMLResponse)
    def new_product(request: Request):
        return product_form(request)

    @app.post("/products")
    async def save_product(request: Request):
        async with request.form(max_fields=10, max_files=0, max_part_size=16384) as form:
            cookie = request.cookies.get("csrf_token", "")
            supplied = str(form.get("csrf_token", ""))
            if not cookie or not secrets.compare_digest(cookie, supplied):
                return render(
                    request,
                    "error.html",
                    status=403,
                    message="表单校验失败，请重新打开录入页面后提交。",
                )
            values = {key: str(form.get(key, "")) for key in LABELS}
        payload = values.copy()
        for key in ("colors", "sizes", "selling_points"):
            payload[key] = values[key].splitlines()
        try:
            facts = ProductInput(**payload)
        except ValidationError as exc:
            errors = []
            for error in exc.errors():
                label = LABELS.get(error["loc"][0], "商品信息")
                message = (
                    "必填，请输入有效内容。"
                    if error["type"] == "string_too_short"
                    else "内容超出限制或格式不正确，请检查字段提示。"
                )
                errors.append(f"{label}：{message}")
            return product_form(request, 422, values, errors)
        with sessions() as session:
            try:
                product = create_product(session, facts)
            except DuplicateSku as exc:
                return product_form(request, 409, values, [str(exc)])
            return RedirectResponse(f"/products/{product.id}", status_code=303)

    @app.get("/products/{product_id}", response_class=HTMLResponse)
    def product_detail(request: Request, product_id: int):
        with sessions() as session:
            product = get_product(session, product_id)
            if product is None:
                return render(request, "error.html", status=404, message="未找到该商品。")
            return render(request, "product_detail.html", product=product)

    return app


app = create_app()
