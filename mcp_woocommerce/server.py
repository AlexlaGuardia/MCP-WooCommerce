"""MCP server for the WooCommerce REST API — 32 tools."""

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_woocommerce.client import WooCommerceClient, WooCommerceError

mcp = FastMCP(
    "mcp-woocommerce",
    instructions=(
        "Production-grade MCP server for the WooCommerce REST API v3. "
        "34 tools for products, orders, customers, coupons, reports, "
        "shipping, payments, webhooks, and system management."
    ),
)

# ── Client singleton ─────────────────────────────────────────────────

_client: WooCommerceClient | None = None


def get_client() -> WooCommerceClient:
    global _client
    if _client is None:
        store_url = os.environ.get("WOOCOMMERCE_URL", "")
        key = os.environ.get("WOOCOMMERCE_KEY", "")
        secret = os.environ.get("WOOCOMMERCE_SECRET", "")
        if not store_url or not key or not secret:
            raise ValueError(
                "Required environment variables: WOOCOMMERCE_URL, "
                "WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET. "
                "Generate keys at: WordPress Admin → WooCommerce → "
                "Settings → Advanced → REST API"
            )
        _client = WooCommerceClient(store_url, key, secret)
    return _client


def _fmt(data: Any) -> str:
    """Format response data as indented JSON string."""
    return json.dumps(data, indent=2, default=str)


# ══════════════════════════════════════════════════════════════════════
# STORE
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def ping() -> str:
    """Validate WooCommerce connection and get store info (name, URL, currency, version, timezone)."""
    wc = get_client()
    try:
        data = await wc.get("/system_status")
        env = data.get("environment", {})
        settings = data.get("settings", {})
        return _fmt({
            "status": "connected",
            "store_url": wc.store_url,
            "wc_version": env.get("version", ""),
            "wp_version": env.get("wp_version", ""),
            "currency": settings.get("currency", ""),
            "currency_symbol": settings.get("currency_symbol", ""),
            "timezone": settings.get("timezone", ""),
            "weight_unit": settings.get("weight_unit", ""),
            "dimension_unit": settings.get("dimension_unit", ""),
        })
    except WooCommerceError as e:
        return f"Connection failed: {e}"


# ══════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_products(
    status: str = "",
    category: str = "",
    search: str = "",
    on_sale: bool = False,
    per_page: int = 20,
    page: int = 1,
    orderby: str = "date",
    order: str = "desc",
) -> str:
    """List products. Filter by status (publish, draft, pending, private), category ID, search term, or on_sale flag. Orderby: date, id, title, price, popularity, rating."""
    wc = get_client()
    params: dict[str, Any] = {
        "per_page": min(per_page, 100),
        "page": page,
        "orderby": orderby,
        "order": order,
    }
    if status:
        params["status"] = status
    if category:
        params["category"] = category
    if search:
        params["search"] = search
    if on_sale:
        params["on_sale"] = True
    data = await wc.get("/products", params=params)
    products = []
    for p in data if isinstance(data, list) else []:
        products.append({
            "id": p["id"],
            "name": p.get("name", ""),
            "slug": p.get("slug", ""),
            "status": p.get("status", ""),
            "type": p.get("type", ""),
            "price": p.get("price", ""),
            "regular_price": p.get("regular_price", ""),
            "sale_price": p.get("sale_price", ""),
            "stock_status": p.get("stock_status", ""),
            "stock_quantity": p.get("stock_quantity"),
            "categories": [c.get("name", "") for c in p.get("categories", [])],
            "sku": p.get("sku", ""),
        })
    return _fmt({"count": len(products), "products": products})


