def test_b06_unknown_product_returns_404(clients):
    assert clients.product.get("/products/9999").status_code == 404


def test_b07_product_price_is_json_number(clients):
    product = clients.product.get("/products/100").json()
    assert type(product["price"]) in (float, int)


def test_b07_product_uses_documented_stock_field(clients):
    product = clients.product.get("/products/100").json()
    assert product.get("stock") == 5
    assert "inStock" not in product


def test_b07_list_and_detail_share_product_contract(clients):
    listed = clients.product.get("/products").json()["items"]
    for product in listed:
        detail = clients.product.get(f'/products/{product["product_id"]}').json()
        assert set(detail) == {"product_id", "name", "price", "stock"}
        assert detail == product


def test_known_product_is_available(clients):
    assert clients.product.get("/products/100").status_code == 200
