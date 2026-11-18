import argparse
import logging
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, insert, text
from sqlalchemy.engine import Connection

from app.core.config import ConfigurationError, load_settings
from app.modules.database.models.ecommerce import (
    Address,
    Category,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Product,
    Review,
)

logger = logging.getLogger(__name__)

# Fixed UTC reference timestamp guarantees bit-for-bit reproducible dates across runs.
REFERENCE_UTC = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
DEFAULT_SEED = 42


@dataclass(frozen=True, slots=True)
class SeedScale:
    customers: int = 1200
    products: int = 200
    orders: int = 12000
    reviews: int = 4500


DEFAULT_SCALE = SeedScale()

FIRST_NAMES = (
    "Amina",
    "Liam",
    "Sofia",
    "Noah",
    "Maya",
    "Lucas",
    "Nadia",
    "Ethan",
    "Chloe",
    "Omar",
    "Elena",
    "Mateo",
    "Hana",
    "David",
    "Zara",
    "Julian",
    "Clara",
    "Tariq",
    "Freya",
    "Daniel",
)

LAST_NAMES = (
    "Benali",
    "Carter",
    "Moreau",
    "Nakamura",
    "Alvarez",
    "Lindqvist",
    "Patel",
    "Kowalski",
    "Haddad",
    "Brooks",
    "Rossi",
    "Schneider",
    "Okafor",
    "Silva",
    "Kim",
    "Dupont",
    "Novak",
    "Reed",
    "Sato",
    "Mansour",
)

COUNTRY_LOCATIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "US": (("Austin", "TX"), ("Seattle", "WA"), ("New York", "NY"), ("Chicago", "IL")),
    "GB": (("London", "England"), ("Manchester", "England"), ("Edinburgh", "Scotland")),
    "DE": (("Berlin", "Berlin"), ("Munich", "Bavaria"), ("Hamburg", "Hamburg")),
    "FR": (("Paris", "Ile-de-France"), ("Lyon", "Auvergne-Rhone-Alpes"), ("Marseille", "PACA")),
    "CA": (("Toronto", "ON"), ("Vancouver", "BC"), ("Montreal", "QC")),
    "ES": (("Madrid", "Madrid"), ("Barcelona", "Catalonia")),
    "NL": (("Amsterdam", "North Holland"), ("Rotterdam", "South Holland")),
    "JP": (("Tokyo", "Tokyo"), ("Osaka", "Osaka")),
    "AU": (("Sydney", "NSW"), ("Melbourne", "VIC")),
    "AE": (("Dubai", "Dubai"), ("Abu Dhabi", "Abu Dhabi")),
}
COUNTRIES = tuple(COUNTRY_LOCATIONS.keys())
COUNTRY_WEIGHTS = (32, 12, 11, 10, 9, 6, 5, 5, 5, 5)

SEGMENTS = ("retail", "vip", "wholesale")
SEGMENT_WEIGHTS = (76, 16, 8)

WAREHOUSES = ("WH-US-EAST", "WH-US-WEST", "WH-EU-CENT", "WH-AP-EAST")

CATEGORY_TREE: tuple[tuple[int, int | None, str, str], ...] = (
    (1, None, "Electronics", "electronics"),
    (2, None, "Home & Office", "home-office"),
    (3, None, "Apparel", "apparel"),
    (4, None, "Sports & Outdoors", "sports-outdoors"),
    (5, None, "Accessories", "accessories"),
    (6, 1, "Laptops & Monitors", "laptops-monitors"),
    (7, 1, "Audio & Headphones", "audio-headphones"),
    (8, 1, "Smart Home", "smart-home"),
    (9, 2, "Ergonomic Furniture", "ergonomic-furniture"),
    (10, 2, "Desk Lighting", "desk-lighting"),
    (11, 3, "Outerwear", "outerwear"),
    (12, 3, "Footwear", "footwear"),
    (13, 4, "Fitness Gear", "fitness-gear"),
    (14, 4, "Camping & Trail", "camping-trail"),
    (15, 5, "Bags & Travel", "bags-travel"),
)
LEAF_CATEGORY_IDS = tuple(row[0] for row in CATEGORY_TREE if row[1] is not None)