@mcp.tool()
async def get_product(product_id: int) -> str:
    """Get full details for a product including pricing, inventory, categories, images, and attributes."""
    wc = get_client()
    p = await wc.get(f"/products/{product_id}")
    return _fmt({
        "id": p["id"],
        "name": p.get("name", ""),
        "slug": p.get("slug", ""),
        "permalink": p.get("permalink", ""),
        "type": p.get("type", ""),
        "status": p.get("status", ""),
        "description": p.get("short_description", "") or p.get("description", "")[:500],
        "sku": p.get("sku", ""),
        "price": p.get("price", ""),
        "regular_price": p.get("regular_price", ""),
        "sale_price": p.get("sale_price", ""),
        "on_sale": p.get("on_sale", False),
        "stock_status": p.get("stock_status", ""),
        "stock_quantity": p.get("stock_quantity"),
        "manage_stock": p.get("manage_stock", False),
        "weight": p.get("weight", ""),
        "dimensions": p.get("dimensions", {}),
        "categories": [{"id": c["id"], "name": c.get("name", "")} for c in p.get("categories", [])],
        "tags": [{"id": t["id"], "name": t.get("name", "")} for t in p.get("tags", [])],
        "images": [{"id": i["id"], "src": i.get("src", "")} for i in p.get("images", [])[:5]],
        "attributes": [
            {"name": a.get("name", ""), "options": a.get("options", [])}
            for a in p.get("attributes", [])
        ],
        "variations": p.get("variations", []),
        "total_sales": p.get("total_sales", 0),
        "average_rating": p.get("average_rating", ""),
        "rating_count": p.get("rating_count", 0),
        "created_at": p.get("date_created", ""),
    })


@mcp.tool()
async def create_product(
    name: str,
    product_type: str = "simple",
    regular_price: str = "",
    description: str = "",
    short_description: str = "",
    sku: str = "",
    manage_stock: bool = False,
    stock_quantity: int = 0,
    categories: str = "",
    status: str = "publish",
) -> str:
    """Create a product. Type: simple, grouped, external, variable. Categories: comma-separated IDs."""
    wc = get_client()
    body: dict[str, Any] = {
        "name": name,
        "type": product_type,
        "status": status,
    }
    if regular_price:
        body["regular_price"] = regular_price
    if description:
        body["description"] = description
    if short_description:
        body["short_description"] = short_description
    if sku:
        body["sku"] = sku
    if manage_stock:
        body["manage_stock"] = True
        body["stock_quantity"] = stock_quantity
    if categories:
        body["categories"] = [
            {"id": int(c.strip())} for c in categories.split(",") if c.strip()
        ]
    p = await wc.post("/products", json=body)
    return _fmt({
        "id": p["id"],
        "name": p.get("name", ""),
        "status": p.get("status", ""),
        "type": p.get("type", ""),
        "permalink": p.get("permalink", ""),
        "message": "Product created.",
    })


@mcp.tool()
async def update_product(
    product_id: int,
    name: str = "",
    regular_price: str = "",
    sale_price: str = "",
    status: str = "",
    stock_quantity: int = -1,
    description: str = "",
    sku: str = "",
) -> str:
    """Update a product. Only provide fields you want to change. Set sale_price to empty string to remove sale."""
    wc = get_client()
    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if regular_price:
        body["regular_price"] = regular_price
    if sale_price is not None:
        body["sale_price"] = sale_price
    if status:
        body["status"] = status
    if stock_quantity >= 0:
        body["stock_quantity"] = stock_quantity
        body["manage_stock"] = True
    if description:
        body["description"] = description
    if sku:
        body["sku"] = sku
    if not body:
        return "No fields provided to update."
    p = await wc.put(f"/products/{product_id}", json=body)
    return _fmt({
        "id": p["id"],
        "name": p.get("name", ""),
        "status": p.get("status", ""),
        "updated_fields": list(body.keys()),
        "message": "Product updated.",
    })


@mcp.tool()
async def delete_product(product_id: int, force: bool = False) -> str:
    """Delete a product. Set force=True for permanent deletion (bypass trash)."""
    wc = get_client()
    params = {"force": force}
    await wc.delete(f"/products/{product_id}", params=params)
    return _fmt({
        "product_id": product_id,
        "permanent": force,
        "message": "Product deleted." if force else "Product moved to trash.",
    })


