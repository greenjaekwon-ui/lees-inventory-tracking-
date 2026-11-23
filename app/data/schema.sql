CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,                 -- salted hash, never the password (SEC-2)
    role TEXT NOT NULL,                          -- a Role name, e.g. INVENTORY_MANAGER
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,    -- duplicate check (SR-1.4)
    low_stock_level INTEGER NOT NULL DEFAULT 0 CHECK (low_stock_level >= 0),
    archived INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS stock_batch (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product(id),
    expiry_date TEXT,                            -- ISO yyyy-mm-dd, NULL = no expiry
    qty_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (qty_in_stock >= 0),
    qty_sold     INTEGER NOT NULL DEFAULT 0 CHECK (qty_sold >= 0),
    qty_damaged  INTEGER NOT NULL DEFAULT 0 CHECK (qty_damaged >= 0),
    qty_expired  INTEGER NOT NULL DEFAULT 0 CHECK (qty_expired >= 0)
);
CREATE TABLE IF NOT EXISTS stock_change (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES stock_batch(id),
    quantity INTEGER NOT NULL,
    from_status TEXT, to_status TEXT, reason TEXT,
    performed_by TEXT, date_time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sale (
    id INTEGER PRIMARY KEY,
    sale_ref TEXT NOT NULL UNIQUE,               -- a reused reference is rejected (SR-9.4)
    batch_id INTEGER NOT NULL REFERENCES stock_batch(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    performed_by TEXT, date_time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS damage_record (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES stock_batch(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    reason TEXT NOT NULL, note TEXT,
    performed_by TEXT, date_time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL, detail TEXT,
    performed_by TEXT,                           -- NULL for automatic expiry events (SEC-4)
    date_time TEXT NOT NULL
);
