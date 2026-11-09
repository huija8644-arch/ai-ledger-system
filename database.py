import sqlite3
import json
import os
import sys
from datetime import datetime

# In frozen (packaged exe) mode, persist db next to the executable
if getattr(sys, 'frozen', False):
    DB_DIR = os.path.dirname(sys.executable)
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(DB_DIR, "ledger.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force_reset=False):
    if force_reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        opening_ar REAL DEFAULT 0.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        remark TEXT DEFAULT '',
        opening_ap REAL DEFAULT 0.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT '未分类',
        spec TEXT DEFAULT '件',
        sale_price REAL DEFAULT 0.0,
        purchase_price REAL DEFAULT 0.0,
        opening_qty REAL DEFAULT 0.0,
        safety_stock REAL DEFAULT 30.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ai_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        source_name TEXT,
        model_source TEXT,
        model_name TEXT,
        business_nature TEXT,
        cash_flow_warning TEXT,
        internal_control_notes TEXT,
        action_items TEXT,
        raw_response TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS import_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_code TEXT UNIQUE NOT NULL,
        source_name TEXT NOT NULL,
        source_type TEXT DEFAULT 'file_upload',
        parse_mode TEXT DEFAULT 'semantic_engine',
        summary TEXT DEFAULT '',
        record_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'committed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        date TEXT NOT NULL,
        order_no TEXT NOT NULL,
        product_name TEXT NOT NULL,
        spec TEXT DEFAULT '件',
        unit_price REAL NOT NULL,
        qty REAL NOT NULL,
        amount REAL NOT NULL,
        buyer TEXT DEFAULT '',
        supplier_name TEXT NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        remark TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        date TEXT NOT NULL,
        order_no TEXT NOT NULL,
        product_name TEXT NOT NULL,
        spec TEXT DEFAULT '件',
        unit_price REAL NOT NULL,
        qty REAL NOT NULL,
        amount REAL NOT NULL,
        seller TEXT DEFAULT '',
        customer_name TEXT NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS supplier_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        date TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        amount REAL NOT NULL,
        payer TEXT DEFAULT '',
        payee TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS customer_receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        date TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        amount REAL NOT NULL,
        payer TEXT DEFAULT '',
        payee TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS ai_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        provider TEXT DEFAULT 'deepseek',
        api_key TEXT DEFAULT '',
        base_url TEXT DEFAULT 'https://api.deepseek.com/v1',
        model_name TEXT DEFAULT 'deepseek-chat',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Ensure products table has category column if upgraded from older version
    try:
        cur.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT '未分类'")
    except sqlite3.OperationalError:
        pass

    # Ensure ai_audit_logs exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            source_name TEXT,
            model_source TEXT,
            model_name TEXT,
            business_nature TEXT,
            cash_flow_warning TEXT,
            internal_control_notes TEXT,
            action_items TEXT,
            raw_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial settings if not present
    cur.execute("SELECT COUNT(*) FROM ai_settings")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO ai_settings (id, provider, api_key, base_url, model_name)
            VALUES (1, 'deepseek', '', 'https://api.deepseek.com/v1', 'deepseek-chat')
        """)

    conn.commit()
    conn.close()


def reset_to_sample():
    """Initializes and seeds the sample clothing business data."""
    init_db(force_reset=True)
    conn = get_conn()
    cur = conn.cursor()
    seed_initial_data(cur)
    conn.commit()
    conn.close()


def reset_to_empty():
    """Wipes all transactional and master data, providing a brand new empty ledger."""
    init_db(force_reset=True)
    conn = get_conn()
    cur = conn.cursor()
    # tables are already created empty
    conn.commit()
    conn.close()


def clear_transactions_only():
    """Wipes all transactional streams and import batches, keeping products, customers, suppliers."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM purchases")
    cur.execute("DELETE FROM sales")
    cur.execute("DELETE FROM supplier_payments")
    cur.execute("DELETE FROM customer_receipts")
    cur.execute("DELETE FROM import_batches")
    conn.commit()
    conn.close()


