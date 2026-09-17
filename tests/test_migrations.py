from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import make_engine
from app.domain import ProductInput
from app.models import DraftVersion, GenerationTask
from app.services import create_product


def test_migration_round_trip_and_database_constraints(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("WORKBENCH_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = make_engine(url)
    assert set(inspect(engine).get_table_names()) == {
        "alembic_version",
        "products",
        "generation_tasks",
        "draft_versions",
    }
    with Session(engine) as session:
        product = create_product(session, ProductInput(sku="M001", name="迁移样例"))
        session.add(GenerationTask(product_id=product.id, status="running"))
        session.add(DraftVersion(product_id=product.id, version=1))
        session.commit()
    engine.dispose()
    engine = make_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT status FROM generation_tasks")) == "running"
        assert connection.scalar(text("SELECT review_status FROM draft_versions")) == "unreviewed"
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    with Session(engine) as session:
        for task in [
            GenerationTask(product_id=999),
            GenerationTask(product_id=1, status="approved"),
        ]:
            session.add(task)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
            else:
                raise AssertionError("数据库必须拒绝无效外键或任务状态")
    command.check(config)
    engine.dispose()
    command.downgrade(config, "base")
    engine = make_engine(url)
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
    command.upgrade(config, "head")
