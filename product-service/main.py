from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="ProductService")


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    price: float = Field(ge=0, allow_inf_nan=False)
    stock: int = Field(ge=0)


class ProductList(BaseModel):
    items: list[Product]


PRODUCTS = [
    Product(product_id=100, name="Keyboard", price=59.99, stock=5),
    Product(product_id=101, name="Mouse", price=29.99, stock=0),
]


@app.get("/products", response_model=ProductList)
async def list_products():
    return ProductList(items=PRODUCTS)


@app.get("/products/{pid}", response_model=Product)
async def get_product(pid: int):
    for product in PRODUCTS:
        if product.product_id == pid:
            return product
    raise HTTPException(404, "Product not found")