PRODUCT_ADJECTIVES = (
    "Apex",
    "Nordic",
    "Aero",
    "Vertex",
    "Pulse",
    "Studio",
    "Summit",
    "Precision",
    "Core",
    "Horizon",
)
PRODUCT_NOUNS: dict[int, tuple[str, ...]] = {
    6: ("Ultrabook 14", "4K Monitor 27", "USB-C Dock", "Workstation Stand"),
    7: ("ANC Headphones", "Studio Earbuds", "Desktop DAC", "Bluetooth Speaker"),
    8: ("Air Quality Sensor", "Smart Thermostat", "Wi-Fi Plug Pack", "Security Camera"),
    9: ("Mesh Task Chair", "Standing Desk Frame", "Monitor Arm", "Footrest Pro"),
    10: ("LED Task Lamp", "Monitor Light Bar", "Ambient Floor Lamp", "Warm Desk Bulb"),
    11: ("Shell Jacket", "Merino Zip Hoodie", "Insulated Parka", "Windbreaker"),
    12: ("Trail Runner", "Everyday Sneaker", "Weatherproof Boot", "Knit Loafer"),
    13: ("Adjustable Kettlebell", "Grip Yoga Mat", "Resistance Kit", "Foam Roller"),
    14: ("Ultralight Tent", "Insulated Flask", "Trail Headlamp", "Sleeping Pad"),
    15: ("Commuter Backpack", "Carry-On Duffel", "Tech Organizer", "Leather Sleeve"),
}

REVIEW_COMMENTS: dict[int, tuple[str, ...]] = {
    5: (
        "Build quality exceeded expectations and arrived ahead of schedule.",
        "Performs reliably every day; worth every dollar.",
        "Clean design, accurate specs, and thoughtful packaging.",
    ),
    4: (
        "Very solid overall with only minor setup friction.",
        "Good value for the price and matches the description well.",
        "Comfortable and dependable after several weeks of use.",
    ),
    3: (
        "Works as advertised, though materials feel average.",
        "Decent performance but slightly overpriced for the category.",
    ),
    2: (
        "Sizing and finish were inconsistent; expected better quality control.",
        "Works intermittently and required troubleshooting out of the box.",
    ),
    1: (
        "Stopped working within two weeks and had to request a refund.",
        "Arrived with defects and did not match the product listing.",
    ),
}


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    categories: list[dict[str, Any]]
    customers: list[dict[str, Any]]
    addresses: list[dict[str, Any]]
    products: list[dict[str, Any]]
    inventory: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    order_items: list[dict[str, Any]]
    payments: list[dict[str, Any]]
    reviews: list[dict[str, Any]]


def _money(value: float) -> Decimal:
    return Decimal(f"{value:.2f}")


