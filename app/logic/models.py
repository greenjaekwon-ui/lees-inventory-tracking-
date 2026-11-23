"""Classes and enumerations from the SDS class diagram (section 3.2)."""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class Status(Enum):
    IN_STOCK = "In Stock"
    SOLD = "Sold"
    DAMAGED = "Damaged"
    EXPIRED = "Expired"


class Role(Enum):
    OWNER = "Business Owner/Manager"
    INVENTORY_MANAGER = "Stock/Inventory Manager"
    WAREHOUSE = "Warehouse/Stock Staff"
    CASHIER = "Sales/Cashier Staff"


class ChangeType(Enum):
    STOCK_RECEIVED = "Stock received"
    COUNT_CORRECTION = "Count correction"
    SALE = "Sale"
    DAMAGE = "Damage"
    EXPIRY = "Expiry"


class DamageReason(Enum):               # SRS FID-10 SR-10.2
    ON_DELIVERY = "Damaged on delivery"
    IN_STORAGE = "Damaged in storage"
    IN_HANDLING = "Damaged in handling"
    OTHER = "Other"


# Default permissions for this version (SRS 3.2.2 table, SDS 2.3.1). The client must still approve them.
# Alerts (FID-5, FID-6) are shown to warehouse staff, inventory managers and the owner, not to cashiers (SR-6.3).
ROLE_PERMISSIONS = {
    Role.INVENTORY_MANAGER: {"view_products", "add_product", "update_product", "remove_product",
                             "view_alerts", "record_damage", "run_expiry_check"},
    Role.OWNER:             {"view_products", "add_product", "update_product", "remove_product",
                             "view_alerts", "run_expiry_check"},
    Role.WAREHOUSE:         {"view_products", "view_alerts", "record_damage"},
    Role.CASHIER:           {"view_products"},
}


@dataclass
class User:
    id: int
    username: str
    role: Role

    def has_permission(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, set())


@dataclass
class StockBatch:
    id: int
    product_id: int
    expiry_date: Optional[date] = None
    qty_in_stock: int = 0
    qty_sold: int = 0
    qty_damaged: int = 0
    qty_expired: int = 0

    def total(self) -> int:
        return self.qty_in_stock + self.qty_sold + self.qty_damaged + self.qty_expired


@dataclass
class Product:
    id: int
    name: str
    low_stock_level: int = 0
    archived: bool = False
    batches: List[StockBatch] = field(default_factory=list)

    def total_in_stock(self) -> int:
        return sum(b.qty_in_stock for b in self.batches)


@dataclass
class StockChange:
    id: int
    batch_id: int
    quantity: int
    from_status: Optional[str]
    to_status: Optional[str]
    reason: str
    performed_by: Optional[str]
    date_time: str


@dataclass
class Sale:
    id: int
    sale_ref: str
    batch_id: int
    quantity: int
    performed_by: Optional[str]
    date_time: str


@dataclass
class DamageRecord:
    id: int
    batch_id: int
    quantity: int
    reason: str
    note: str
    performed_by: Optional[str]
    date_time: str


@dataclass
class AuditLog:
    id: int
    action: str
    detail: str
    performed_by: Optional[str]     # None for automatic expiry events (SEC-4)
    date_time: str