@mcp.tool()
async def search_products(query: str, per_page: int = 20) -> str:
    """Search products by name or SKU."""
    wc = get_client()
    data = await wc.get("/products", params={
        "search": query,
        "per_page": min(per_page, 100),
    })
    products = []
    for p in data if isinstance(data, list) else []:
        products.append({
            "id": p["id"],
            "name": p.get("name", ""),
            "sku": p.get("sku", ""),
            "price": p.get("price", ""),
            "stock_status": p.get("stock_status", ""),
            "status": p.get("status", ""),
        })
    return _fmt({"query": query, "count": len(products), "products": products})


@mcp.tool()
async def list_product_categories(
    per_page: int = 50,
    page: int = 1,
    parent: int = -1,
) -> str:
    """List product categories. Set parent=0 for top-level only."""
    wc = get_client()
    params: dict[str, Any] = {"per_page": min(per_page, 100), "page": page}
    if parent >= 0:
        params["parent"] = parent
    data = await wc.get("/products/categories", params=params)
    cats = []
    for c in data if isinstance(data, list) else []:
        cats.append({
            "id": c["id"],
            "name": c.get("name", ""),
            "slug": c.get("slug", ""),
            "parent": c.get("parent", 0),
            "count": c.get("count", 0),
        })
    return _fmt({"count": len(cats), "categories": cats})


