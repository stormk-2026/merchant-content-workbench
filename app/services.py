from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain import ProductInput
from app.models import Product


class DuplicateSku(Exception):
    pass


def create_product(session: Session, facts: ProductInput) -> Product:
    product = Product(**facts.model_dump())
    session.add(product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if session.scalar(select(Product.id).where(Product.sku == facts.sku)) is not None:
            raise DuplicateSku("该款号已存在，请查看已有商品。") from None
        raise
    return product


def list_products(session: Session):
    return session.scalars(select(Product).order_by(Product.id.desc())).all()


def get_product(session: Session, product_id: int):
    return session.get(Product, product_id)
