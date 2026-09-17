"""商品事实规则：不依赖 HTTP、数据库或模型供应商。"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ShortFact = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    colors: list[ShortFact] = Field(default_factory=list, max_length=30)
    sizes: list[ShortFact] = Field(default_factory=list, max_length=30)
    material: str | None = Field(default=None, max_length=1000)
    selling_points: list[ShortFact] = Field(default_factory=list, max_length=30)

    @field_validator("material", mode="before")
    @classmethod
    def normalize_material(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @field_validator("colors", "sizes", "selling_points")
    @classmethod
    def normalize_list(cls, values):
        return list(dict.fromkeys(value for value in values if value))