# ══════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_orders(
    status: str = "",
    customer: int = 0,
    after: str = "",
    before: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List orders. Filter by status (pending, processing, on-hold, completed, cancelled, refunded, failed), customer ID, or date range (ISO 8601)."""
    wc = get_client()
    params: dict[str, Any] = {"per_page": min(per_page, 100), "page": page}
    if status:
        params["status"] = status
    if customer:
        params["customer"] = customer
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    data = await wc.get("/orders", params=params)
    orders = []
    for o in data if isinstance(data, list) else []:
        orders.append({
            "id": o["id"],
            "number": o.get("number", ""),
            "status": o.get("status", ""),
            "total": o.get("total", ""),
            "currency": o.get("currency", ""),
            "customer_id": o.get("customer_id", 0),
            "billing_email": o.get("billing", {}).get("email", ""),
            "billing_name": f"{o.get('billing', {}).get('first_name', '')} {o.get('billing', {}).get('last_name', '')}".strip(),
            "items_count": len(o.get("line_items", [])),
            "payment_method": o.get("payment_method_title", ""),
            "created_at": o.get("date_created", ""),
        })
    return _fmt({"count": len(orders), "orders": orders})


@mcp.tool()
async def get_order(order_id: int) -> str:
    """Get full details for an order including line items, shipping, billing, and payment info."""
    wc = get_client()
    o = await wc.get(f"/orders/{order_id}")
    items = []
    for li in o.get("line_items", []):
        items.append({
            "product_id": li.get("product_id", 0),
            "name": li.get("name", ""),
            "quantity": li.get("quantity", 0),
            "subtotal": li.get("subtotal", ""),
            "total": li.get("total", ""),
            "sku": li.get("sku", ""),
        })
    return _fmt({
        "id": o["id"],
        "number": o.get("number", ""),
        "status": o.get("status", ""),
        "total": o.get("total", ""),
        "subtotal": o.get("subtotal", ""),
        "total_tax": o.get("total_tax", ""),
        "discount_total": o.get("discount_total", ""),
        "shipping_total": o.get("shipping_total", ""),
        "currency": o.get("currency", ""),
        "payment_method": o.get("payment_method_title", ""),
        "transaction_id": o.get("transaction_id", ""),
        "customer_id": o.get("customer_id", 0),
        "billing": {
            "name": f"{o.get('billing', {}).get('first_name', '')} {o.get('billing', {}).get('last_name', '')}".strip(),
            "email": o.get("billing", {}).get("email", ""),
            "phone": o.get("billing", {}).get("phone", ""),
            "address": o.get("billing", {}).get("address_1", ""),
            "city": o.get("billing", {}).get("city", ""),
            "state": o.get("billing", {}).get("state", ""),
            "postcode": o.get("billing", {}).get("postcode", ""),
            "country": o.get("billing", {}).get("country", ""),
        },
        "shipping": {
            "name": f"{o.get('shipping', {}).get('first_name', '')} {o.get('shipping', {}).get('last_name', '')}".strip(),
            "address": o.get("shipping", {}).get("address_1", ""),
            "city": o.get("shipping", {}).get("city", ""),
            "state": o.get("shipping", {}).get("state", ""),
            "postcode": o.get("shipping", {}).get("postcode", ""),
            "country": o.get("shipping", {}).get("country", ""),
        },
        "line_items": items,
        "coupon_lines": [
            {"code": c.get("code", ""), "discount": c.get("discount", "")}
            for c in o.get("coupon_lines", [])
        ],
        "customer_note": o.get("customer_note", ""),
        "created_at": o.get("date_created", ""),
        "completed_at": o.get("date_completed"),
    })


@mcp.tool()
async def create_order(
    customer_id: int = 0,
    status: str = "pending",
    line_items: str = "",
    billing_email: str = "",
    billing_first_name: str = "",
    billing_last_name: str = "",
    payment_method: str = "",
    note: str = "",
) -> str:
    """Create an order. line_items: JSON array of {product_id, quantity} objects. Example: '[{"product_id": 42, "quantity": 2}]'"""
    wc = get_client()
    body: dict[str, Any] = {"status": status}
    if customer_id:
        body["customer_id"] = customer_id
    if line_items:
        body["line_items"] = json.loads(line_items)
    billing: dict[str, str] = {}
    if billing_email:
        billing["email"] = billing_email
    if billing_first_name:
        billing["first_name"] = billing_first_name
    if billing_last_name:
        billing["last_name"] = billing_last_name
    if billing:
        body["billing"] = billing
    if payment_method:
        body["payment_method"] = payment_method
    if note:
        body["customer_note"] = note
    o = await wc.post("/orders", json=body)
    return _fmt({
        "id": o["id"],
        "number": o.get("number", ""),
        "status": o.get("status", ""),
        "total": o.get("total", ""),
        "message": "Order created.",
    })


@mcp.tool()
async def update_order_status(order_id: int, status: str) -> str:
    """Update an order's status. Status: pending, processing, on-hold, completed, cancelled, refunded, failed."""
    wc = get_client()
    o = await wc.put(f"/orders/{order_id}", json={"status": status})
    return _fmt({
        "id": o["id"],
        "number": o.get("number", ""),
        "status": o.get("status", ""),
        "message": f"Order status updated to '{status}'.",
    })


@mcp.tool()
async def list_order_notes(order_id: int) -> str:
    """List all notes on an order (internal staff notes and customer-facing notes)."""
    wc = get_client()
    data = await wc.get(f"/orders/{order_id}/notes")
    notes = []
    for n in data if isinstance(data, list) else []:
        notes.append({
            "id": n.get("id", ""),
            "note": n.get("note", ""),
            "customer_note": n.get("customer_note", False),
            "author": n.get("author", ""),
            "created_at": n.get("date_created", ""),
        })
    return _fmt({"order_id": order_id, "count": len(notes), "notes": notes})


@mcp.tool()
async def create_order_note(
    order_id: int,
    note: str,
    customer_note: bool = False,
) -> str:
    """Add a note to an order. Set customer_note=True to make it visible to the customer."""
    wc = get_client()
    n = await wc.post(
        f"/orders/{order_id}/notes",
        json={"note": note, "customer_note": customer_note},
    )
    return _fmt({
        "id": n.get("id", ""),
        "order_id": order_id,
        "customer_note": customer_note,
        "message": "Note added.",
    })


