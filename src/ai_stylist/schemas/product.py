from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str
    description: str | None = None
    category: str
    brand: str | None = None
    color: list[str] = Field(default_factory=list)
    size: list[str] = Field(default_factory=list)
    material: str | None = None
    price: float | None = None
    currency: str = "VND"
    product_url: str | None = None
    image_url: str | None = None
    stock_status: str = "in_stock"
    rating: float | None = None
    review_count: int | None = None
    sales_count: int | None = None
