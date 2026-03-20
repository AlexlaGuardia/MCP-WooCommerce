"""Tests for mcp-woocommerce server — tool registration and client validation."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from mcp_woocommerce.client import WooCommerceClient, WooCommerceError
from mcp_woocommerce import server


# ── Client Tests ─────────────────────────────────────────────────────


class TestWooCommerceClient:
    def test_base_url_construction(self):
        client = WooCommerceClient(
            "https://mystore.com", "ck_test", "cs_test"
        )
        assert client.base_url == "https://mystore.com/wp-json/wc/v3"

    def test_base_url_trailing_slash(self):
        client = WooCommerceClient(
            "https://mystore.com/", "ck_test", "cs_test"
        )
        assert client.base_url == "https://mystore.com/wp-json/wc/v3"

    def test_base_url_already_has_api_path(self):
        client = WooCommerceClient(
            "https://mystore.com/wp-json/wc/v3", "ck_test", "cs_test"
        )
        assert client.base_url == "https://mystore.com/wp-json/wc/v3"

    def test_store_url_stored(self):
        client = WooCommerceClient(
            "https://mystore.com/", "ck_test", "cs_test"
        )
        assert client.store_url == "https://mystore.com"


class TestWooCommerceError:
    def test_error_format(self):
        err = WooCommerceError("woocommerce_rest_invalid_id", "Invalid ID.", 404)
        assert err.code == "woocommerce_rest_invalid_id"
        assert err.message == "Invalid ID."
        assert err.status == 404
        assert "404" in str(err)


# ── Server Singleton Tests ───────────────────────────────────────────


class TestGetClient:
    def setup_method(self):
        server._client = None

    def teardown_method(self):
        server._client = None

    def test_missing_env_vars_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="WOOCOMMERCE_URL"):
                server.get_client()

    def test_valid_env_vars(self):
        with patch.dict(os.environ, {
            "WOOCOMMERCE_URL": "https://test.com",
            "WOOCOMMERCE_KEY": "ck_test",
            "WOOCOMMERCE_SECRET": "cs_test",
        }):
            client = server.get_client()
            assert isinstance(client, WooCommerceClient)
            assert client.store_url == "https://test.com"

    def test_singleton_returns_same_instance(self):
        with patch.dict(os.environ, {
            "WOOCOMMERCE_URL": "https://test.com",
            "WOOCOMMERCE_KEY": "ck_test",
            "WOOCOMMERCE_SECRET": "cs_test",
        }):
            c1 = server.get_client()
            c2 = server.get_client()
            assert c1 is c2


# ── Tool Registration Tests ──────────────────────────────────────────


class TestToolRegistration:
    """Verify all 34 tools are registered on the FastMCP instance."""

    def test_tool_count(self):
        tools = server.mcp._tool_manager._tools
        assert len(tools) == 34, f"Expected 34 tools, got {len(tools)}: {list(tools.keys())}"

    def test_core_tools_exist(self):
        tools = server.mcp._tool_manager._tools
        expected = [
            "ping",
            # Products
            "list_products", "get_product", "create_product", "update_product",
            "delete_product", "search_products", "list_product_categories",
            # Orders
            "list_orders", "get_order", "create_order", "update_order_status",
            "list_order_notes", "create_order_note", "create_refund",
            # Customers
            "list_customers", "get_customer", "create_customer", "search_customers",
            # Coupons
            "list_coupons", "get_coupon", "create_coupon", "delete_coupon",
            # Reports
            "get_sales_report", "get_top_sellers", "get_order_totals", "get_product_totals",
            # Shipping & Payments
            "list_shipping_zones", "list_payment_gateways", "list_tax_rates",
            # Webhooks
            "list_webhooks", "create_webhook", "delete_webhook",
            # System
            "get_system_status",
        ]
        for name in expected:
            assert name in tools, f"Missing tool: {name}"


# ── Format Helper Tests ──────────────────────────────────────────────


class TestFormat:
    def test_fmt_returns_json(self):
        result = server._fmt({"key": "value"})
        assert '"key": "value"' in result

    def test_fmt_handles_non_serializable(self):
        from datetime import datetime
        result = server._fmt({"dt": datetime(2026, 1, 1)})
        assert "2026" in result