@mcp.tool()
async def create_refund(
    order_id: int,
    amount: str,
    reason: str = "",
) -> str:
    """Create a refund for an order. Amount as string (e.g. '25.00')."""
    wc = get_client()
    body: dict[str, Any] = {"amount": amount}
    if reason:
        body["reason"] = reason
    r = await wc.post(f"/orders/{order_id}/refunds", json=body)
    return _fmt({
        "id": r.get("id", ""),
        "order_id": order_id,
        "amount": r.get("amount", ""),
        "reason": r.get("reason", ""),
        "message": "Refund created.",
    })


# ══════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_customers(
    role: str = "",
    search: str = "",
    per_page: int = 20,
    page: int = 1,
    orderby: str = "registered_date",
    order: str = "desc",
) -> str:
    """List customers. Filter by role (all, administrator, customer) or search by name/email. Orderby: id, include, name, registered_date."""
    wc = get_client()
    params: dict[str, Any] = {
        "per_page": min(per_page, 100),
        "page": page,
        "orderby": orderby,
        "order": order,
    }
    if role:
        params["role"] = role
    if search:
        params["search"] = search
    data = await wc.get("/customers", params=params)
    customers = []
    for c in data if isinstance(data, list) else []:
        customers.append({
            "id": c["id"],
            "email": c.get("email", ""),
            "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
            "username": c.get("username", ""),
            "orders_count": c.get("orders_count", 0),
            "total_spent": c.get("total_spent", ""),
            "avatar_url": c.get("avatar_url", ""),
            "registered_at": c.get("date_created", ""),
        })
    return _fmt({"count": len(customers), "customers": customers})


@mcp.tool()
async def get_customer(customer_id: int) -> str:
    """Get full details for a customer including billing/shipping addresses and order stats."""
    wc = get_client()
    c = await wc.get(f"/customers/{customer_id}")
    return _fmt({
        "id": c["id"],
        "email": c.get("email", ""),
        "first_name": c.get("first_name", ""),
        "last_name": c.get("last_name", ""),
        "username": c.get("username", ""),
        "role": c.get("role", ""),
        "orders_count": c.get("orders_count", 0),
        "total_spent": c.get("total_spent", ""),
        "billing": {
            "email": c.get("billing", {}).get("email", ""),
            "phone": c.get("billing", {}).get("phone", ""),
            "address": c.get("billing", {}).get("address_1", ""),
            "city": c.get("billing", {}).get("city", ""),
            "state": c.get("billing", {}).get("state", ""),
            "postcode": c.get("billing", {}).get("postcode", ""),
            "country": c.get("billing", {}).get("country", ""),
        },
        "shipping": {
            "address": c.get("shipping", {}).get("address_1", ""),
            "city": c.get("shipping", {}).get("city", ""),
            "state": c.get("shipping", {}).get("state", ""),
            "postcode": c.get("shipping", {}).get("postcode", ""),
            "country": c.get("shipping", {}).get("country", ""),
        },
        "registered_at": c.get("date_created", ""),
        "last_active": c.get("date_modified", ""),
    })


@mcp.tool()
async def create_customer(
    email: str,
    first_name: str = "",
    last_name: str = "",
    username: str = "",
) -> str:
    """Create a new customer. Only email is required."""
    wc = get_client()
    body: dict[str, Any] = {"email": email}
    if first_name:
        body["first_name"] = first_name
    if last_name:
        body["last_name"] = last_name
    if username:
        body["username"] = username
    c = await wc.post("/customers", json=body)
    return _fmt({
        "id": c["id"],
        "email": c.get("email", ""),
        "username": c.get("username", ""),
        "message": "Customer created.",
    })


