# mcp-woocommerce

Production-grade MCP server for the **WooCommerce REST API** — 34 tools for products, orders, customers, coupons, reports, shipping, payments, webhooks, and system management.

## Why This Exists

WooCommerce powers **36% of all e-commerce** (5M+ active stores) but has zero comprehensive MCP servers. This fills that gap with 34 production-ready tools covering the entire WooCommerce REST API v3.

## Features

- **34 tools** across 8 categories (products, orders, customers, coupons, reports, shipping/payments, webhooks, system)
- **Full CRUD** for products, orders, customers, and coupons
- **Reports & analytics** — sales reports, top sellers, order totals, product totals
- **Webhook management** — create, list, delete webhooks for real-time event handling
- **System diagnostics** — WooCommerce/WordPress versions, plugins, server environment
- **Shipping zones** with methods, payment gateways, tax rates
- **Production-grade** error handling with typed exceptions
- **Simple auth** — consumer key + secret via environment variables

## Quick Start

### Install

```bash
pip install mcp-woocommerce
```

### Configure

Set your WooCommerce REST API credentials as environment variables:

```bash
export WOOCOMMERCE_URL="https://yourstore.com"
export WOOCOMMERCE_KEY="ck_your_consumer_key"
export WOOCOMMERCE_SECRET="cs_your_consumer_secret"
```

Generate API keys at: **WordPress Admin > WooCommerce > Settings > Advanced > REST API**

### Run

```bash
mcp-woocommerce
```

Or run as a module:

```bash
python -m mcp_woocommerce
```

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "woocommerce": {
      "command": "mcp-woocommerce",
      "env": {
        "WOOCOMMERCE_URL": "https://yourstore.com",
        "WOOCOMMERCE_KEY": "ck_your_consumer_key",
        "WOOCOMMERCE_SECRET": "cs_your_consumer_secret"
      }
    }
  }
}
```

## Tools (32)

### Store
| Tool | Description |
|------|-------------|
| `ping` | Validate connection and get store info |

### Products (7)
| Tool | Description |
|------|-------------|
| `list_products` | List products with filters (status, category, search, on_sale) |
| `get_product` | Full product details (pricing, inventory, images, attributes) |
| `create_product` | Create a product (simple, variable, grouped, external) |
| `update_product` | Update product fields (price, stock, status, etc.) |
| `delete_product` | Delete or trash a product |
| `search_products` | Search by name or SKU |
| `list_product_categories` | List categories with hierarchy |

### Orders (7)
| Tool | Description |
|------|-------------|
| `list_orders` | List orders with filters (status, customer, date range) |
| `get_order` | Full order details (items, billing, shipping, payment) |
| `create_order` | Create an order with line items |
| `update_order_status` | Change order status (pending, processing, completed, etc.) |
| `list_order_notes` | Get all notes on an order |
| `create_order_note` | Add staff or customer-facing notes |
| `create_refund` | Issue a refund |

### Customers (4)
| Tool | Description |
|------|-------------|
| `list_customers` | List customers with filters (role, search) |
| `get_customer` | Full customer details with addresses and order stats |
| `create_customer` | Create a new customer |
| `search_customers` | Search by name or email |

### Coupons (4)
| Tool | Description |
|------|-------------|
| `list_coupons` | List coupons with search |
| `get_coupon` | Full coupon details (restrictions, limits, usage) |
| `create_coupon` | Create percent, fixed cart, or fixed product coupons |
| `delete_coupon` | Delete a coupon |

### Reports (4)
| Tool | Description |
|------|-------------|
| `get_sales_report` | Sales totals by period (week, month, year, custom range) |
| `get_top_sellers` | Top-selling products by period |
| `get_order_totals` | Order counts by status |
| `get_product_totals` | Product counts by type |

### Shipping & Payments (3)
| Tool | Description |
|------|-------------|
| `list_shipping_zones` | Shipping zones with their methods |
| `list_payment_gateways` | Payment gateways with enabled status |
| `list_tax_rates` | All configured tax rates |

### Webhooks (3)
| Tool | Description |
|------|-------------|
| `list_webhooks` | List all webhooks |
| `create_webhook` | Create webhooks for order/product/customer events |
| `delete_webhook` | Delete a webhook |

### System (1)
| Tool | Description |
|------|-------------|
| `get_system_status` | WooCommerce/WordPress versions, plugins, server environment |

## Authentication

WooCommerce uses **consumer key + consumer secret** for REST API auth. This server uses HTTP Basic Authentication over HTTPS.

1. Go to **WordPress Admin > WooCommerce > Settings > Advanced > REST API**
2. Click **Add key**
3. Set permissions to **Read/Write**
4. Copy the consumer key (`ck_...`) and consumer secret (`cs_...`)

> **Important:** Your store must use HTTPS for Basic Auth to work securely.

## Requirements

- Python 3.10+
- WooCommerce 3.5+ with REST API v3
- HTTPS enabled on your store

## License

MIT