def seed_initial_data(cur):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO import_batches (batch_code, source_name, source_type, parse_mode, summary, record_count, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'committed', ?)
    """, (
        "BATCH-INIT-001",
        "示例台账数据 (服装进销存样例)",
        "initial_seed",
        "系统初始化导入",
        "导入 4 家客户、3 家供应商、11 个服装 SKU，以及 11 笔采购、3 笔销售、2 笔付款、3 笔收款流水",
        19,
        now_str
    ))
    batch_id = cur.lastrowid

    customers = [
        ("客户1", "北京市朝阳区", "13047***202", 25000.0),
        ("客户2", "北京市怀柔区", "13213***991", 0.0),
        ("客户3", "北京市丰台区", "15027***013", 30000.0),
        ("客户4", "湖北省武汉市", "17777***156", 0.0),
    ]
    cur.executemany("""
        INSERT INTO customers (name, address, phone, opening_ar)
        VALUES (?, ?, ?, ?)
    """, customers)

    suppliers = [
        ("公司1", "北京市房山区", "13467***956", "", 0.0),
        ("公司2", "郑州市金水区", "18436***004", "", 0.0),
        ("公司3", "天津市滨海新区", "13695***288", "", 0.0),
    ]
    cur.executemany("""
        INSERT INTO suppliers (name, address, phone, remark, opening_ap)
        VALUES (?, ?, ?, ?, ?)
    """, suppliers)

    products = [
        ("四季休闲服 黑色", "件", 401.0, 256.61, 50, 30),
        ("四季休闲服 红色", "件", 401.0, 256.61, 50, 30),
        ("四季休闲服 紫色", "件", 401.0, 256.61, 50, 30),
        ("轻便系列运动衣 黑色", "件", 132.48, 76.92, 50, 30),
        ("轻便系列运动衣 红色", "件", 132.48, 76.92, 50, 30),
        ("轻便系列运动衣 灰色", "件", 132.48, 76.92, 60, 30),
        ("轻便系列运动衣 蓝色", "件", 132.48, 76.92, 60, 30),
        ("轻便系列运动衣 米色", "件", 132.48, 76.92, 60, 30),
        ("轻便系列运动衣 棕色", "件", 132.48, 76.92, 60, 30),
        ("轻便系列运动衣 卡其色", "件", 132.48, 76.92, 60, 30),
        ("轻便系列运动衣 黄色", "件", 132.48, 76.92, 60, 30),
    ]
    cur.executemany("""
        INSERT INTO products (name, spec, sale_price, purchase_price, opening_qty, safety_stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, products)

    purchases = [
        (batch_id, "2024-11-15", "A2020001", "四季休闲服 黑色", "件", 256.61, 20, 5132.2, "张珊", "公司1", "北京市房山区", "13467***956", "0"),
        (batch_id, "2024-11-15", "A2020001", "四季休闲服 红色", "件", 256.61, 20, 5132.2, "张珊", "公司1", "北京市房山区", "13467***956", "0"),
        (batch_id, "2024-11-15", "A2020001", "四季休闲服 紫色", "件", 256.61, 20, 5132.2, "张珊", "公司1", "北京市房山区", "13467***956", "0"),
        (batch_id, "2024-11-15", "A2020002", "轻便系列运动衣 黑色", "件", 76.92, 10, 769.2, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020002", "轻便系列运动衣 红色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020002", "轻便系列运动衣 灰色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020003", "轻便系列运动衣 蓝色", "件", 76.92, 5, 384.6, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020003", "轻便系列运动衣 米色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020003", "轻便系列运动衣 棕色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020003", "轻便系列运动衣 卡其色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
        (batch_id, "2024-11-15", "A2020003", "轻便系列运动衣 黄色", "件", 76.92, 15, 1153.8, "王三", "公司2", "郑州市金水区", "18436***004", "0"),
    ]
    cur.executemany("""
        INSERT INTO purchases (batch_id, date, order_no, product_name, spec, unit_price, qty, amount, buyer, supplier_name, address, phone, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, purchases)

    sales = [
        (batch_id, "2024-11-18", "A2020001", "四季休闲服 红色", "件", 401.0, 20, 8020.0, "陈士园", "客户1", "北京市朝阳区", "13047***202"),
        (batch_id, "2024-11-18", "A2020002", "四季休闲服 黑色", "件", 410.0, 13, 5330.0, "杨澜月", "客户2", "北京市怀柔区", "13213***991"),
        (batch_id, "2024-11-18", "A2020003", "轻便系列运动衣 黑色", "件", 132.48, 53, 7021.44, "魏莹雪", "客户3", "北京市丰台区", "15027***013"),
    ]
    cur.executemany("""
        INSERT INTO sales (batch_id, date, order_no, product_name, spec, unit_price, qty, amount, seller, customer_name, address, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sales)

    payments = [
        (batch_id, "2024-11-15", "公司1", "北京市房山区", "13467***956", 10000.0, "张三", "李静"),
        (batch_id, "2024-11-16", "公司2", "郑州市金水区", "18436***004", 2000.0, "张三", "李静"),
    ]
    cur.executemany("""
        INSERT INTO supplier_payments (batch_id, date, supplier_name, address, phone, amount, payer, payee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, payments)

    receipts = [
        (batch_id, "2024-11-19", "客户1", "北京市朝阳区", "13047***202", 5000.0, "张三", "李静"),
        (batch_id, "2024-11-20", "客户2", "北京市怀柔区", "13213***991", 5000.0, "张三", "李静"),
        (batch_id, "2024-11-21", "客户3", "北京市丰台区", "15027***013", 600.0, "张三", "李静"),
    ]
    cur.executemany("""
        INSERT INTO customer_receipts (batch_id, date, customer_name, address, phone, amount, payer, payee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, receipts)


# ================= CRUD Operations =================

def save_product(data):
    conn = get_conn()
    cur = conn.cursor()
    name = str(data.get("name", "")).strip()
    if not name:
        conn.close()
        return {"ok": False, "error": "商品名称不能为空"}

    spec = str(data.get("spec", "件")).strip() or "件"
    category = str(data.get("category", "未分类")).strip() or "未分类"
    sale_price = float(data.get("sale_price", 0.0) or 0.0)
    purchase_price = float(data.get("purchase_price", 0.0) or 0.0)
    opening_qty = float(data.get("opening_qty", 0.0) or 0.0)
    safety_stock = float(data.get("safety_stock", 30.0) or 30.0)
    pid = data.get("id")

    try:
        if pid:
            cur.execute("""
                UPDATE products
                SET name = ?, category = ?, spec = ?, sale_price = ?, purchase_price = ?, opening_qty = ?, safety_stock = ?
                WHERE id = ?
            """, (name, category, spec, sale_price, purchase_price, opening_qty, safety_stock, pid))
        else:
            cur.execute("""
                INSERT INTO products (name, category, spec, sale_price, purchase_price, opening_qty, safety_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, category, spec, sale_price, purchase_price, opening_qty, safety_stock))
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"已存在名称为「{name}」的商品"}
    finally:
        conn.close()


def delete_product(prod_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_customer(data):
    conn = get_conn()
    cur = conn.cursor()
    name = str(data.get("name", "")).strip()
    if not name:
        conn.close()
        return {"ok": False, "error": "客户名称不能为空"}

    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    opening_ar = float(data.get("opening_ar", 0.0) or 0.0)
    cid = data.get("id")

    try:
        if cid:
            cur.execute("""
                UPDATE customers
                SET name = ?, address = ?, phone = ?, opening_ar = ?
                WHERE id = ?
            """, (name, address, phone, opening_ar, cid))
        else:
            cur.execute("""
                INSERT INTO customers (name, address, phone, opening_ar)
                VALUES (?, ?, ?, ?)
            """, (name, address, phone, opening_ar))
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"已存在名称为「{name}」的客户"}
    finally:
        conn.close()


def delete_customer(cust_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_supplier(data):
    conn = get_conn()
    cur = conn.cursor()
    name = str(data.get("name", "")).strip()
    if not name:
        conn.close()
        return {"ok": False, "error": "供应商名称不能为空"}

    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    remark = str(data.get("remark", "")).strip()
    opening_ap = float(data.get("opening_ap", 0.0) or 0.0)
    sid = data.get("id")

    try:
        if sid:
            cur.execute("""
                UPDATE suppliers
                SET name = ?, address = ?, phone = ?, remark = ?, opening_ap = ?
                WHERE id = ?
            """, (name, address, phone, remark, opening_ap, sid))
        else:
            cur.execute("""
                INSERT INTO suppliers (name, address, phone, remark, opening_ap)
                VALUES (?, ?, ?, ?, ?)
            """, (name, address, phone, remark, opening_ap))
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"已存在名称为「{name}」的供应商"}
    finally:
        conn.close()


def delete_supplier(sup_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM suppliers WHERE id = ?", (sup_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_purchase(data):
    conn = get_conn()
    cur = conn.cursor()
    pname = str(data.get("product_name", "")).strip()
    sname = str(data.get("supplier_name", "")).strip()
    if not pname or not sname:
        conn.close()
        return {"ok": False, "error": "商品名称和供应商名称为必填项"}

    pid = data.get("id")
    date_str = normalize_date_str(data.get("date", ""))
    order_no = str(data.get("order_no", "")).strip() or f"PO-{datetime.now().strftime('%m%d%H%M')}"
    spec = str(data.get("spec", "件")).strip() or "件"
    unit_price = float(data.get("unit_price", 0.0) or 0.0)
    qty = float(data.get("qty", 0.0) or 0.0)
    amount = float(data.get("amount", 0.0) or (round(unit_price * qty, 2)))
    buyer = str(data.get("buyer", "")).strip()
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    remark = str(data.get("remark", "")).strip()

    # ensure product and supplier exist in master tables
    category = str(data.get("category", "未分类")).strip() or "未分类"
    cur.execute("SELECT id, spec FROM products WHERE name = ?", (pname,))
    existing_prod = cur.fetchone()
    if not existing_prod:
        cur.execute("INSERT INTO products (name, category, spec, purchase_price, sale_price, opening_qty, safety_stock) VALUES (?, ?, ?, ?, ?, 0, 30)",
                    (pname, category, spec, unit_price, round(unit_price * 1.5, 2)))
    elif spec and existing_prod["spec"] != spec:
        cur.execute("UPDATE products SET spec = ? WHERE id = ?", (spec, existing_prod["id"]))

    cur.execute("SELECT id FROM suppliers WHERE name = ?", (sname,))
    if not cur.fetchone():
        cur.execute("INSERT INTO suppliers (name, address, phone) VALUES (?, ?, ?)", (sname, address, phone))

    if pid:
        cur.execute("""
            UPDATE purchases
            SET date = ?, order_no = ?, product_name = ?, spec = ?, unit_price = ?, qty = ?, amount = ?, buyer = ?, supplier_name = ?, address = ?, phone = ?, remark = ?
            WHERE id = ?
        """, (date_str, order_no, pname, spec, unit_price, qty, amount, buyer, sname, address, phone, remark, pid))
    else:
        cur.execute("""
            INSERT INTO purchases (date, order_no, product_name, spec, unit_price, qty, amount, buyer, supplier_name, address, phone, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, order_no, pname, spec, unit_price, qty, amount, buyer, sname, address, phone, remark))

    conn.commit()
    conn.close()
    return {"ok": True}


def delete_purchase(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM purchases WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_sale(data):
    conn = get_conn()
    cur = conn.cursor()
    pname = str(data.get("product_name", "")).strip()
    cname = str(data.get("customer_name", "")).strip()
    if not pname or not cname:
        conn.close()
        return {"ok": False, "error": "商品名称和客户名称为必填项"}

    sid = data.get("id")
    date_str = normalize_date_str(data.get("date", ""))
    order_no = str(data.get("order_no", "")).strip() or f"SO-{datetime.now().strftime('%m%d%H%M')}"
    spec = str(data.get("spec", "件")).strip() or "件"
    unit_price = float(data.get("unit_price", 0.0) or 0.0)
    qty = float(data.get("qty", 0.0) or 0.0)
    amount = float(data.get("amount", 0.0) or (round(unit_price * qty, 2)))
    seller = str(data.get("seller", "")).strip()
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()

    # ensure product and customer exist
    cur.execute("SELECT id, spec FROM products WHERE name = ?", (pname,))
    existing_prod = cur.fetchone()
    if not existing_prod:
        cur.execute("INSERT INTO products (name, spec, sale_price, purchase_price, opening_qty, safety_stock) VALUES (?, ?, ?, ?, 0, 30)",
                    (pname, spec, unit_price, round(unit_price * 0.6, 2)))
    elif spec and existing_prod["spec"] != spec:
        cur.execute("UPDATE products SET spec = ? WHERE id = ?", (spec, existing_prod["id"]))

    cur.execute("SELECT id FROM customers WHERE name = ?", (cname,))
    if not cur.fetchone():
        cur.execute("INSERT INTO customers (name, address, phone) VALUES (?, ?, ?)", (cname, address, phone))

    if sid:
        cur.execute("""
            UPDATE sales
            SET date = ?, order_no = ?, product_name = ?, spec = ?, unit_price = ?, qty = ?, amount = ?, seller = ?, customer_name = ?, address = ?, phone = ?
            WHERE id = ?
        """, (date_str, order_no, pname, spec, unit_price, qty, amount, seller, cname, address, phone, sid))
    else:
        cur.execute("""
            INSERT INTO sales (date, order_no, product_name, spec, unit_price, qty, amount, seller, customer_name, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, order_no, pname, spec, unit_price, qty, amount, seller, cname, address, phone))

    conn.commit()
    conn.close()
    return {"ok": True}


def delete_sale(sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sales WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_payment(data):
    conn = get_conn()
    cur = conn.cursor()
    sname = str(data.get("supplier_name", "")).strip()
    amount = float(data.get("amount", 0.0) or 0.0)
    if not sname or amount <= 0:
        conn.close()
        return {"ok": False, "error": "供应商名称和有效金额为必填项"}

    pid = data.get("id")
    date_str = normalize_date_str(data.get("date", ""))
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    payer = str(data.get("payer", "")).strip()
    payee = str(data.get("payee", "")).strip()

    if pid:
        cur.execute("""
            UPDATE supplier_payments
            SET date = ?, supplier_name = ?, address = ?, phone = ?, amount = ?, payer = ?, payee = ?
            WHERE id = ?
        """, (date_str, sname, address, phone, amount, payer, payee, pid))
    else:
        cur.execute("""
            INSERT INTO supplier_payments (date, supplier_name, address, phone, amount, payer, payee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_str, sname, address, phone, amount, payer, payee))

    conn.commit()
    conn.close()
    return {"ok": True}


def delete_payment(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM supplier_payments WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return {"ok": True}


def save_receipt(data):
    conn = get_conn()
    cur = conn.cursor()
    cname = str(data.get("customer_name", "")).strip()
    amount = float(data.get("amount", 0.0) or 0.0)
    if not cname or amount <= 0:
        conn.close()
        return {"ok": False, "error": "客户名称和有效金额为必填项"}

    rid = data.get("id")
    date_str = normalize_date_str(data.get("date", ""))
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    payer = str(data.get("payer", "")).strip()
    payee = str(data.get("payee", "")).strip()

    if rid:
        cur.execute("""
            UPDATE customer_receipts
            SET date = ?, customer_name = ?, address = ?, phone = ?, amount = ?, payer = ?, payee = ?
            WHERE id = ?
        """, (date_str, cname, address, phone, amount, payer, payee, rid))
    else:
        cur.execute("""
            INSERT INTO customer_receipts (date, customer_name, address, phone, amount, payer, payee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_str, cname, address, phone, amount, payer, payee))

    conn.commit()
    conn.close()
    return {"ok": True}


def delete_receipt(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM customer_receipts WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ================= Dashboard State Engine =================

def normalize_date_str(val):
    import re
    from datetime import timedelta
    s = str(val or "").strip()
    if not s:
        return datetime.now().strftime("%Y-%m-%d")
    # Handle Excel serial date numbers (e.g. 46332 -> 2026-11-06)
    if re.match(r"^\d{5}(?:\.0+)?$", s):
        days = int(float(s))
        if 35000 <= days <= 65000:
            return (datetime(1899, 12, 30) + timedelta(days=days)).strftime("%Y-%m-%d")
    m = re.search(r"(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s


def get_dashboard_state():
    conn = get_conn()
    cur = conn.cursor()

    # Auto-heal any non-padded or Excel serial dates in transaction tables so chronological sorting is 100% accurate
    dirty_dates = False
    for tbl in ("purchases", "sales", "supplier_payments", "customer_receipts"):
        cur.execute(f"DELETE FROM {tbl} WHERE batch_id IN (SELECT id FROM import_batches WHERE status = 'rolled_back')")
        if cur.rowcount > 0:
            dirty_dates = True
        rows_to_check = cur.execute(f"SELECT id, date FROM {tbl}").fetchall()
        for r in rows_to_check:
            norm_d = normalize_date_str(r["date"])
            if norm_d != r["date"]:
                cur.execute(f"UPDATE {tbl} SET date = ? WHERE id = ?", (norm_d, r["id"]))
                dirty_dates = True
    if dirty_dates:
        conn.commit()

    products = [dict(r) for r in cur.execute("SELECT * FROM products ORDER BY id DESC").fetchall()]
    customers = [dict(r) for r in cur.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()]
    suppliers = [dict(r) for r in cur.execute("SELECT * FROM suppliers ORDER BY id DESC").fetchall()]

    purchases = [dict(r) for r in cur.execute("""
        SELECT p.*, b.batch_code, b.source_name
        FROM purchases p
        LEFT JOIN import_batches b ON p.batch_id = b.id
        WHERE b.status IS NULL OR b.status = 'committed'
        ORDER BY p.date DESC, p.id DESC
    """).fetchall()]

    sales = [dict(r) for r in cur.execute("""
        SELECT s.*, b.batch_code, b.source_name
        FROM sales s
        LEFT JOIN import_batches b ON s.batch_id = b.id
        WHERE b.status IS NULL OR b.status = 'committed'
        ORDER BY s.date DESC, s.id DESC
    """).fetchall()]

    supplier_payments = [dict(r) for r in cur.execute("""
        SELECT sp.*, b.batch_code, b.source_name
        FROM supplier_payments sp
        LEFT JOIN import_batches b ON sp.batch_id = b.id
        WHERE b.status IS NULL OR b.status = 'committed'
        ORDER BY sp.date DESC, sp.id DESC
    """).fetchall()]

    customer_receipts = [dict(r) for r in cur.execute("""
        SELECT cr.*, b.batch_code, b.source_name
        FROM customer_receipts cr
        LEFT JOIN import_batches b ON cr.batch_id = b.id
        WHERE b.status IS NULL OR b.status = 'committed'
        ORDER BY cr.date DESC, cr.id DESC
    """).fetchall()]

    batches = [dict(r) for r in cur.execute("""
        SELECT * FROM import_batches ORDER BY created_at DESC, id DESC
    """).fetchall()]

    ai_cfg_row = cur.execute("SELECT * FROM ai_settings WHERE id = 1").fetchone()
    ai_cfg = dict(ai_cfg_row) if ai_cfg_row else {"provider": "deepseek", "base_url": "", "model_name": "", "api_key": ""}
    conn.close()

    # --- 1. Inventory Ledger ---
    inventory_ledger = []
    total_stock_qty = 0
    total_stock_value = 0.0
    total_in_amount = 0.0
    total_out_amount = 0.0
    low_stock_items = []

    for prod in products:
        pname = prod["name"]
        p_purchases = [x for x in purchases if x["product_name"] == pname]
        p_sales = [x for x in sales if x["product_name"] == pname]

        in_qty = round(sum(float(x["qty"]) for x in p_purchases), 2)
        in_amount = round(sum(float(x["amount"]) for x in p_purchases), 2)
        in_price = prod["purchase_price"]
        if in_qty > 0 and in_price <= 0:
            in_price = round(in_amount / in_qty, 2)

        out_qty = round(sum(float(x["qty"]) for x in p_sales), 2)
        out_amount = round(sum(float(x["amount"]) for x in p_sales), 2)
        out_price = round(out_amount / out_qty, 2) if out_qty > 0 else None

        opening_qty = round(float(prod["opening_qty"] or 0.0), 2)
        stock_qty = round(opening_qty + in_qty - out_qty, 2)
        stock_amount = round(stock_qty * float(in_price), 2)
        safety_stock = round(float(prod["safety_stock"] or 30.0), 2)
        is_low = stock_qty < safety_stock

        all_p_dates = [x["date"] for x in p_purchases if x.get("date")] + [x["date"] for x in p_sales if x.get("date")]
        latest_date = max(all_p_dates) if all_p_dates else "1970-01-01"
        latest_tx_id = max([x["id"] for x in p_purchases] + [x["id"] for x in p_sales], default=0)

        row = {
            "id": prod["id"],
            "product_name": pname,
            "category": prod.get("category") or "未分类",
            "spec": prod["spec"],
            "sale_price": prod["sale_price"],
            "purchase_price": prod["purchase_price"],
            "opening_qty": opening_qty if opening_qty % 1 != 0 else int(opening_qty),
            "in_qty": in_qty if in_qty % 1 != 0 else int(in_qty),
            "in_price": in_price if in_qty > 0 or opening_qty > 0 else prod["purchase_price"],
            "in_amount": in_amount,
            "out_qty": out_qty if out_qty % 1 != 0 else int(out_qty),
            "out_price": out_price,
            "out_amount": out_amount,
            "stock_qty": stock_qty if stock_qty % 1 != 0 else int(stock_qty),
            "stock_amount": stock_amount,
            "safety_stock": safety_stock if safety_stock % 1 != 0 else int(safety_stock),
            "is_low_stock": is_low,
            "shortage_qty": max(0, round(safety_stock - stock_qty, 2)),
            "latest_date": latest_date,
            "latest_tx_id": latest_tx_id,
        }
        inventory_ledger.append(row)
        total_stock_qty += stock_qty
        total_stock_value += stock_amount
        total_in_amount += in_amount
        total_out_amount += out_amount
        if is_low:
            low_stock_items.append(row)

    # Default sort inventory by latest transaction date descending, then newest product id
    inventory_ledger.sort(key=lambda x: (x["latest_date"], x["latest_tx_id"], x["id"]), reverse=True)

    # --- 2. Supplier AP Ledger ---
    ap_rows = []
    for sup in suppliers:
        sname = sup["name"]
        s_purchases = [x for x in purchases if x["supplier_name"] == sname]
        s_payments = [x for x in supplier_payments if x["supplier_name"] == sname]

        p_amt = round(sum(float(x["amount"]) for x in s_purchases), 2)
        paid_amt = round(sum(float(x["amount"]) for x in s_payments), 2)
        opening_ap = round(float(sup.get("opening_ap", 0.0) or 0.0), 2)
        ap_bal = round(opening_ap + p_amt - paid_amt, 2)

        all_s_dates = [x["date"] for x in s_purchases if x.get("date")] + [x["date"] for x in s_payments if x.get("date")]
        latest_date = max(all_s_dates) if all_s_dates else "1970-01-01"
        latest_tx_id = max([x["id"] for x in s_purchases] + [x["id"] for x in s_payments], default=0)

        ap_rows.append({
            "id": sup["id"],
            "supplier_name": sname,
            "address": sup["address"],
            "phone": sup["phone"],
            "opening_ap": opening_ap,
            "purchase_amount": p_amt,
            "paid_amount": paid_amt,
            "ap_balance": ap_bal,
            "ap_share": 0.0,
            "rank": 0,
            "latest_date": latest_date,
            "latest_tx_id": latest_tx_id,
        })

    total_ap = round(sum(x["ap_balance"] for x in ap_rows), 2)
    sorted_ap = sorted(ap_rows, key=lambda x: x["ap_balance"], reverse=True)
    rank_map_ap = {item["supplier_name"]: idx + 1 for idx, item in enumerate(sorted_ap)}
    for r in ap_rows:
        r["ap_share"] = round((r["ap_balance"] / total_ap) * 100, 2) if total_ap > 0 else 0.0
        r["rank"] = rank_map_ap[r["supplier_name"]]
    ap_rows.sort(key=lambda x: (x["latest_date"], x["latest_tx_id"], x["id"]), reverse=True)

    # --- 3. Customer AR Ledger ---
    ar_rows = []
    for cust in customers:
        cname = cust["name"]
        c_sales = [x for x in sales if x["customer_name"] == cname]
        c_receipts = [x for x in customer_receipts if x["customer_name"] == cname]

        s_amt = round(sum(float(x["amount"]) for x in c_sales), 2)
        rec_amt = round(sum(float(x["amount"]) for x in c_receipts), 2)
        opening_ar = round(float(cust.get("opening_ar", 0.0) or 0.0), 2)
        ar_bal = round(opening_ar + s_amt - rec_amt, 2)

        all_c_dates = [x["date"] for x in c_sales if x.get("date")] + [x["date"] for x in c_receipts if x.get("date")]
        latest_date = max(all_c_dates) if all_c_dates else "1970-01-01"
        latest_tx_id = max([x["id"] for x in c_sales] + [x["id"] for x in c_receipts], default=0)

        ar_rows.append({
            "id": cust["id"],
            "customer_name": cname,
            "address": cust["address"],
            "phone": cust["phone"],
            "opening_ar": opening_ar,
            "sales_amount": s_amt,
            "received_amount": rec_amt,
            "ar_balance": ar_bal,
            "ar_share": 0.0,
            "rank": 0,
            "latest_date": latest_date,
            "latest_tx_id": latest_tx_id,
        })

    total_ar = round(sum(x["ar_balance"] for x in ar_rows), 2)
    sorted_ar = sorted(ar_rows, key=lambda x: x["ar_balance"], reverse=True)
    rank_map_ar = {item["customer_name"]: idx + 1 for idx, item in enumerate(sorted_ar)}
    for r in ar_rows:
        r["ar_share"] = round((r["ar_balance"] / total_ar) * 100, 2) if total_ar > 0 else 0.0
        r["rank"] = rank_map_ar[r["customer_name"]]
    ar_rows.sort(key=lambda x: (x["latest_date"], x["latest_tx_id"], x["id"]), reverse=True)

    # --- 4. Profit & Diagnostics ---
    prod_cost_map = {p["name"]: float(p["purchase_price"]) for p in products}
    total_cogs = 0.0
    price_anomalies = []
    for s in sales:
        unit_cost = prod_cost_map.get(s["product_name"], 0.0)
        total_cogs += unit_cost * int(s["qty"])
        prod_obj = next((p for p in products if p["name"] == s["product_name"]), None)
        if prod_obj and abs(float(s["unit_price"]) - float(prod_obj["sale_price"])) > 0.01:
            diff = round(float(s["unit_price"]) - float(prod_obj["sale_price"]), 2)
            price_anomalies.append({
                "order_no": s["order_no"],
                "product_name": s["product_name"],
                "customer_name": s["customer_name"],
                "actual_price": s["unit_price"],
                "standard_price": prod_obj["sale_price"],
                "diff": diff
            })

    gross_profit = round(total_out_amount - total_cogs, 2)
    gross_margin = round((gross_profit / total_out_amount) * 100, 2) if total_out_amount > 0 else 0.0

    ai_insights = []
    for item in low_stock_items:
        matched_sup = next((p["supplier_name"] for p in purchases if p["product_name"] == item["product_name"]), "默认供应商")
        restock_qty = max(50 - item["stock_qty"], item["safety_stock"] - item["stock_qty"] + 20)
        est_cost = round(restock_qty * float(item["purchase_price"]), 2)
        ai_insights.append({
            "level": "critical",
            "category": "库存安全预警",
            "title": f"【{item['product_name']}】当前库存仅剩 {item['stock_qty']} {item['spec']}，低于安全库存 ({item['safety_stock']}{item['spec']})",
            "detail": f"本期入库 {item['in_qty']} 件，集中出库 {item['out_qty']} 件。建议立即向【{matched_sup}】补货 {restock_qty} 件（预计采购资金 ¥{est_cost:,.2f}）。",
            "quick_action": f"向{matched_sup}采购{item['product_name']}{restock_qty}件，单价{item['purchase_price']}"
        })

    if sorted_ar and sorted_ar[0]["ar_balance"] > 20000:
        top_ar = sorted_ar[0]
        ai_insights.append({
            "level": "warning",
            "category": "应收催收提醒",
            "title": f"【{top_ar['customer_name']}】累计应收款达 ¥{top_ar['ar_balance']:,.2f}（占总应收 {top_ar['ar_share']}%，排名第 1）",
            "detail": f"上期结转 ¥{top_ar['opening_ar']:,.2f} + 本期拿货 ¥{top_ar['sales_amount']:,.2f}，本期仅回款 ¥{top_ar['received_amount']:,.2f}，建议核对并安排催收。",
            "quick_action": f"收到{top_ar['customer_name']}回款10000元，交款人张三，收款人李静"
        })

    for pa in price_anomalies:
        direction = "溢价成交" if pa["diff"] > 0 else "折价销售"
        ai_insights.append({
            "level": "info",
            "category": "成交价浮动监测",
            "title": f"销售单【{pa['order_no']}】{pa['product_name']} 发生{direction}（实售 ¥{pa['actual_price']} vs 标价 ¥{pa['standard_price']}）",
            "detail": f"客户：{pa['customer_name']}，单件差额 {'+' if pa['diff'] > 0 else ''}{pa['diff']} 元，系统已自动按实际成交价核算应收与毛利。",
            "quick_action": ""
        })

    return {
        "kpis": {
            "total_stock_qty": total_stock_qty,
            "total_stock_value": round(total_stock_value, 2),
            "low_stock_count": len(low_stock_items),
            "total_purchase_amount": round(total_in_amount, 2),
            "total_sales_amount": round(total_out_amount, 2),
            "gross_profit": gross_profit,
            "gross_margin": gross_margin,
            "total_ar": total_ar,
            "total_ap": total_ap,
            "total_received": round(sum(float(x["amount"]) for x in customer_receipts), 2),
            "total_paid": round(sum(float(x["amount"]) for x in supplier_payments), 2),
            "is_empty": (len(products) == 0 and len(purchases) == 0 and len(sales) == 0)
        },
        "inventory_ledger": inventory_ledger,
        "ap_ledger": ap_rows,
        "ar_ledger": ar_rows,
        "purchases": purchases,
        "sales": sales,
        "supplier_payments": supplier_payments,
        "customer_receipts": customer_receipts,
        "customers": customers,
        "suppliers": suppliers,
        "products": products,
        "batches": batches,
        "ai_insights": ai_insights,
        "ai_settings": {
            "provider": ai_cfg["provider"],
            "base_url": ai_cfg["base_url"],
            "model_name": ai_cfg["model_name"],
            "has_key": bool(ai_cfg["api_key"] and len(ai_cfg["api_key"].strip()) > 5),
            "masked_key": (ai_cfg["api_key"][:4] + "****" + ai_cfg["api_key"][-4:]) if len(ai_cfg.get("api_key", "")) > 8 else ""
        }
    }
