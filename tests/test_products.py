import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain import ProductInput
from app.models import Base, DraftVersion, GenerationTask
from app.services import DuplicateSku, create_product


def test_unknown_facts_remain_empty():
    product = ProductInput(sku=" A001 ", name=" 衬衫 ")
    assert product.sku == "A001"
    assert product.name == "衬衫"
    assert product.colors == []
    assert product.sizes == []
    assert product.material is None
    assert product.selling_points == []


@pytest.mark.parametrize("field", ["sku", "name"])
def test_required_fields_reject_whitespace(field):
    values = {"sku": "A001", "name": "衬衫", field: "  "}
    with pytest.raises(ValidationError):
        ProductInput(**values)


def test_empty_optional_values_and_lists_are_normalized():
    product = ProductInput(sku="A001", name="衬衫", material="  ", colors=[" 白色 ", "", "白色"])
    assert product.material is None
    assert product.colors == ["白色"]


@pytest.mark.parametrize("values", [{"sku": "x" * 65}, {"colors": ["x"] * 31}])
def test_input_limits(values):
    with pytest.raises(ValidationError):
        ProductInput(**({"sku": "A001", "name": "衬衫"} | values))


def test_duplicate_sku_and_persistence(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        product = create_product(session, ProductInput(sku="A001", name="衬衫"))
        product_id = product.id
        with pytest.raises(DuplicateSku):
            create_product(session, ProductInput(sku=" A001 ", name="另一个商品"))
        task = GenerationTask(product_id=product_id)
        session.add(task)
        session.flush()
        session.add(DraftVersion(product_id=product_id, task_id=task.id, version=1))
        session.commit()
    with Session(engine) as session:
        task = session.scalar(select(GenerationTask))
        draft = session.scalar(select(DraftVersion))
        assert task.status == "pending"
        assert draft.review_status == "unreviewed"
        assert draft.content == {}
        assert task.error_message is None
