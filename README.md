# 商品内容制作与审核工作台

面向服饰商品详情文案的本地单用户作品。**当前仅完成 M1 商品事实底座**；没有真实客户验证，不代表商用系统或已完成 AI 闭环。

## 安装与运行

要求 Python 3.11、uv 和 Git。当前验证平台是 macOS arm64。
从项目根目录执行：

```sh
uv sync --locked --python python3.11
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 。终端 Ctrl+C 停止服务；重新启动保留商品数据。
默认数据库 `workbench.db` 位于项目根目录，已排除 Git。不自动建表，必须先运行迁移。
`WORKBENCH_DATABASE_URL` 可通过 shell 环境变量覆盖默认路径；M1 不自动加载 `.env`，也不需要模型密钥。不要监听 `0.0.0.0`，当前没有多用户身份认证。

依赖由 `pyproject.toml` 声明、`uv.lock` 锁定；当前 Python 限制在 3.11 系列是为了缩小首版验证矩阵。

## 测试与检查

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run alembic check
```

已建立 `.venv` 后也可以使用 `.venv/bin/python -m pytest -q`、`.venv/bin/ruff check .` 等直接调用环境内工具；这不更改依赖管理方式。

真实 HTTP 冒烟（先启动上面的服务）：

```sh
uv run python scripts/smoke_http.py
```

每次冒烟会在本地库新增一件带 `DEMO-M1-` 前缀的自制样例，不调用模型。单元/集成测试使用临时数据库，不修改工作数据库。迁移测试中的降级只作用于临时库，不要对有用数据执行降级。

## 当前功能

- 款号、名称必填；颜色、尺码、已确认材质、卖点可留空。
- 文本长度校验、款号唯一（区分大小写），错误时保留表单输入。
- 商品列表、录入和详情页；未知信息显示“未确认”。
- SQLite 持久化；任务和草稿版本的最小数据结构及数据库约束。
- 模板转义、表单 CSRF 校验、本机 Host 限制和基本安全响应头。

## 已知限制

- 无生成调用、任务执行器、重启任务恢复、事实冲突检查、审核、编辑和导出。这些属于 M2–M4，不能依据 M1 声称完整闭环。
- 商品记录仅支持新增/查看，暂不支持编辑/删除；列表尚未分页，适合少量学习样例。
- 文本格式通过不意味着内容真实；M1 只保存使用者陈述的事实。
- 任务表中的 `running` 不会自动转成成功。任务执行/中断恢复在 M2 实现，M1 页面不会创建任务。
- Starlette 测试客户端报告两条上游弃用警告：httpx 接口和 AnyIO BlockingPortal 别名。当前锁定组合测试通过，未隐藏警告，后续更新依赖时复查。
- 已验证 HTTP 行为和模板输出，未完成多浏览器、屏幕阅读器或完整视觉/键盘人工验收。
- 数据为本地明文 SQLite，没有认证、多租户或生产运维能力。只用于约定的本机单用户场景。

## 阅读入口

- 产品边界：[docs/PRODUCT_CONTRACT.md](docs/PRODUCT_CONTRACT.md)
- 开发约束：[AGENTS.md](AGENTS.md)
- 分阶段计划：[docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
