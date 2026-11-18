from app.schemas.evals import GoldenTestCase

GOLDEN_BENCHMARK_CASES: list[GoldenTestCase] = [
    GoldenTestCase(
        id="golden_01",
        question="List the 5 most expensive active products with their prices",
        category="Filtering & Sorting",
        difficulty="easy",
        golden_sql=(
            "SELECT id, name, unit_price FROM ecommerce.products "
            "WHERE is_active = true ORDER BY unit_price DESC LIMIT 5;"
        ),
        description="Tests single-table filtering on boolean flag and descending numeric sort with LIMIT.",
    ),
    GoldenTestCase(
        id="golden_02",
        question="Count of customers grouped by customer segment",
        category="Aggregation",
        difficulty="easy",
        golden_sql=(
            "SELECT segment, COUNT(*) AS customer_count FROM ecommerce.customers "
            "GROUP BY segment ORDER BY customer_count DESC;"
        ),
        description="Tests straightforward GROUP BY aggregation with descending count ordering.",
    ),
    GoldenTestCase(
        id="golden_03",
        question="Total delivered revenue and order count by customer segment",
        category="Joins & Aggregation",
        difficulty="medium",
        golden_sql=(
            "SELECT c.segment, COUNT(o.id) AS order_count, ROUND(SUM(o.total_amount), 2) AS total_revenue "
            "FROM ecommerce.orders o "
            "JOIN ecommerce.customers c ON c.id = o.customer_id "
            "WHERE o.status = 'delivered' "
            "GROUP BY c.segment ORDER BY total_revenue DESC;"
        ),
        description="Tests 2-table join between orders and customers with status filtering and numeric rounding.",
    ),
    GoldenTestCase(
        id="golden_04",
        question="Top 5 product categories by total sales volume (quantity sold)",
        category="Joins & Aggregation",
        difficulty="medium",
        golden_sql=(
            "SELECT cat.name AS category_name, SUM(oi.quantity) AS total_units_sold "
            "FROM ecommerce.order_items oi "
            "JOIN ecommerce.products p ON p.id = oi.product_id "
            "JOIN ecommerce.categories cat ON cat.id = p.category_id "
            "JOIN ecommerce.orders o ON o.id = oi.order_id "
            "WHERE o.status = 'delivered' "
            "GROUP BY cat.name ORDER BY total_units_sold DESC LIMIT 5;"
        ),
        description="Tests complex 4-table join traversals through order items and categories.",
    ),
    GoldenTestCase(
        id="golden_05",
        question="Products with stock quantity strictly below their reorder level",
        category="Filtering & Joins",
        difficulty="medium",
        golden_sql=(
            "SELECT p.name AS product_name, i.warehouse_code, i.stock_quantity, i.reorder_level "
            "FROM ecommerce.inventory i "
            "JOIN ecommerce.products p ON p.id = i.product_id "
            "WHERE i.stock_quantity < i.reorder_level "
            "ORDER BY i.stock_quantity ASC LIMIT 10;"
        ),
        description="Tests comparative column filtering across join boundaries.",
    ),
    GoldenTestCase(
        id="golden_06",
        question="Total amount paid and count of payments by payment method for captured payments",
        category="Aggregation",
        difficulty="medium",
        golden_sql=(
            "SELECT payment_method, COUNT(*) AS payment_count, ROUND(SUM(amount), 2) AS total_paid "
            "FROM ecommerce.payments "
            "WHERE status = 'captured' "
            "GROUP BY payment_method ORDER BY total_paid DESC;"
        ),
        description="Tests payment status semantics and sum aggregation.",
    ),
    GoldenTestCase(
        id="golden_07",
        question="Top 5 products with highest average review rating having at least 3 reviews",
        category="HAVING & Aggregation",
        difficulty="hard",
        golden_sql=(
            "SELECT p.name AS product_name, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.id) AS review_count "
            "FROM ecommerce.reviews r "
            "JOIN ecommerce.products p ON p.id = r.product_id "
            "GROUP BY p.id, p.name "
            "HAVING COUNT(r.id) >= 3 "
            "ORDER BY avg_rating DESC, review_count DESC LIMIT 5;"
        ),
        description="Tests HAVING clause filtering on aggregate review counts with dual-column sorting.",
    ),
    GoldenTestCase(
        id="golden_08",
        question="Monthly delivered order count and revenue for year 2025",
        category="Date Functions & Trends",
        difficulty="hard",
        golden_sql=(
            "SELECT DATE_TRUNC('month', placed_at) AS order_month, COUNT(*) AS orders_count, "
            "ROUND(SUM(total_amount), 2) AS monthly_revenue "
            "FROM ecommerce.orders "
            "WHERE status = 'delivered' AND placed_at >= '2025-01-01' AND placed_at < '2026-01-01' "
            "GROUP BY DATE_TRUNC('month', placed_at) ORDER BY order_month ASC;"
        ),
        description="Tests DATE_TRUNC timestamp grouping and bounded interval date filtering.",
    ),
    GoldenTestCase(
        id="golden_09",
        question="Top 3 highest spending customers with their segment and total delivered spend",
        category="Multi-Join & Ranking",
        difficulty="hard",
        golden_sql=(
            "SELECT c.id AS customer_id, c.full_name, c.segment, ROUND(SUM(o.total_amount), 2) AS lifetime_spend "
            "FROM ecommerce.customers c "
            "JOIN ecommerce.orders o ON o.customer_id = c.id "
            "WHERE o.status = 'delivered' "
            "GROUP BY c.id, c.full_name, c.segment ORDER BY lifetime_spend DESC LIMIT 3;"
        ),
        description="Tests customer lifetime value aggregation with multiple non-aggregate group keys.",
    ),
    GoldenTestCase(
        id="golden_10",
        question="Delivered orders and total spend grouped by default shipping state",
        category="Geographic & Distinct",
        difficulty="hard",
        golden_sql=(
            "SELECT a.state, COUNT(DISTINCT o.id) AS order_count, ROUND(SUM(o.total_amount), 2) AS state_revenue "
            "FROM ecommerce.orders o "
            "JOIN ecommerce.customers c ON c.id = o.customer_id "
            "JOIN ecommerce.addresses a ON a.customer_id = c.id "
            "WHERE o.status = 'delivered' AND a.is_default = true "
            "GROUP BY a.state ORDER BY state_revenue DESC LIMIT 5;"
        ),
        description="Tests COUNT(DISTINCT) over multi-table joins to avoid fanout cartesian inflation.",
    ),
]
