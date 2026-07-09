from pydantic import BaseModel, Field


class Category(BaseModel):
    """Mirrors Java product-service's Category/CategorySummaryResponse."""
    slug: str | None = None
    name: str


class ProductImage(BaseModel):
    """Mirrors Java product-service's ProductImage/ProductImageResponse."""
    image_url: str
    image_public_id: str | None = None
    is_primary: bool = False


class ProductVariant(BaseModel):
    """Mirrors Java product-service's ProductVariant/ProductVariantResponse."""
    id: str
    product_id: str
    sku: str
    size: str
    color: str
    material: str | None = None
    price_override: float | None = None
    stock_quantity: int = 0
    active: bool = True


class Product(BaseModel):
    """
    Mirrors Java product-service's Product/ProductResponse (id -> product_id,
    basePrice -> base_price, targetDemographic/status kept verbatim). Java has
    no brand/rating/review_count/sales_count/currency/product_url, so this
    schema doesn't carry them either.
    """
    product_id: str
    name: str
    description: str | None = None
    base_price: float
    target_demographic: str = "UNISEX"
    status: str = "ACTIVE"
    categories: list[Category] = Field(default_factory=list)
    variants: list[ProductVariant] = Field(default_factory=list)
    images: list[ProductImage] = Field(default_factory=list)
    # Recommendation-slot classification (top/bottom/dress/shoes/bag/accessory).
    # Python-only concept derived from `categories`; Java has no equivalent field.
    slot: str = "product"

    @property
    def primary_image_url(self) -> str | None:
        for image in self.images:
            if image.is_primary:
                return image.image_url
        return self.images[0].image_url if self.images else None

    @property
    def colors(self) -> list[str]:
        return list(dict.fromkeys(v.color for v in self.variants))

    @property
    def sizes(self) -> list[str]:
        return list(dict.fromkeys(v.size for v in self.variants))

    @property
    def material(self) -> str | None:
        return next((v.material for v in self.variants if v.material), None)

    @property
    def category_names(self) -> list[str]:
        return [c.name for c in self.categories]