def generate_synthetic_dataset(
    *,
    seed: int = DEFAULT_SEED,
    scale: SeedScale = DEFAULT_SCALE,
) -> SyntheticDataset:
    """Generate a deterministic, mathematically consistent synthetic e-commerce dataset."""
    rng = random.Random(seed)

    categories = [
        {"id": cat_id, "parent_id": parent_id, "name": name, "slug": slug}
        for cat_id, parent_id, name, slug in CATEGORY_TREE
    ]

    customers: list[dict[str, Any]] = []
    addresses: list[dict[str, Any]] = []
    customer_segments: dict[int, str] = {}
    address_id = 1

    for cust_id in range(1, scale.customers + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        country = rng.choices(COUNTRIES, weights=COUNTRY_WEIGHTS, k=1)[0]
        segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        created_offset_days = rng.randint(1, 730)
        created_at = REFERENCE_UTC - timedelta(
            days=created_offset_days,
            minutes=rng.randint(0, 1439),
        )
        customer_segments[cust_id] = segment

        customers.append(
            {
                "id": cust_id,
                "email": f"{first.lower()}.{last.lower()}.{cust_id}@example-commerce.test",
                "full_name": f"{first} {last}",
                "segment": segment,
                "country_code": country,
                "created_at": created_at,
            }
        )

        city, state = rng.choice(COUNTRY_LOCATIONS[country])
        addresses.append(
            {
                "id": address_id,
                "customer_id": cust_id,
                "city": city,
                "state": state,
                "country_code": country,
                "is_default": True,
            }
        )
        address_id += 1

        if rng.random() < 0.30:
            alt_city, alt_state = rng.choice(COUNTRY_LOCATIONS[country])
            addresses.append(
                {
                    "id": address_id,
                    "customer_id": cust_id,
                    "city": alt_city,
                    "state": alt_state,
                    "country_code": country,
                    "is_default": False,
                }
            )
            address_id += 1

    products: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    product_prices: dict[int, Decimal] = {}

    for prod_id in range(1, scale.products + 1):
        cat_id = LEAF_CATEGORY_IDS[(prod_id - 1) % len(LEAF_CATEGORY_IDS)]
        adj = PRODUCT_ADJECTIVES[(prod_id * 3) % len(PRODUCT_ADJECTIVES)]
        noun_choices = PRODUCT_NOUNS[cat_id]
        noun = noun_choices[(prod_id // len(LEAF_CATEGORY_IDS)) % len(noun_choices)]

        base_price = rng.uniform(18.0, 680.0) if cat_id in (6, 7, 9) else rng.uniform(14.0, 240.0)
        unit_price = _money(base_price)
        margin_ratio = rng.uniform(0.38, 0.72)
        cost_price = _money(float(unit_price) * margin_ratio)
        product_prices[prod_id] = unit_price

        products.append(
            {
                "id": prod_id,
                "category_id": cat_id,
                "sku": f"SKU-{cat_id:02d}-{prod_id:04d}",
                "name": f"{adj} {noun} #{prod_id}",
                "unit_price": unit_price,
                "cost_price": cost_price,
                "is_active": rng.random() < 0.92,
                "created_at": REFERENCE_UTC - timedelta(days=rng.randint(30, 720)),
            }
        )

        # Include realistic low-stock and stockout records (~12% below reorder level).
        reorder_level = rng.randint(10, 45)
        if rng.random() < 0.04:
            stock_quantity = 0
        elif rng.random() < 0.10:
            stock_quantity = rng.randint(1, max(1, reorder_level - 1))
        else:
            stock_quantity = rng.randint(reorder_level, 420)

        inventory.append(
            {
                "product_id": prod_id,
                "stock_quantity": stock_quantity,
                "reorder_level": reorder_level,
                "warehouse_code": rng.choice(WAREHOUSES),
                "updated_at": REFERENCE_UTC - timedelta(hours=rng.randint(1, 240)),
            }
        )

    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []
    order_item_id = 1
    payment_id = 1
    customer_product_pairs: list[tuple[int, int]] = []

    order_statuses = ("delivered", "shipped", "paid", "pending", "cancelled", "refunded")
    order_status_weights = (58, 14, 10, 6, 7, 5)
    payment_methods = ("card", "wallet", "bank_transfer")
    payment_method_weights = (68, 22, 10)

    for order_id in range(1, scale.orders + 1):
        cust_id = rng.randint(1, scale.customers)
        segment = customer_segments[cust_id]
        status = rng.choices(order_statuses, weights=order_status_weights, k=1)[0]

        # 540-day window (~18 months) with slight recency weight.
        days_ago = int((rng.random() ** 1.25) * 540)
        placed_at = REFERENCE_UTC - timedelta(days=days_ago, minutes=rng.randint(0, 1439))

        item_count = rng.choices((1, 2, 3, 4, 5), weights=(36, 31, 19, 10, 4), k=1)[0]
        chosen_products = rng.sample(
            range(1, scale.products + 1),
            k=min(item_count, scale.products),
        )

        subtotal = Decimal("0.00")
        for prod_id in chosen_products:
            qty = rng.choices((1, 2, 3, 4), weights=(68, 20, 8, 4), k=1)[0]
            if segment == "wholesale":
                qty += rng.randint(2, 6)
            unit_price = product_prices[prod_id]
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            subtotal += line_total

            order_items.append(
                {
                    "id": order_item_id,
                    "order_id": order_id,
                    "product_id": prod_id,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )
            order_item_id += 1
            if len(customer_product_pairs) < scale.reviews * 2 and status == "delivered":
                customer_product_pairs.append((cust_id, prod_id))

        if segment == "vip":
            discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
        elif segment == "wholesale":
            discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
        elif rng.random() < 0.20:
            discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        else:
            discount = Decimal("0.00")

        shipping = (
            Decimal("0.00")
            if (segment == "vip" or subtotal >= Decimal("150.00"))
            else Decimal("12.50")
        )
        total = max(Decimal("0.00"), (subtotal - discount + shipping).quantize(Decimal("0.01")))

        orders.append(
            {
                "id": order_id,
                "customer_id": cust_id,
                "status": status,
                "subtotal_amount": subtotal,
                "discount_amount": discount,
                "shipping_amount": shipping,
                "total_amount": total,
                "currency": "USD",
                "placed_at": placed_at,
            }
        )

        method = rng.choices(payment_methods, weights=payment_method_weights, k=1)[0]
        if status in ("paid", "shipped", "delivered"):
            # Occasional initial failed payment attempt before successful capture.
            if rng.random() < 0.06:
                payments.append(
                    {
                        "id": payment_id,
                        "order_id": order_id,
                        "payment_method": method,
                        "status": "failed",
                        "amount": total,
                        "paid_at": None,
                    }
                )
                payment_id += 1
            payments.append(
                {
                    "id": payment_id,
                    "order_id": order_id,
                    "payment_method": method,
                    "status": "captured",
                    "amount": total,
                    "paid_at": placed_at + timedelta(minutes=rng.randint(1, 45)),
                }
            )
            payment_id += 1
        elif status == "refunded":
            payments.append(
                {
                    "id": payment_id,
                    "order_id": order_id,
                    "payment_method": method,
                    "status": "refunded",
                    "amount": total,
                    "paid_at": placed_at + timedelta(minutes=rng.randint(1, 45)),
                }
            )
            payment_id += 1
        elif status == "pending":
            payments.append(
                {
                    "id": payment_id,
                    "order_id": order_id,
                    "payment_method": method,
                    "status": "authorized",
                    "amount": total,
                    "paid_at": None,
                }
            )
            payment_id += 1

    reviews: list[dict[str, Any]] = []
    ratings = (5, 4, 3, 2, 1)
    rating_weights = (46, 28, 13, 8, 5)
    for review_id in range(1, scale.reviews + 1):
        if review_id <= len(customer_product_pairs) and rng.random() < 0.85:
            cust_id, prod_id = customer_product_pairs[review_id - 1]
            verified = True
        else:
            cust_id = rng.randint(1, scale.customers)
            prod_id = rng.randint(1, scale.products)
            verified = False

        rating = rng.choices(ratings, weights=rating_weights, k=1)[0]
        reviews.append(
            {
                "id": review_id,
                "product_id": prod_id,
                "customer_id": cust_id,
                "rating": rating,
                "comment": rng.choice(REVIEW_COMMENTS[rating]),
                "is_verified_purchase": verified,
                "created_at": REFERENCE_UTC - timedelta(days=rng.randint(1, 500)),
            }
        )

    return SyntheticDataset(
        categories=categories,
        customers=customers,
        addresses=addresses,
        products=products,
        inventory=inventory,
        orders=orders,
        order_items=order_items,
        payments=payments,
        reviews=reviews,
    )


def _bulk_insert_chunks(
    conn: Connection,
    table: Any,
    rows: list[dict[str, Any]],
    chunk_size: int = 2000,
) -> None:
    for start in range(0, len(rows), chunk_size):
        conn.execute(insert(table), rows[start : start + chunk_size])


def _sync_sequences(conn: Connection) -> None:
    tables_with_serial_id = (
        "categories",
        "customers",
        "addresses",
        "products",
        "orders",
        "order_items",
        "payments",
        "reviews",
    )
    for table_name in tables_with_serial_id:
        conn.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('ecommerce.{table_name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM ecommerce.{table_name}), 1), true)"
            )
        )


def _fetch_counts(conn: Connection) -> dict[str, int]:
    table_names = (
        "categories",
        "customers",
        "addresses",
        "products",
        "inventory",
        "orders",
        "order_items",
        "payments",
        "reviews",
    )
    counts: dict[str, int] = {}
    for name in table_names:
        result = conn.execute(text(f"SELECT COUNT(*) FROM ecommerce.{name}")).scalar_one()
        counts[name] = int(result)
    return counts


def seed_database(
    migrator_url: str,
    *,
    seed: int = DEFAULT_SEED,
    scale: SeedScale = DEFAULT_SCALE,
    force: bool = False,
) -> dict[str, int]:
    """Deterministically seed the synthetic ecommerce schema using the migrator role."""
    engine = create_engine(migrator_url, future=True)
    try:
        with engine.begin() as conn:
            existing_customers = conn.execute(
                text("SELECT COUNT(*) FROM ecommerce.customers")
            ).scalar_one()
            if int(existing_customers) > 0 and not force:
                logger.info("ecommerce schema already seeded; skipping (pass --force to reseed).")
                return _fetch_counts(conn)

            if force:
                conn.execute(
                    text(
                        "TRUNCATE TABLE "
                        "ecommerce.reviews, "
                        "ecommerce.payments, "
                        "ecommerce.order_items, "
                        "ecommerce.orders, "
                        "ecommerce.inventory, "
                        "ecommerce.products, "
                        "ecommerce.categories, "
                        "ecommerce.addresses, "
                        "ecommerce.customers "
                        "RESTART IDENTITY CASCADE"
                    )
                )

            dataset = generate_synthetic_dataset(seed=seed, scale=scale)
            _bulk_insert_chunks(conn, Category.__table__, dataset.categories)
            _bulk_insert_chunks(conn, Customer.__table__, dataset.customers)
            _bulk_insert_chunks(conn, Address.__table__, dataset.addresses)
            _bulk_insert_chunks(conn, Product.__table__, dataset.products)
            _bulk_insert_chunks(conn, Inventory.__table__, dataset.inventory)
            _bulk_insert_chunks(conn, Order.__table__, dataset.orders)
            _bulk_insert_chunks(conn, OrderItem.__table__, dataset.order_items)
            _bulk_insert_chunks(conn, Payment.__table__, dataset.payments)
            _bulk_insert_chunks(conn, Review.__table__, dataset.reviews)

            _sync_sequences(conn)

        # Refresh planner statistics so introspection & EXPLAIN (FORMAT JSON) are accurate.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for table_name in (
                "categories",
                "customers",
                "addresses",
                "products",
                "inventory",
                "orders",
                "order_items",
                "payments",
                "reviews",
            ):
                conn.execute(text(f"ANALYZE ecommerce.{table_name}"))

        with engine.connect() as conn:
            return _fetch_counts(conn)
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic ecommerce database.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic RNG seed.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate ecommerce tables and reseed deterministically.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    settings = load_settings()
    if settings.database_migrator_url is None:
        raise ConfigurationError(
            "DATABASE_MIGRATOR_URL is required to seed the database. "
            "Configure it in the root .env file (see .env.example)."
        )

    counts = seed_database(
        settings.database_migrator_url.get_secret_value(),
        seed=args.seed,
        force=args.force,
    )
    for table_name, count in counts.items():
        print(f"ecommerce.{table_name}: {count}")


if __name__ == "__main__":
    main()