@mcp.tool()
async def search_customers(query: str, per_page: int = 20) -> str:
    """Search customers by name or email."""
    wc = get_client()
    data = await wc.get("/customers", params={
        "search": query,
        "per_page": min(per_page, 100),
    })
    customers = []
    for c in data if isinstance(data, list) else []:
        customers.append({
            "id": c["id"],
            "email": c.get("email", ""),
            "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
            "orders_count": c.get("orders_count", 0),
            "total_spent": c.get("total_spent", ""),
        })
    return _fmt({"query": query, "count": len(customers), "customers": customers})


# ══════════════════════════════════════════════════════════════════════
# COUPONS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_coupons(
    search: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List coupons. Optionally search by code."""
    wc = get_client()
    params: dict[str, Any] = {"per_page": min(per_page, 100), "page": page}
    if search:
        params["search"] = search
    data = await wc.get("/coupons", params=params)
    coupons = []
    for c in data if isinstance(data, list) else []:
        coupons.append({
            "id": c["id"],
            "code": c.get("code", ""),
            "discount_type": c.get("discount_type", ""),
            "amount": c.get("amount", ""),
            "usage_count": c.get("usage_count", 0),
            "usage_limit": c.get("usage_limit"),
            "expiry_date": c.get("date_expires"),
            "free_shipping": c.get("free_shipping", False),
        })
    return _fmt({"count": len(coupons), "coupons": coupons})


@mcp.tool()
async def get_coupon(coupon_id: int) -> str:
    """Get full details for a coupon."""
    wc = get_client()
    c = await wc.get(f"/coupons/{coupon_id}")
    return _fmt({
        "id": c["id"],
        "code": c.get("code", ""),
        "discount_type": c.get("discount_type", ""),
        "amount": c.get("amount", ""),
        "free_shipping": c.get("free_shipping", False),
        "expiry_date": c.get("date_expires"),
        "minimum_amount": c.get("minimum_amount", ""),
        "maximum_amount": c.get("maximum_amount", ""),
        "usage_count": c.get("usage_count", 0),
        "usage_limit": c.get("usage_limit"),
        "usage_limit_per_user": c.get("usage_limit_per_user"),
        "individual_use": c.get("individual_use", False),
        "exclude_sale_items": c.get("exclude_sale_items", False),
        "product_ids": c.get("product_ids", []),
        "excluded_product_ids": c.get("excluded_product_ids", []),
        "email_restrictions": c.get("email_restrictions", []),
        "created_at": c.get("date_created", ""),
    })


@mcp.tool()
async def create_coupon(
    code: str,
    discount_type: str = "percent",
    amount: str = "10",
    free_shipping: bool = False,
    expiry_date: str = "",
    usage_limit: int = 0,
    minimum_amount: str = "",
    individual_use: bool = False,
) -> str:
    """Create a coupon. discount_type: percent, fixed_cart, fixed_product. Amount as string (e.g. '10' for 10% or $10)."""
    wc = get_client()
    body: dict[str, Any] = {
        "code": code,
        "discount_type": discount_type,
        "amount": amount,
    }
    if free_shipping:
        body["free_shipping"] = True
    if expiry_date:
        body["date_expires"] = expiry_date
    if usage_limit:
        body["usage_limit"] = usage_limit
    if minimum_amount:
        body["minimum_amount"] = minimum_amount
    if individual_use:
        body["individual_use"] = True
    c = await wc.post("/coupons", json=body)
    return _fmt({
        "id": c["id"],
        "code": c.get("code", ""),
        "discount_type": c.get("discount_type", ""),
        "amount": c.get("amount", ""),
        "message": "Coupon created.",
    })


@mcp.tool()
async def delete_coupon(coupon_id: int, force: bool = True) -> str:
    """Delete a coupon. force=True for permanent deletion."""
    wc = get_client()
    await wc.delete(f"/coupons/{coupon_id}", params={"force": force})
    return _fmt({"coupon_id": coupon_id, "message": "Coupon deleted."})


# ══════════════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_sales_report(
    period: str = "month",
    date_min: str = "",
    date_max: str = "",
) -> str:
    """Get sales report. Period: week, month, last_month, year. Or provide date_min/date_max (YYYY-MM-DD)."""
    wc = get_client()
    params: dict[str, Any] = {"period": period}
    if date_min:
        params["date_min"] = date_min
    if date_max:
        params["date_max"] = date_max
    data = await wc.get("/reports/sales", params=params)
    # WooCommerce returns an array with one report object
    r = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
    return _fmt({
        "total_sales": r.get("total_sales", ""),
        "net_sales": r.get("net_sales", ""),
        "average_sales": r.get("average_sales", ""),
        "total_orders": r.get("total_orders", 0),
        "total_items": r.get("total_items", 0),
        "total_tax": r.get("total_tax", ""),
        "total_shipping": r.get("total_shipping", ""),
        "total_refunds": r.get("total_refunds", 0),
        "total_discount": r.get("total_discount", ""),
        "total_customers": r.get("total_customers", 0),
        "period": period,
    })


@mcp.tool()
async def get_top_sellers(period: str = "month") -> str:
    """Get top-selling products. Period: week, month, last_month, year."""
    wc = get_client()
    data = await wc.get("/reports/top_sellers", params={"period": period})
    products = []
    for p in data if isinstance(data, list) else []:
        products.append({
            "product_id": p.get("product_id", 0),
            "title": p.get("title", ""),
            "quantity": p.get("quantity", 0),
        })
    return _fmt({"period": period, "count": len(products), "top_sellers": products})


@mcp.tool()
async def get_order_totals() -> str:
    """Get order counts by status (pending, processing, completed, etc.)."""
    wc = get_client()
    data = await wc.get("/reports/orders/totals")
    totals = []
    for t in data if isinstance(data, list) else []:
        totals.append({
            "slug": t.get("slug", ""),
            "name": t.get("name", ""),
            "total": t.get("total", 0),
        })
    return _fmt({"order_totals": totals})


@mcp.tool()
async def get_product_totals() -> str:
    """Get product counts by type (simple, variable, grouped, external)."""
    wc = get_client()
    data = await wc.get("/reports/products/totals")
    totals = []
    for t in data if isinstance(data, list) else []:
        totals.append({
            "slug": t.get("slug", ""),
            "name": t.get("name", ""),
            "total": t.get("total", 0),
        })
    return _fmt({"product_totals": totals})


# ══════════════════════════════════════════════════════════════════════
# SHIPPING & PAYMENTS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_shipping_zones() -> str:
    """List all shipping zones with their methods."""
    wc = get_client()
    zones = await wc.get("/shipping/zones")
    result = []
    for z in zones if isinstance(zones, list) else []:
        zone_id = z.get("id", 0)
        methods = await wc.get(f"/shipping/zones/{zone_id}/methods")
        result.append({
            "id": zone_id,
            "name": z.get("name", ""),
            "order": z.get("order", 0),
            "methods": [
                {
                    "id": m.get("id", ""),
                    "title": m.get("title", ""),
                    "method_id": m.get("method_id", ""),
                    "enabled": m.get("enabled", False),
                }
                for m in (methods if isinstance(methods, list) else [])
            ],
        })
    return _fmt({"count": len(result), "shipping_zones": result})


@mcp.tool()
async def list_payment_gateways() -> str:
    """List all payment gateways with their enabled status and settings."""
    wc = get_client()
    data = await wc.get("/payment_gateways")
    gateways = []
    for g in data if isinstance(data, list) else []:
        gateways.append({
            "id": g.get("id", ""),
            "title": g.get("title", ""),
            "description": g.get("description", ""),
            "enabled": g.get("enabled", False),
            "method_title": g.get("method_title", ""),
            "order": g.get("order", ""),
        })
    return _fmt({"count": len(gateways), "payment_gateways": gateways})


@mcp.tool()
async def list_tax_rates(per_page: int = 50, page: int = 1) -> str:
    """List all tax rates."""
    wc = get_client()
    data = await wc.get("/taxes", params={
        "per_page": min(per_page, 100),
        "page": page,
    })
    rates = []
    for r in data if isinstance(data, list) else []:
        rates.append({
            "id": r.get("id", ""),
            "country": r.get("country", ""),
            "state": r.get("state", ""),
            "postcode": r.get("postcode", ""),
            "city": r.get("city", ""),
            "rate": r.get("rate", ""),
            "name": r.get("name", ""),
            "shipping": r.get("shipping", False),
            "class": r.get("class", "standard"),
        })
    return _fmt({"count": len(rates), "tax_rates": rates})


# ══════════════════════════════════════════════════════════════════════
# WEBHOOKS
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def list_webhooks(per_page: int = 20, page: int = 1) -> str:
    """List all webhooks."""
    wc = get_client()
    data = await wc.get("/webhooks", params={
        "per_page": min(per_page, 100),
        "page": page,
    })
    hooks = []
    for h in data if isinstance(data, list) else []:
        hooks.append({
            "id": h.get("id", ""),
            "name": h.get("name", ""),
            "status": h.get("status", ""),
            "topic": h.get("topic", ""),
            "delivery_url": h.get("delivery_url", ""),
            "created_at": h.get("date_created", ""),
        })
    return _fmt({"count": len(hooks), "webhooks": hooks})


@mcp.tool()
async def create_webhook(
    name: str,
    topic: str,
    delivery_url: str,
    secret: str = "",
    status: str = "active",
) -> str:
    """Create a webhook. Topics: order.created, order.updated, order.deleted, product.created, product.updated, product.deleted, customer.created, customer.updated, coupon.created, coupon.updated, etc."""
    wc = get_client()
    body: dict[str, Any] = {
        "name": name,
        "topic": topic,
        "delivery_url": delivery_url,
        "status": status,
    }
    if secret:
        body["secret"] = secret
    h = await wc.post("/webhooks", json=body)
    return _fmt({
        "id": h.get("id", ""),
        "name": h.get("name", ""),
        "topic": h.get("topic", ""),
        "delivery_url": h.get("delivery_url", ""),
        "status": h.get("status", ""),
        "message": "Webhook created.",
    })


@mcp.tool()
async def delete_webhook(webhook_id: int, force: bool = True) -> str:
    """Delete a webhook."""
    wc = get_client()
    await wc.delete(f"/webhooks/{webhook_id}", params={"force": force})
    return _fmt({"webhook_id": webhook_id, "message": "Webhook deleted."})


# ══════════════════════════════════════════════════════════════════════
# SYSTEM
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_system_status() -> str:
    """Get WooCommerce system status — versions, database, active plugins, server environment, and store diagnostics."""
    wc = get_client()
    data = await wc.get("/system_status")
    env = data.get("environment", {})
    db = data.get("database", {})
    settings = data.get("settings", {})
    active_plugins = [
        {"name": p.get("name", ""), "version": p.get("version", "")}
        for p in data.get("active_plugins", [])
    ]
    return _fmt({
        "environment": {
            "wc_version": env.get("version", ""),
            "wp_version": env.get("wp_version", ""),
            "php_version": env.get("php_version", ""),
            "server_info": env.get("server_info", ""),
            "max_upload_size": env.get("max_upload_size", 0),
            "wp_memory_limit": env.get("wp_memory_limit", 0),
            "wp_debug_mode": env.get("wp_debug_mode", False),
        },
        "database": {
            "wc_database_version": db.get("wc_database_version", ""),
            "database_size": db.get("database_size", {}),
        },
        "store_settings": {
            "currency": settings.get("currency", ""),
            "currency_symbol": settings.get("currency_symbol", ""),
            "taxonomies": settings.get("taxonomies", {}),
        },
        "active_plugins_count": len(active_plugins),
        "active_plugins": active_plugins[:20],
    })


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
