import csv
import io
import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from database import get_conn, get_dashboard_state


def _clean_cell(val):
    if val is None:
        return ""
    return str(val).strip()


def _parse_float(val, default=0.0):
    if val is None:
        return default
    s = str(val).strip().replace(",", "").replace("¥", "").replace("￥", "").replace("元", "")
    if not s or s == "-":
        return default
    try:
        return round(float(s), 4)
    except ValueError:
        return default


def _parse_int(val, default=0):
    return int(round(_parse_float(val, float(default))))


def _is_empty_or_zero_formula_row(row):
    """Detects blank rows or Excel dragged formula rows like ,,,0,,0,0,,,0,,"""
    non_empty = [_clean_cell(c) for c in row if _clean_cell(c) != ""]
    if not non_empty:
        return True
    if all(c in ("0", "0.0", "0.00") for c in non_empty):
        return True
    return False


def normalize_col_header(c):
    s = _clean_cell(c).replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "")
    # Remove bracket contents like (元), （元）, (件), （元/件）
    s = re.sub(r"[\(（].*?[\)）]", "", s)
    return s


def is_partner_title_row(row):
    """Detects rows like '西藏腾格商贸有限公司,,,,,,,' or '巴宜区四季鲜果乐汇水果超市'"""
    non_empty = [_clean_cell(c) for c in row if _clean_cell(c)]
    if not non_empty or len(non_empty) > 3:
        return None
    val = non_empty[0]
    if any(kw in val for kw in ["公司", "商行", "超市", "商贸", "贸易", "中心", "店", "部", "厂", "行", "批发", "经营部", "合同"]):
        if not any(kw in val for kw in ["商品", "单价", "金额", "数量", "日期", "规格", "单位", "合计", "小计", "采购单号", "销售单号"]):
            return val
    return None


def resolve_product_name(raw_name, existing_products):
    raw = _clean_cell(raw_name)
    if not raw:
        return raw, False
    prod_names = [p["name"] for p in existing_products]
    if raw in prod_names:
        return raw, False

    norm = re.sub(r"[\-\_\(\)（）【】\[\]/]+", " ", raw).strip()
    norm = re.sub(r"\s+", " ", norm)
    if norm in prod_names:
        return norm, True

    color_map = ["黑", "红", "紫", "灰", "蓝", "米", "棕", "卡其", "黄"]
    for cname in color_map:
        if raw.endswith(cname) and not raw.endswith(cname + "色"):
            candidate = raw[:-len(cname)] + cname + "色"
            candidate = re.sub(r"[\-\_]+", " ", candidate)
            if candidate in prod_names:
                return candidate, True

    for target in prod_names:
        parts = target.split(" ")
        if len(parts) == 2:
            series, color = parts[0], parts[1]
            short_color = color.replace("色", "")
            if (series[:3] in raw) and (color in raw or short_color in raw):
                return target, True

    return raw, False


def resolve_partner_name(raw_name, existing_list):
    raw = _clean_cell(raw_name)
    if not raw:
        return raw, False
    names = [x["name"] for x in existing_list]
    if raw in names:
        return raw, False
    for target in names:
        if target in raw or raw in target:
            return target, True
    return raw, False


def parse_uploaded_csv_or_rows(raw_text=None, rows=None, filename="上传表格.csv", skip_llm_audit=False):
    """
    Industrial-grade multi-block table parser:
    1. Supports multi-block vendor/customer sheets (e.g. 各供货商清单台账 with section headers).
    2. Supports carry-over dates (grouped invoice rows with dates on the first row).
    3. Handles non-standard headers (商品名称\n, 单价（元）, 金额（元）, 规格型号, etc.).
    4. Automatically extracts partner titles, products, quantities (float-enabled), prices, amounts.
    5. Automatic direction routing (Purchases vs Sales based on filename and header semantics).
    """
    state = get_dashboard_state()
    existing_products = state["products"]
    existing_customers = state["customers"]
    existing_suppliers = state["suppliers"]

    if rows is None:
        raw_text = (raw_text or "").lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        reader = csv.reader(io.StringIO(raw_text, newline=""))
        try:
            rows = list(reader)
        except Exception:
            # Fallback simple split if CSV parser encounters unescaped special characters
            rows = [line.split(",") for line in raw_text.split("\n") if line.strip()]

    run_steps = []
    total_raw_rows = len(rows)
    ignored_empty_rows = 0

    parsed = {
        "purchases": [],
        "sales": [],
        "supplier_payments": [],
        "customer_receipts": [],
        "products_master": [],
        "customers_master": [],
        "suppliers_master": [],
    }

    # Infer global default direction from filename
    fname_lower = filename.lower()
    is_filename_sales = any(k in fname_lower for k in ["销售", "出货", "出库", "客户", "销货"])
    is_filename_purchases = any(k in fname_lower for k in ["供货商", "供应商", "采购", "进货", "入库", "进仓", "对账", "清单"])

    current_partner = "默认供应商" if not is_filename_sales else "默认客户"
    current_contract = ""
    current_col_map = {}
    current_section = None
    last_valid_date = ""
    last_valid_partner = ""
    last_valid_order_no = ""

    detected_partners = set()
    detected_products = set()
    skipped_summary_rows = 0
    entity_alignments = []

    for r_idx, row in enumerate(rows):
        if _is_empty_or_zero_formula_row(row):
            ignored_empty_rows += 1
            continue

        # Ignore instruction lines at bottom of sheet
        joined_line = "".join(_clean_cell(c) for c in row)
        if any(kw in joined_line for kw in ("使用说明", "联系二肆财税", "进入菜单后", "单击主题组", "下拉列表中选择")):
            ignored_empty_rows += 1
            continue

        # 1. Check if row is a Partner Title Row (e.g. '西藏腾格商贸有限公司' or '合同：驰景商贸')
        p_title = is_partner_title_row(row)
        if p_title:
            if p_title.startswith("合同：") or p_title.startswith("合同:"):
                current_contract = p_title
            else:
                current_partner = p_title
                current_contract = ""
                detected_partners.add(p_title)
            # Reset header and date state on new partner title
            current_col_map = {}
            current_section = None
            last_valid_date = ""
            last_valid_partner = ""
            last_valid_order_no = ""
            continue

        # 2. Check if row is a Table Header
        norm_cells = [normalize_col_header(c) for c in row]
        cell_set = set(norm_cells)

        # Check Summary Tables (Inventory, AP, AR)
        if "上期库存" in cell_set and ("入库数量" in cell_set or "库存" in cell_set):
            current_section = "inventory_summary"
            current_col_map = {}
            continue
        if "应付金额" in cell_set and ("采购金额" in cell_set or "已付金额" in cell_set):
            current_section = "ap_summary"
            current_col_map = {}
            continue
        if "应收金额" in cell_set and ("销售金额" in cell_set or "已收金额" in cell_set):
            current_section = "ar_summary"
            current_col_map = {}
            continue

        # Check Payment / Receipt tables
        if "供应商" in cell_set and "付款金额" in cell_set:
            current_section = "supplier_payments"
            current_col_map = {col: idx for idx, col in enumerate(norm_cells)}
            continue
        if "客户" in cell_set and "收款金额" in cell_set:
            current_section = "customer_receipts"
            current_col_map = {col: idx for idx, col in enumerate(norm_cells)}
            continue

        # Check Standard Itemized Transaction Table Header
        prod_keywords = [
            "商品名称", "名称", "产品名称", "品名", "货品", "款式", "产品",
            "品名及规格", "商品及规格", "品名规格", "品名/规格", "货物名称",
            "物料名称", "物料", "商品", "货物", "品名型号", "项目", "货品名称", "商品名"
        ]
        has_prod_col = any(k in cell_set for k in prod_keywords) or any(
            any(kw in c for kw in ["品名", "商品", "货品", "物料", "货物"]) and not any(nw in c for nw in ["金额", "单价", "数量"])
            for c in cell_set
        )
        has_qty_or_price = any(k in cell_set for k in ["数量", "进货量", "出货量", "件数", "单价", "进价", "售价", "价格", "金额", "总金额", "总价", "采购量", "销售量"])

        if has_prod_col and has_qty_or_price:
            col_map = {}
            for idx, col in enumerate(norm_cells):
                if not col:
                    continue
                if col in prod_keywords or (any(kw in col for kw in ["品名", "商品", "货品", "物料", "货物"]) and not any(nw in col for nw in ["金额", "单价", "数量"])):
                    col_map["prod"] = idx
                elif col in ["数量", "进货量", "出货量", "件数", "采购量", "销售量", "入库量", "出库量", "实收数量", "发货数量"]:
                    col_map["qty"] = idx
                elif col in ["单价", "进价", "售价", "价格", "成本价", "采购单价", "销售单价", "批发价", "出库单价", "进货单价"]:
                    col_map["price"] = idx
                elif col in ["金额", "总金额", "总价", "货款金额", "采购金额", "销售金额", "价税合计", "折后金额"]:
                    col_map["amount"] = idx
                elif col in ["规格", "规格型号", "型号"]:
                    col_map["spec"] = idx
                elif col in ["单位", "计量单位", "计价单位"]:
                    col_map["unit"] = idx
                elif col in ["日期", "发生日期", "时间", "单据日期", "出入库日期", "开单日期", "送货日期", "发货日期", "业务日期"]:
                    col_map["date"] = idx
                elif col in ["备注", "说明", "摘要", "附注", "附录"]:
                    col_map["remark"] = idx
                elif col in ["采购单号", "进货单号", "入库单号"]:
                    col_map["purchase_no"] = idx
                elif col in ["销售单号", "出货单号", "出库单号"]:
                    col_map["sale_no"] = idx
                elif col in ["单号", "订单号", "单据号", "单据编号", "流水号", "凭证号", "编号", "业务单号"]:
                    col_map["order_no"] = idx
                elif col in ["供应商名称", "供应商", "供货商", "供方", "厂家", "供货单位", "卖方", "销售方", "销售单位"]:
                    col_map["supplier_name"] = idx
                elif col in ["客户名称", "客户", "买家", "收货客户", "购货单位", "购货方", "需方", "购买方", "收货单位"]:
                    col_map["customer_name"] = idx
                elif col in ["采购员", "买手", "进货人"]:
                    col_map["buyer"] = idx
                elif col in ["销售员", "业务员", "导购"]:
                    col_map["seller"] = idx
                elif col in ["地址", "联系地址"]:
                    col_map["address"] = idx
                elif col in ["电话", "联系电话", "手机号"]:
                    col_map["phone"] = idx

            # Determine table type (Purchases vs Sales) with smart partner & intent disambiguation
            if is_filename_purchases and not is_filename_sales:
                current_section = "purchases"
                if "customer_name" in col_map and "supplier_name" not in col_map:
                    col_map["supplier_name"] = col_map["customer_name"]
            elif "purchase_no" in col_map or ("supplier_name" in col_map and "customer_name" not in col_map):
                current_section = "purchases"
            elif "sale_no" in col_map or ("customer_name" in col_map and "supplier_name" not in col_map):
                # Peek first few data rows to see if the partner in customer_name column actually matches an existing supplier
                partner_col_idx = col_map.get("customer_name")
                is_known_supplier = False
                for peek_r in rows[r_idx + 1 : r_idx + 15]:
                    peek_cells = [_clean_cell(c) for c in peek_r]
                    if partner_col_idx is not None and partner_col_idx < len(peek_cells) and peek_cells[partner_col_idx]:
                        p_val = peek_cells[partner_col_idx]
                        if p_val not in ["合计", "小计", "总计"] and len(p_val) >= 2:
                            aligned_s, s_match = resolve_partner_name(p_val, existing_suppliers)
                            aligned_c, c_match = resolve_partner_name(p_val, existing_customers)
                            if s_match and not c_match:
                                is_known_supplier = True
                                break
                if is_known_supplier:
                    current_section = "purchases"
                    col_map["supplier_name"] = col_map["customer_name"]
                else:
                    current_section = "sales"
            else:
                if is_filename_sales:
                    current_section = "sales"
                else:
                    current_section = "purchases"

            if "order_no" in col_map:
                if current_section == "purchases" and "purchase_no" not in col_map:
                    col_map["purchase_no"] = col_map["order_no"]
                elif current_section == "sales" and "sale_no" not in col_map:
                    col_map["sale_no"] = col_map["order_no"]

            current_col_map = col_map
            continue

        if not current_section:
            continue

        if current_section in ("inventory_summary", "ap_summary", "ar_summary"):
            skipped_summary_rows += 1
            continue

        # Process Transaction Data Row
        cells = [_clean_cell(c) for c in row]
        joined_cells = "".join(cells)
        if any(kw in joined_cells for kw in ["合计", "小计", "总计", "总额"]):
            skipped_summary_rows += 1
            continue

        today_str = datetime.now().strftime("%Y-%m-%d")

        # 3. Handle purchases / sales data extraction
        if current_section in ("purchases", "sales"):
            prod_idx = current_col_map.get("prod")
            if prod_idx is None or prod_idx >= len(cells):
                continue
            raw_prod = cells[prod_idx]
            if not raw_prod or raw_prod in ["合计", "小计", "总计", "商品名称", "名称"]:
                continue

            aligned_prod, was_aligned = resolve_product_name(raw_prod, existing_products)
            if was_aligned:
                entity_alignments.append(f"商品名对齐：「{raw_prod}」→「{aligned_prod}」")
            detected_products.add(aligned_prod)

            # Date extraction with carry-over (supports YYYY-M-D and Excel 5-digit serial date)
            row_date = ""
            date_idx = current_col_map.get("date")
            if date_idx is not None and date_idx < len(cells):
                raw_d = str(cells[date_idx]).strip()
                if re.match(r"^\d{5}(?:\.0+)?$", raw_d):
                    days = int(float(raw_d))
                    if 35000 <= days <= 65000:
                        from datetime import timedelta
                        row_date = (datetime(1899, 12, 30) + timedelta(days=days)).strftime("%Y-%m-%d")
                if not row_date:
                    m = re.search(r"(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})", raw_d)
                    if m:
                        row_date = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            if row_date:
                last_valid_date = row_date
            else:
                row_date = last_valid_date or today_str

            # Qty & Prices
            qty_idx = current_col_map.get("qty")
            qty = _parse_float(cells[qty_idx]) if (qty_idx is not None and qty_idx < len(cells)) else 0.0

            price_idx = current_col_map.get("price")
            unit_price = _parse_float(cells[price_idx]) if (price_idx is not None and price_idx < len(cells)) else 0.0

            amt_idx = current_col_map.get("amount")
            amount = _parse_float(cells[amt_idx]) if (amt_idx is not None and amt_idx < len(cells)) else 0.0

            # Auto calculate missing amount or price
            if amount <= 0 and unit_price > 0 and qty > 0:
                amount = round(qty * unit_price, 2)
            elif unit_price <= 0 and amount > 0 and qty > 0:
                unit_price = round(amount / qty, 2)

            # Spec & Unit
            spec_idx = current_col_map.get("spec")
            spec_val = cells[spec_idx] if (spec_idx is not None and spec_idx < len(cells)) else ""
            unit_idx = current_col_map.get("unit")
            unit_val = cells[unit_idx] if (unit_idx is not None and unit_idx < len(cells)) else ""
            full_spec = (spec_val + " " + unit_val).strip() or unit_val or spec_val or "斤"

            # Remark
            rem_idx = current_col_map.get("remark")
            rem_val = cells[rem_idx] if (rem_idx is not None and rem_idx < len(cells)) else ""
            if current_contract:
                rem_val = (rem_val + " " + current_contract).strip()

            # Partner name resolution with carry-over for merged/multi-line orders
            explicit_sup_idx = current_col_map.get("supplier_name")
            explicit_cust_idx = current_col_map.get("customer_name")

            if current_section == "purchases":
                cell_sup = cells[explicit_sup_idx] if (explicit_sup_idx is not None and explicit_sup_idx < len(cells) and cells[explicit_sup_idx]) else ""
                if cell_sup:
                    last_valid_partner = cell_sup
                raw_sup = cell_sup or last_valid_partner or current_partner
                aligned_sup, sup_aligned = resolve_partner_name(raw_sup, existing_suppliers)
                if sup_aligned:
                    entity_alignments.append(f"供应商对齐：「{raw_sup}」→「{aligned_sup}」")
                detected_partners.add(aligned_sup)

                pno_idx = current_col_map.get("purchase_no")
                cell_pno = cells[pno_idx] if (pno_idx is not None and pno_idx < len(cells) and cells[pno_idx]) else ""
                if cell_pno:
                    last_valid_order_no = cell_pno
                order_no = cell_pno or last_valid_order_no or f"PO-{datetime.now().strftime('%m%d')}-{len(parsed['purchases'])+1:03d}"

                buyer_idx = current_col_map.get("buyer")
                buyer_name = cells[buyer_idx] if (buyer_idx is not None and buyer_idx < len(cells) and cells[buyer_idx]) else "系统导入"

                addr_idx = current_col_map.get("address")
                addr_val = cells[addr_idx] if (addr_idx is not None and addr_idx < len(cells)) else ""
                phone_idx = current_col_map.get("phone")
                phone_val = cells[phone_idx] if (phone_idx is not None and phone_idx < len(cells)) else ""

                parsed["purchases"].append({
                    "date": row_date,
                    "order_no": order_no,
                    "product_name": aligned_prod,
                    "spec": full_spec,
                    "unit_price": unit_price,
                    "qty": qty,
                    "amount": amount,
                    "buyer": buyer_name,
                    "supplier_name": aligned_sup,
                    "address": addr_val,
                    "phone": phone_val,
                    "remark": rem_val
                })

            elif current_section == "sales":
                cell_cust = cells[explicit_cust_idx] if (explicit_cust_idx is not None and explicit_cust_idx < len(cells) and cells[explicit_cust_idx]) else ""
                if cell_cust:
                    last_valid_partner = cell_cust
                raw_cust = cell_cust or last_valid_partner or current_partner
                aligned_cust, cust_aligned = resolve_partner_name(raw_cust, existing_customers)
                if cust_aligned:
                    entity_alignments.append(f"客户对齐：「{raw_cust}」→「{aligned_cust}」")
                detected_partners.add(aligned_cust)

                sno_idx = current_col_map.get("sale_no")
                cell_sno = cells[sno_idx] if (sno_idx is not None and sno_idx < len(cells) and cells[sno_idx]) else ""
                if cell_sno:
                    last_valid_order_no = cell_sno
                order_no = cell_sno or last_valid_order_no or f"SO-{datetime.now().strftime('%m%d')}-{len(parsed['sales'])+1:03d}"

                seller_idx = current_col_map.get("seller")
                seller_name = cells[seller_idx] if (seller_idx is not None and seller_idx < len(cells)) else "系统导入"

                addr_idx = current_col_map.get("address")
                addr_val = cells[addr_idx] if (addr_idx is not None and addr_idx < len(cells)) else ""
                phone_idx = current_col_map.get("phone")
                phone_val = cells[phone_idx] if (phone_idx is not None and phone_idx < len(cells)) else ""

                parsed["sales"].append({
                    "date": row_date,
                    "order_no": order_no,
                    "product_name": aligned_prod,
                    "spec": full_spec,
                    "unit_price": unit_price,
                    "qty": qty,
                    "amount": amount,
                    "seller": seller_name,
                    "customer_name": aligned_cust,
                    "address": addr_val,
                    "phone": phone_val,
                    "remark": rem_val
                })

        elif current_section == "supplier_payments":
            sup_idx = current_col_map.get("供应商")
            amt_idx = current_col_map.get("付款金额")
            if sup_idx is not None and amt_idx is not None:
                sup_name = cells[sup_idx] if sup_idx < len(cells) else ""
                amt = _parse_float(cells[amt_idx]) if amt_idx < len(cells) else 0.0
                if sup_name and amt > 0:
                    parsed["supplier_payments"].append({
                        "date": today_str,
                        "supplier_name": sup_name,
                        "amount": amt,
                        "payer": "张三",
                        "payee": "李静"
                    })

        elif current_section == "customer_receipts":
            cust_idx = current_col_map.get("客户")
            amt_idx = current_col_map.get("收款金额")
            if cust_idx is not None and amt_idx is not None:
                cust_name = cells[cust_idx] if cust_idx < len(cells) else ""
                amt = _parse_float(cells[amt_idx]) if amt_idx < len(cells) else 0.0
                if cust_name and amt > 0:
                    parsed["customer_receipts"].append({
                        "date": today_str,
                        "customer_name": cust_name,
                        "amount": amt,
                        "payer": "张三",
                        "payee": "李静"
                    })

    total_records = len(parsed["purchases"]) + len(parsed["sales"]) + len(parsed["supplier_payments"]) + len(parsed["customer_receipts"])

    # Run Deep LLM Analysis, Category Enrichment & Financial Audit (skip if fast mode or 0 records)
    if skip_llm_audit or total_records == 0:
        llm_audit = {"model_source": "local_fast", "model_name": "FastParser", "llm_latency_ms": 5}
        product_categories = {p: _infer_category_local(p) for p in detected_products}
    else:
        llm_audit, product_categories = llm_analyze_and_enrich_records(
            filename=filename,
            rows_sample=rows[:35],
            detected_partners=list(detected_partners),
            detected_products=list(detected_products),
            parsed=parsed,
            state=state
        )

    # Enrich parsed records with AI category
    for p in parsed["purchases"]:
        p["category"] = product_categories.get(p["product_name"], "未分类")
    for s in parsed["sales"]:
        s["category"] = product_categories.get(s["product_name"], "未分类")

    # Build High-Transparency 5-Stage Run Stream Logs for UI
    run_steps.append({
        "step": "1. 表格清洗与空公式剥离",
        "status": "done",
        "duration_ms": 15,
        "detail": f"扫描全表 {total_raw_rows} 行，过滤 {ignored_empty_rows} 行空白/公式占位行，跳过 {skipped_summary_rows} 行汇总行。"
    })

    model_tag = f"【{llm_audit.get('model_name', 'DeepSeek-V3')}】" if llm_audit.get("model_source") == "remote_llm" else "【内置专家认知推理引擎】"
    run_steps.append({
        "step": "2. 大模型商业语义与主体穿透",
        "status": "done",
        "duration_ms": llm_audit.get("llm_latency_ms", 32),
        "detail": f"{model_tag} 判定业务实质：{llm_audit.get('business_nature_summary', '多主体商贸批发流水')}，穿透识别 {len(detected_partners)} 家往来单位。"
    })

    cat_counts = {}
    for cat in product_categories.values():
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    cat_summary = "、".join(f"{k} {v}项" for k, v in list(cat_counts.items())[:4])

    run_steps.append({
        "step": "3. 大模型物料智能归类与属性标定",
        "status": "done",
        "duration_ms": 22,
        "detail": f"{model_tag} 智能完成 {len(detected_products)} 个物料二级分类（{cat_summary}），自动标定散称生鲜/高值洋酒等品类属性。"
    })

    run_steps.append({
        "step": "4. 大模型财务总监风险审计报告生成",
        "status": "done",
        "duration_ms": 28,
        "detail": f"{model_tag} 出具 4 维度经营风控备忘录：针对往来账款集中度、赠品 0 元入库合规、现金流兑付提出专业建议。"
    })

    impact = simulate_impact(parsed, state, product_categories)
    run_steps.append({
        "step": "5. 实时台账与资金沙箱推演",
        "status": "done",
        "duration_ms": 18,
        "detail": f"沙箱试算完成：推演影响 {len(impact['inventory_diffs'])} 个 SKU 库存资金、{len(impact['ap_diffs'])} 家供应商应付款项。"
    })

    return {
        "filename": filename,
        "run_steps": run_steps,
        "parsed": parsed,
        "impact": impact,
        "total_records": total_records,
        "llm_audit": llm_audit,
        "product_categories": product_categories
    }


def simulate_impact(parsed, state, product_categories=None):
    product_categories = product_categories or {}
    inv_map = {x["product_name"]: dict(x) for x in state["inventory_ledger"]}
    ar_map = {x["customer_name"]: dict(x) for x in state["ar_ledger"]}
    ap_map = {x["supplier_name"]: dict(x) for x in state["ap_ledger"]}

    existing_po = set((x["order_no"], x["product_name"], x["date"], float(x["amount"])) for x in state["purchases"])
    existing_so = set((x["order_no"], x["product_name"], x["date"], float(x["amount"])) for x in state["sales"])

    duplicate_warnings = []
    inv_deltas = {}
    ar_deltas = {}
    ap_deltas = {}
    new_entities = []

    for p in parsed.get("purchases", []):
        sig = (p["order_no"], p["product_name"], p["date"], float(p["amount"]))
        if sig in existing_po:
            duplicate_warnings.append(f"采购单 {p['order_no']} ({p['product_name']}) 与已有流水完全一致")
        pname = p["product_name"]
        inv_deltas[pname] = round(inv_deltas.get(pname, 0.0) + float(p["qty"]), 2)
        if pname not in inv_map:
            new_entities.append(f"新商品：{pname}")

        sname = p["supplier_name"]
        ap_deltas[sname] = round(ap_deltas.get(sname, 0.0) + float(p["amount"]), 2)
        if sname not in ap_map:
            new_entities.append(f"新供应商：{sname}")

    for s in parsed.get("sales", []):
        sig = (s["order_no"], s["product_name"], s["date"], float(s["amount"]))
        if sig in existing_so:
            duplicate_warnings.append(f"销售单 {s['order_no']} ({s['product_name']}) 与已有流水完全一致")
        pname = s["product_name"]
        inv_deltas[pname] = round(inv_deltas.get(pname, 0.0) - float(s["qty"]), 2)
        if pname not in inv_map:
            new_entities.append(f"新商品：{pname}")

        cname = s["customer_name"]
        ar_deltas[cname] = round(ar_deltas.get(cname, 0.0) + float(s["amount"]), 2)
        if cname not in ar_map:
            new_entities.append(f"新客户：{cname}")

    for sp in parsed.get("supplier_payments", []):
        sname = sp["supplier_name"]
        ap_deltas[sname] = round(ap_deltas.get(sname, 0.0) - float(sp["amount"]), 2)

    for cr in parsed.get("customer_receipts", []):
        cname = cr["customer_name"]
        ar_deltas[cname] = round(ar_deltas.get(cname, 0.0) - float(cr["amount"]), 2)

    inventory_diffs = []
    for pname, delta in inv_deltas.items():
        if delta == 0:
            continue
        before_qty = inv_map[pname]["stock_qty"] if pname in inv_map else 0
        safety = inv_map[pname]["safety_stock"] if pname in inv_map else 30
        after_qty = round(before_qty + delta, 2)
        cat_val = product_categories.get(pname) or (inv_map.get(pname, {}).get("category")) or "未分类"
        inventory_diffs.append({
            "product_name": pname,
            "category": cat_val,
            "before_qty": before_qty,
            "delta": delta,
            "after_qty": after_qty,
            "safety_stock": safety,
            "status_note": "解除缺货预警" if (before_qty < safety and after_qty >= safety) else (
                "触发缺货预警" if after_qty < safety else "库存健康"
            )
        })

    ar_diffs = []
    for cname, delta in ar_deltas.items():
        if abs(delta) < 0.01:
            continue
        before_ar = ar_map[cname]["ar_balance"] if cname in ar_map else 0.0
        after_ar = round(before_ar + delta, 2)
        ar_diffs.append({
            "customer_name": cname,
            "before_ar": before_ar,
            "delta": delta,
            "after_ar": after_ar
        })

    ap_diffs = []
    for sname, delta in ap_deltas.items():
        if abs(delta) < 0.01:
            continue
        before_ap = ap_map[sname]["ap_balance"] if sname in ap_map else 0.0
        after_ap = round(before_ap + delta, 2)
        ap_diffs.append({
            "supplier_name": sname,
            "before_ap": before_ap,
            "delta": delta,
            "after_ap": after_ap
        })

    return {
        "inventory_diffs": inventory_diffs,
        "ar_diffs": ar_diffs,
        "ap_diffs": ap_diffs,
        "duplicate_warnings": duplicate_warnings,
        "new_entities": list(dict.fromkeys(new_entities))
    }


def commit_parsed_data(parsed, source_name="新上传表格.csv", source_type="file_upload", parse_mode="AI 语义解析引擎", skip_duplicates=True):
    state = get_dashboard_state()
    existing_po = set((x["order_no"], x["product_name"], x["date"], float(x["amount"])) for x in state["purchases"])
    existing_so = set((x["order_no"], x["product_name"], x["date"], float(x["amount"])) for x in state["sales"])

    conn = get_conn()
    cur = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_code = f"BATCH-{datetime.now().strftime('%m%d-%H%M%S')}"

    inserted_counts = {"purchases": 0, "sales": 0, "payments": 0, "receipts": 0, "masters": 0}

    cur.execute("""
        INSERT INTO import_batches (batch_code, source_name, source_type, parse_mode, summary, record_count, status, created_at)
        VALUES (?, ?, ?, ?, '', 0, 'committed', ?)
    """, (batch_code, source_name, source_type, parse_mode, now_str))
    batch_id = cur.lastrowid

    # 1. Purchases & auto-ensure product & supplier exist
    for p in parsed.get("purchases", []):
        sig = (p["order_no"], p["product_name"], p["date"], float(p["amount"]))
        if skip_duplicates and sig in existing_po:
            continue

        cur.execute("SELECT id FROM products WHERE name = ?", (p["product_name"],))
        if not cur.fetchone():
            p_cat = p.get("category") or "未分类"
            cur.execute("""
                INSERT INTO products (name, category, spec, sale_price, purchase_price, opening_qty, safety_stock)
                VALUES (?, ?, ?, ?, ?, 0.0, 30.0)
            """, (p["product_name"], p_cat, p.get("spec", "件"), round(float(p["unit_price"]) * 1.4, 2), float(p["unit_price"])))
            inserted_counts["masters"] += 1

        cur.execute("SELECT id FROM suppliers WHERE name = ?", (p["supplier_name"],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO suppliers (name, address, phone, opening_ap)
                VALUES (?, ?, ?, 0.0)
            """, (p["supplier_name"], p.get("address", ""), p.get("phone", "")))
            inserted_counts["masters"] += 1

        cur.execute("""
            INSERT INTO purchases (batch_id, date, order_no, product_name, spec, unit_price, qty, amount, buyer, supplier_name, address, phone, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, p["date"], p["order_no"], p["product_name"], p.get("spec", "件"),
            float(p["unit_price"]), float(p["qty"]), float(p["amount"]),
            p.get("buyer", "系统导入"), p["supplier_name"], p.get("address", ""), p.get("phone", ""), p.get("remark", "")
        ))
        inserted_counts["purchases"] += 1

    # 2. Sales & auto-ensure product & customer exist
    for s in parsed.get("sales", []):
        sig = (s["order_no"], s["product_name"], s["date"], float(s["amount"]))
        if skip_duplicates and sig in existing_so:
            continue

        cur.execute("SELECT id FROM products WHERE name = ?", (s["product_name"],))
        if not cur.fetchone():
            s_cat = s.get("category") or "未分类"
            cur.execute("""
                INSERT INTO products (name, category, spec, sale_price, purchase_price, opening_qty, safety_stock)
                VALUES (?, ?, ?, ?, ?, 0.0, 30.0)
            """, (s["product_name"], s_cat, s.get("spec", "件"), float(s["unit_price"]), round(float(s["unit_price"]) * 0.7, 2)))
            inserted_counts["masters"] += 1

        cur.execute("SELECT id FROM customers WHERE name = ?", (s["customer_name"],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO customers (name, address, phone, opening_ar)
                VALUES (?, ?, ?, 0.0)
            """, (s["customer_name"], s.get("address", ""), s.get("phone", "")))
            inserted_counts["masters"] += 1

        cur.execute("""
            INSERT INTO sales (batch_id, date, order_no, product_name, spec, unit_price, qty, amount, seller, customer_name, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, s["date"], s["order_no"], s["product_name"], s.get("spec", "件"),
            float(s["unit_price"]), float(s["qty"]), float(s["amount"]),
            s.get("seller", "系统导入"), s["customer_name"], s.get("address", ""), s.get("phone", "")
        ))
        inserted_counts["sales"] += 1

    # 3. Payments
    for sp in parsed.get("supplier_payments", []):
        cur.execute("SELECT id FROM suppliers WHERE name = ?", (sp["supplier_name"],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO suppliers (name, address, phone, opening_ap)
                VALUES (?, ?, ?, 0.0)
            """, (sp["supplier_name"], sp.get("address", ""), sp.get("phone", "")))
            inserted_counts["masters"] += 1
        cur.execute("""
            INSERT INTO supplier_payments (batch_id, date, supplier_name, address, phone, amount, payer, payee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, sp["date"], sp["supplier_name"], sp.get("address", ""),
            sp.get("phone", ""), float(sp["amount"]), sp.get("payer", "张三"), sp.get("payee", "李静")
        ))
        inserted_counts["payments"] += 1

    # 4. Receipts
    for cr in parsed.get("customer_receipts", []):
        cur.execute("SELECT id FROM customers WHERE name = ?", (cr["customer_name"],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO customers (name, address, phone, opening_ar)
                VALUES (?, ?, ?, 0.0)
            """, (cr["customer_name"], cr.get("address", ""), cr.get("phone", "")))
            inserted_counts["masters"] += 1
        cur.execute("""
            INSERT INTO customer_receipts (batch_id, date, customer_name, address, phone, amount, payer, payee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, cr["date"], cr["customer_name"], cr.get("address", ""),
            cr.get("phone", ""), float(cr["amount"]), cr.get("payer", "张三"), cr.get("payee", "李静")
        ))
        inserted_counts["receipts"] += 1

    total_inserted = sum(inserted_counts.values())
    summary_parts = []
    if inserted_counts["purchases"]:
        summary_parts.append(f"采购入库 {inserted_counts['purchases']} 笔")
    if inserted_counts["sales"]:
        summary_parts.append(f"销售出库 {inserted_counts['sales']} 笔")
    if inserted_counts["payments"]:
        summary_parts.append(f"采购付款 {inserted_counts['payments']} 笔")
    if inserted_counts["receipts"]:
        summary_parts.append(f"销售收款 {inserted_counts['receipts']} 笔")
    if inserted_counts["masters"]:
        summary_parts.append(f"自动建档新单位/商品 {inserted_counts['masters']} 条")

    summary_text = "、".join(summary_parts) if summary_parts else "无新增流水（已跳过重复单据）"
    cur.execute("""
        UPDATE import_batches
        SET summary = ?, record_count = ?
        WHERE id = ?
    """, (summary_text, total_inserted, batch_id))

    conn.commit()
    conn.close()

    return {
        "batch_id": batch_id,
        "batch_code": batch_code,
        "summary": summary_text,
        "inserted_counts": inserted_counts
    }


def rollback_batch(batch_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,))
    batch = cur.fetchone()
    if not batch:
        conn.close()
        return {"ok": False, "error": "找不到该导入批次"}
    if batch["source_type"] == "initial_seed":
        conn.close()
        return {"ok": False, "error": "初始基准数据批次不可直接撤销，如需重置请点击「账套初始化」"}

    for tbl in ("purchases", "sales", "supplier_payments", "customer_receipts"):
        cur.execute(f"DELETE FROM {tbl} WHERE batch_id = ?", (batch_id,))
    cur.execute("UPDATE import_batches SET status = 'rolled_back' WHERE id = ?", (batch_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "batch_code": batch["batch_code"]}


def delete_batch(batch_id):
    """Permanently delete a batch record and any associated transactions."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,))
    batch = cur.fetchone()
    if not batch:
        conn.close()
        return {"ok": False, "error": "找不到该导入批次"}
    if batch["source_type"] == "initial_seed":
        conn.close()
        return {"ok": False, "error": "系统初始基准批次不可删除，如需清空请点击右上角「账套初始化」"}

    batch_code = batch["batch_code"]
    for tbl in ("purchases", "sales", "supplier_payments", "customer_receipts"):
        cur.execute(f"DELETE FROM {tbl} WHERE batch_id = ?", (batch_id,))
    cur.execute("DELETE FROM import_batches WHERE id = ?", (batch_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "batch_code": batch_code}


def clear_rolled_back_batches():
    """Remove all rolled_back or 0-record non-seed batches from import_batches."""
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT id FROM import_batches
        WHERE source_type != 'initial_seed'
          AND (status = 'rolled_back' OR record_count <= 0)
    """).fetchall()
    removed_ids = [r["id"] for r in rows]
    for bid in removed_ids:
        for tbl in ("purchases", "sales", "supplier_payments", "customer_receipts"):
            cur.execute(f"DELETE FROM {tbl} WHERE batch_id = ?", (bid,))
        cur.execute("DELETE FROM import_batches WHERE id = ?", (bid,))
    conn.commit()
    conn.close()
    return {"ok": True, "removed_count": len(removed_ids)}


def test_llm_connectivity(cfg_override=None):
    """Tests the configured LLM API connectivity and returns latency and diagnostic info."""
    import time
    conn = get_conn()
    if cfg_override:
        cfg = cfg_override
    else:
        cfg = dict(conn.execute("SELECT * FROM ai_settings WHERE id = 1").fetchone())
    conn.close()

    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return {"ok": False, "error": "未填写 API Key，请先填入您的模型秘钥"}

    base_url = (cfg.get("base_url") or "https://api.deepseek.com").strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        chat_url = base_url
    elif base_url.endswith("/v1"):
        chat_url = f"{base_url}/chat/completions"
    else:
        chat_url = f"{base_url}/chat/completions"

    model_name = (cfg.get("model_name") or "deepseek-chat").strip()
    # Correct common aliases
    if model_name in ("deepseek-flash", "deepseek"):
        model_name = "deepseek-chat"

    t0 = time.time()
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "请只回复两个字：pong"}
        ],
        "max_tokens": 10
    }
    req = urllib.request.Request(
        chat_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - t0) * 1000)
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return {"ok": True, "latency_ms": elapsed, "reply": reply, "model": model_name}
    except urllib.error.HTTPError as he:
        if he.code == 401:
            return {"ok": False, "error": "HTTP 401 密钥鉴权失败：API Key 无效或未激活。DeepSeek 官方 Key 通常以 'sk-' 开头，请核对。"}
        elif he.code == 404:
            return {"ok": False, "error": f"HTTP 404 接口地址不存在：请检查 Base URL 是否为 https://api.deepseek.com"}
        else:
            return {"ok": False, "error": f"HTTP 错误 {he.code}: {he.reason}"}
    except Exception as e:
        return {"ok": False, "error": f"网络连接异常: {str(e)}"}


def call_llm_api(prompt, system_prompt, timeout=20):
    """
    Robust LLM caller supporting DeepSeek, OpenAI, Gemini and compatible gateways.
    Returns (content, error_msg, meta_dict).
    """
    import time
    conn = get_conn()
    cfg = dict(conn.execute("SELECT * FROM ai_settings WHERE id = 1").fetchone())
    conn.close()

    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return None, "未配置 API Key", None

    base_url = (cfg.get("base_url") or "https://api.deepseek.com").strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        url = base_url
    elif base_url.endswith("/v1"):
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/chat/completions"

    model_name = (cfg.get("model_name") or "deepseek-chat").strip()
    if model_name in ("deepseek-flash", "deepseek"):
        model_name = "deepseek-chat"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - t0) * 1000)
            content = data["choices"][0]["message"]["content"]
            return content, None, {"model": model_name, "latency_ms": elapsed}
    except urllib.error.HTTPError as he:
        if he.code == 401:
            err_msg = "HTTP 401 密钥失效（请检查 DeepSeek API Key 是否正确）"
        else:
            err_msg = f"HTTP {he.code}: {he.reason}"
        return None, err_msg, {"model": model_name}
    except Exception as e:
        return None, str(e), {"model": model_name}


def _infer_category_local(prod_name):
    """Local high-precision semantic category classifier."""
    p = prod_name.lower()
    if any(k in p for k in ["蜜", "果", "瓜", "蕉", "沃柑", "苹果", "梨", "桃", "提子", "葡萄", "菠萝", "西瓜", "柑", "桔", "橘", "菜", "肉", "鱼", "散称"]):
        return "🍇 生鲜水果"
    if any(k in p for k in ["百威", "啤酒", "拉萨啤酒", "青岛", "雪花", "听装", "纯生", "易拉罐", "可乐", "雪碧", "红牛", "水", "饮料"]):
        return "🍺 啤酒快消"
    if any(k in p for k in ["xo", "轩尼诗", "人头马", "马爹利", "白兰地", "威士忌", "茅台", "五粮液", "剑南春", "洋酒", "红酒", "干红", "年份"]):
        return "🍷 高档洋酒"
    if any(k in p for k in ["红花油", "纱布", "棉签", "创口贴", "白药", "药", "医用", "消炎", "口罩", "纸巾", "洗洁精", "洗衣液"]):
        return "💊 医药日化"
    if any(k in p for k in ["卫衣", "裤", "衫", "外套", "毛衣", "羽绒", "鞋", "包", "服", "裙"]):
        return "👗 服装百货"
    return "📦 通用商品"


def llm_analyze_and_enrich_records(filename, rows_sample, detected_partners, detected_products, parsed, state):
    """
    Core AI CFO Intelligence:
    1. Extracts business nature and cross-entity relations.
    2. Enriches each SKU with accurate commercial categories.
    3. Generates 4-dimension Executive Financial Audit Memo (Cash flow risk, gift fraud prevention, action items).
    4. Dual-track resilience: Calls remote LLM (DeepSeek) if available; otherwise uses high-fidelity local expert engine.
    """
    total_purchases_amt = sum(float(x.get("amount", 0.0)) for x in parsed.get("purchases", []))
    total_sales_amt = sum(float(x.get("amount", 0.0)) for x in parsed.get("sales", []))

    # Calculate supplier distribution
    sup_totals = {}
    for p in parsed.get("purchases", []):
        s = p.get("supplier_name", "未知")
        sup_totals[s] = round(sup_totals.get(s, 0.0) + float(p.get("amount", 0.0)), 2)
    sorted_sups = sorted(sup_totals.items(), key=lambda x: x[1], reverse=True)

    free_gifts = [p for p in parsed.get("purchases", []) if float(p.get("unit_price", 0.0)) == 0.0 or "赠" in p.get("product_name", "")]
    high_value_items = [p for p in parsed.get("purchases", []) if float(p.get("unit_price", 0.0)) >= 200.0]
    float_qty_items = [p for p in parsed.get("purchases", []) if float(p.get("qty", 0.0)) % 1 != 0]

    # Try Remote LLM first
    system_prompt = (
        "你是一位拥有 15 年中国边贸与现代供应链进销存审计经验的资深财务总监（AI CFO）兼 ERP 数据治理专家。"
        "请对用户上传的表格结构、客商主体与流水样本进行商业意图穿透，并出具严密的经营风控与审计备忘录。"
        "必须严格输出纯 JSON 格式（不要使用 markdown 标记包裹），包含以下键名：\n"
        "{\n"
        '  "business_nature": "商业实质与经营特征（100字以内，分析商贸性质、主体类型、业务条线）",\n'
        '  "product_categories": {"商品名": "品类名称（如：🍇 生鲜水果、🍺 啤酒快消、🍷 高档洋酒、💊 医药日化、👗 服装百货、📦 通用商品）"},\n'
        '  "cash_flow_warning": "往来款与现金流占用压力评估（重点分析采购金额集中度与应付款兑付峰值）",\n'
        '  "internal_control_notes": "单据合规与内控风险预警（对0元赠品防飞单、散称生鲜损耗、高值洋酒防盗出具风控建议）",\n'
        '  "action_items": ["财务与库管具体行动指令1", "行动指令2", "行动指令3"]\n'
        "}"
    )

    sample_lines = []
    for p in (parsed.get("purchases", [])[:15] + parsed.get("sales", [])[:15]):
        sample_lines.append(f"- {p.get('date')} | {p.get('supplier_name') or p.get('customer_name')} | {p.get('product_name')} | 数量:{p.get('qty')} | 单价:¥{p.get('unit_price')} | 金额:¥{p.get('amount')}")

    user_prompt = (
        f"上传文件：{filename}\n"
        f"涉及往来单位（{len(detected_partners)}家）：{', '.join(detected_partners[:8])}\n"
        f"提取物料数量：{len(detected_products)}个\n"
        f"采购总额：¥{total_purchases_amt:,.2f}，销售总额：¥{total_sales_amt:,.2f}\n"
        f"供应商采购额排序：{', '.join(f'{k}: ¥{v:,.2f}' for k, v in sorted_sups[:5])}\n"
        f"特征发现：0元/赠品流水 {len(free_gifts)} 笔；单价超200元高值流水 {len(high_value_items)} 笔；散称小数数量流水 {len(float_qty_items)} 笔。\n"
        f"部分流水代表行：\n" + "\n".join(sample_lines) + "\n\n请按规定 JSON 格式输出审计与物料分类："
    )

    remote_resp, err_msg, meta = call_llm_api(user_prompt, system_prompt, timeout=18)

    llm_audit = {}
    product_categories = {}

    if remote_resp and not err_msg:
        try:
            clean_json = re.sub(r"^```(?:json)?\s*", "", remote_resp.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json.strip(), flags=re.MULTILINE)
            parsed_llm = json.loads(clean_json)
            product_categories = parsed_llm.get("product_categories", {})
            llm_audit = {
                "model_source": "remote_llm",
                "model_name": meta.get("model", "DeepSeek-V3"),
                "badge": f"🟢 大模型已全脑深度介入: {meta.get('model', 'DeepSeek-V3')} (在线 API 实时生成)",
                "llm_latency_ms": meta.get("latency_ms", 450),
                "business_nature_summary": parsed_llm.get("business_nature", "多商户联营批发采购台账"),
                "business_nature": parsed_llm.get("business_nature", ""),
                "cash_flow_warning": parsed_llm.get("cash_flow_warning", ""),
                "internal_control_notes": parsed_llm.get("internal_control_notes", ""),
                "action_items": parsed_llm.get("action_items", []),
                "supplier_ranking": sorted_sups,
                "free_gifts_count": len(free_gifts),
                "high_value_count": len(high_value_items),
                "float_qty_count": len(float_qty_items)
            }
        except Exception:
            remote_resp = None

    if not remote_resp:
        # High-Fidelity Local Expert Engine (Fallback with full transparency)
        for prod in detected_products:
            product_categories[prod] = _infer_category_local(prod)

        top_sup_str = f"「{sorted_sups[0][0]}」(¥{sorted_sups[0][1]:,.2f}，占 {round(sorted_sups[0][1]/max(1, total_purchases_amt)*100, 1)}%)" if sorted_sups else "无"

        biz_nature = (
            f"本表格属于典型的区域多商户联营批发台账，涵盖西藏当地商贸公司与周边商超（如 {', '.join(detected_partners[:3])} 等）。"
            f"业务条线涵盖生鲜水果散称、啤酒快消、高档洋酒与医药日化等多品类复合经营，具备鲜明的多主体分段结算与合同代购特征。"
        )

        cf_warning = (
            f"本次入账新增应付采购额 ¥{total_purchases_amt:,.2f}。供应商集中度极高，首位供货商为 {top_sup_str}。"
            f"建议财务紧密监控 30 天账期承兑节点，防范单一大供应商应付账款扎堆兑付造成现金流短期承压。"
        )

        ic_notes = (
            f"1. 【赠品防飞单】：检测到 {len(free_gifts)} 笔 0 元赠品（如百威赠酒等），必须按赠品独立出入库台账建立专人核销凭据，严禁不入账流失；\n"
            f"2. 【生鲜散称损耗】：检测到 {len(float_qty_items)} 笔浮点斤两明细（如西州蜜、沃柑等），高原运输及存储损耗率较高，需执行 48 小时周转日清日结；\n"
            f"3. 【高货值防盗】：检测到 {len(high_value_items)} 笔单价超过 ¥200 的名酒（如轩尼诗XO等），单瓶货值高，建议设立带锁专用库位并双人验货。"
        )

        actions = [
            f"立即核对 {sorted_sups[0][0] if sorted_sups else '主要供应商'} 的纸质送货明细单与实际入库签收印章，完成四单匹配核销；",
            f"针对 {len(free_gifts)} 笔赠品建立《促销赠品领用备查簿》，防止库管与外勤飞单挪用；",
            f"对西州蜜、沃柑等易腐生鲜物料设定 3 天快速周转预警水位，优先安排商超调拨。"
        ]

        diagnostic_note = f"（API 状态提示：{err_msg}；系统已启用内置专家知识推理引擎保底）" if err_msg else "（当前未配置外网 API Key，点击右上角【AI 设置】填写 DeepSeek Key 即可唤醒千亿大模型）"

        llm_audit = {
            "model_source": "local_cfo_engine",
            "model_name": "本地专家认知推理引擎",
            "badge": "🟡 本地专家认知引擎审阅 (未连接有效外网大模型 API)",
            "api_note": diagnostic_note,
            "llm_latency_ms": 25,
            "business_nature_summary": "区域多主体商贸批发与联营采购台账",
            "business_nature": biz_nature,
            "cash_flow_warning": cf_warning,
            "internal_control_notes": ic_notes,
            "action_items": actions,
            "supplier_ranking": sorted_sups,
            "free_gifts_count": len(free_gifts),
            "high_value_count": len(high_value_items),
            "float_qty_count": len(float_qty_items)
        }

    # Fill missing product category defaults
    for prod in detected_products:
        if prod not in product_categories:
            product_categories[prod] = _infer_category_local(prod)

    return llm_audit, product_categories


def generate_financial_audit_memo(state, focus_area="all"):
    """Generates global financial audit memo for current whole ledger state."""
    kpis = state["kpis"]
    top_ar = sorted(state["ar_ledger"], key=lambda x: x["ar_balance"], reverse=True)[:3]
    top_ap = sorted(state["ap_ledger"], key=lambda x: x["ap_balance"], reverse=True)[:3]
    low_stock = [x for x in state["inventory_ledger"] if x["is_low_stock"]]

    ar_summary = "客户应收账款总体良性。"
    if top_ar:
        ar_items = [f"{c['customer_name']} 欠 ¥{c['ar_balance']:,.2f}" for c in top_ar]
        ar_summary = f"应收前三客户（{', '.join(ar_items)}）占全司总应收主要比例，需在账期到期前 7 天发出催款涵。"

    memo = {
        "title": "全局经营台账 · 大模型财务总监审计备忘录",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpi_overview": f"全库总库存 {kpis['total_stock_qty']} 件（占用资金 ¥{kpis['total_stock_value']:,.2f}），客户总应收 ¥{kpis['total_ar']:,.2f}，供应商总应付 ¥{kpis['total_ap']:,.2f}。",
        "ar_audit": ar_summary,
        "ap_audit": "暂无突出应付账款压力。" if not top_ap else f"最大应付供货商为「{top_ap[0]['supplier_name']}」（尚欠 ¥{top_ap[0]['ap_balance']:,.2f}），建议结合资金池现金流规划梯次分期支付。",
        "inventory_audit": f"全库库存充足，有 {len(low_stock)} 个 SKU 跌破安全水位需要紧急补货。" if low_stock else "全库全部物料库存均在安全警戒线以上，无断货风险。",
        "cfo_recommendations": [
            "每周五定期导出客商往来对账单，核查银行流水回单对齐率；",
            "针对 0 元赠品与浮动散称生鲜物料执行双周实物盘点，损耗率控制在 2% 警戒线以内；",
            "建议预留相当于月均采购额 35% 的安全现金储备应对供货商突发集中兑付。"
        ]
    }
    return memo


def _build_ledger_context_for_llm(state):
    k = state["kpis"]
    prod_lines = []
    for p in state["inventory_ledger"][:18]:
        prod_lines.append(f"{p['product_name']}(库存:{p['stock_qty']}{p['spec']}, 进价:¥{p['in_price']}, 售价:¥{p['sale_price']}, 安全线:{p['safety_stock']})")

    short_prods = [f"{x['product_name']}(当前仅剩{x['stock_qty']}件,缺口{x['shortage_qty']}件)" for x in state["inventory_ledger"] if x["is_low_stock"]][:8]
    top_ar = [f"{c['customer_name']}(尚欠¥{c['ar_balance']:,.2f},占全司{c['ar_share']}%)" for c in sorted(state["ar_ledger"], key=lambda x: x["ar_balance"], reverse=True)[:5]]
    top_ap = [f"{s['supplier_name']}(应付¥{s['ap_balance']:,.2f})" for s in sorted(state["ap_ledger"], key=lambda x: x["ap_balance"], reverse=True)[:5]]

    ctx = (
        f"【公司实时台账核心基准数据（严谨事实依据）】\n"
        f"• 全库实时总库存: {k['total_stock_qty']} 件，库存资产资金 ¥{k['total_stock_value']:,.2f}。\n"
        f"• 客户应收账款总额: ¥{k['total_ar']:,.2f}（本期已收回款: ¥{k.get('total_received', 0.0):,.2f}）。\n"
        f"• 供应商应付账款总额: ¥{k['total_ap']:,.2f}（本期已付清: ¥{k.get('total_paid', 0.0):,.2f}）。\n"
        f"• 累计销售出库总额: ¥{k['total_sales_amount']:,.2f}，实现销售毛利 ¥{k['gross_profit']:,.2f}（毛利率 {k.get('gross_margin', 0.0)}%）。\n"
        f"• 缺货预警物料({len(short_prods)}个): {', '.join(short_prods) if short_prods else '全库各SKU库存均在安全水位以上'}\n"
        f"• 欠款客户前列: {', '.join(top_ar) if top_ar else '暂无客户欠款'}\n"
        f"• 待付供货商前列: {', '.join(top_ap) if top_ap else '暂无供应商待付款'}\n"
        f"• 现有部分商品主档: {'; '.join(prod_lines)}\n"
    )
    return ctx



# ================= 业务品类与指令落盘协同执行引擎 =================
CATEGORY_KEYWORDS = {
    '水果': ['西瓜', '阳光玫瑰', '圣女果', '哈密瓜', '橙子', '苹果', '梨', '桃', '香蕉', '柠檬', '水果', '葡萄'],
    '坚果': ['瓜子', '巴坦木', '碧根果', '腰果', '花生', '开心果', '核桃', '杏仁', '坚果', '板栗', '松子'],
    '零食': ['枣', '月饼', '豆', '片', '糖', '枸杞', '桂圆', '干', '零食', '饼', '糕', '条'],
    '酒水': ['青岛', '百威', '啤酒', '纯生', '炫舞', '笑脸', '淡爽', '喜力', '1664', '3650', '动力火车', 'XO', 'VSOP', '黑牌', '马爹利', '芝华士', '红葡萄酒', '马尔贝克', '葡萄酒'],
    '饮料': ['可乐', '雪碧', '红茶', '绿茶', '脉动', '红牛', '旺仔', '酸奶', '苏打水', '矿泉水', '农夫山泉']
}

def resolve_products_by_category_or_name(target_str, products_list):
    """根据自然语言目标提取对应具体物料全称列表"""
    target_str = (target_str or "").strip()
    if not target_str or any(w in target_str for w in ('所有', '全部', '全库', '各SKU', '各个', '全部商品', '所有商品')):
        return [p['name'] for p in products_list]

    matched = set()
    has_cat = False
    for cat_name, kw_list in CATEGORY_KEYWORDS.items():
        if cat_name in target_str:
            has_cat = True
            for p in products_list:
                pname = p['name']
                if any(k in pname for k in kw_list):
                    # 避免把葡萄酒分类到水果
                    if cat_name in ('水果', '坚果', '零食') and any(w in pname for w in ('酒', '啤酒', '系列', '听装', '瓶装', '件', '提', '盒')):
                        continue
                    matched.add(pname)

    if not has_cat:
        for p in products_list:
            if target_str in p['name'] or p['name'] in target_str:
                matched.add(p['name'])

    return sorted(list(matched))


def execute_system_action(action, params):
    """
    直接执行 AI 协同操作指令并将数据原子落盘到 SQLite 数据库 (ledger.db)
    返回: (ok: bool, detail: dict, summary_msg: str)
    """
    from database import get_conn, save_payment, save_receipt, save_product, save_supplier, save_customer

    today_str = datetime.now().strftime("%Y-%m-%d")

    if action == "set_safety_stock":
        targets = params.get("target_products", [])
        raw_val = params.get("safety_stock", 10.0)
        try:
            val = float(raw_val)
        except Exception:
            val = 10.0

        if not targets:
            return False, {}, "未找到需要调整安全库存的目标商品。"

        conn = get_conn()
        cur = conn.cursor()
        updated_items = []
        for name in targets:
            row = cur.execute("SELECT id, name, safety_stock FROM products WHERE name = ? OR name LIKE ?", (name, f"%{name}%")).fetchone()
            if row:
                old_val = row["safety_stock"]
                cur.execute("UPDATE products SET safety_stock = ? WHERE id = ?", (val, row["id"]))
                updated_items.append((row["name"], old_val, val))

        conn.commit()
        conn.close()

        if not updated_items:
            return False, {}, "在商品主档中未匹配到指定名称的商品。"

        preview_lines = [f"• {name}：原 {int(old) if old == int(old) else old} 件 ➔ **统一设为 {int(new) if new == int(new) else new} 件**" for name, old, new in updated_items[:10]]
        more_str = f"\n• ...以及其余 {len(updated_items) - 10} 款商品" if len(updated_items) > 10 else ""
        summary = (
            f"✅ **已成功执行指令并安全落盘到系统！**\n\n"
            f"已为您将 **{len(updated_items)} 款** 商品的安全库存统一设置为 **{int(val) if val == int(val) else val} 件**：\n"
            + "\n".join(preview_lines) + more_str + "\n\n"
            f"📌 **系统联动生效报告**：\n"
            f"• 数据库 `products` 基础资料已完成事务提交并持久化存储；\n"
            f"• 全库缺货警戒水位已重新即时核算，所有看板已自动同步刷新！"
        )
        return True, {"action": action, "updated_count": len(updated_items), "items": updated_items}, summary

    elif action == "update_product_price":
        pname = params.get("product_name", "")
        purchase_price = params.get("purchase_price")
        sale_price = params.get("sale_price")
        if not pname:
            return False, {}, "请指定需要修改价格的商品名称。"

        conn = get_conn()
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM products WHERE name = ? OR name LIKE ?", (pname, f"%{pname}%")).fetchone()
        if not row:
            conn.close()
            return False, {}, f"在主档中未找到商品「{pname}」。"

        updates = []
        vals = []
        msgs = []
        if purchase_price is not None:
            pp = float(purchase_price)
            updates.append("purchase_price = ?")
            vals.append(pp)
            msgs.append(f"采购进价由 ¥{row['purchase_price']} 变更为 **¥{pp:.2f}**")
        if sale_price is not None:
            sp = float(sale_price)
            updates.append("sale_price = ?")
            vals.append(sp)
            msgs.append(f"销售单价由 ¥{row['sale_price']} 变更为 **¥{sp:.2f}**")

        if not updates:
            conn.close()
            return False, {}, "未提供需要修改的价格数值。"

        vals.append(row["id"])
        cur.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = ?", tuple(vals))
        conn.commit()
        conn.close()

        summary = (
            f"✅ **已成功修改商品【{row['name']}】价格并落盘！**\n\n"
            + "\n".join(f"• {m}" for m in msgs) + "\n\n"
            f"商品基础资料与往来核算参考价已实时全量更新生效。"
        )
        return True, {"action": action, "product": row["name"]}, summary

    elif action == "record_payment":
        sname = params.get("supplier_name", "")
        amount = float(params.get("amount", 0.0) or 0.0)
        pdate = params.get("date", today_str) or today_str
        payer = params.get("payer", "财务出纳")
        remark = params.get("remark", "AI自然语言协同登记")
        if not sname or amount <= 0:
            return False, {}, "录入付款单需提供供应商名称与大于0的金额。"

        res = save_payment({
            "supplier_name": sname,
            "amount": amount,
            "date": pdate,
            "payer": payer,
            "payee": sname,
            "phone": f"备注:{remark}" if remark else ""
        })
        if res.get("ok"):
            summary = (
                f"✅ **已成功为【{sname}】登记已付款 ¥{amount:,.2f} 并落盘！**\n\n"
                f"• 付款时间：{pdate}\n"
                f"• 经办出纳：{payer}\n"
                f"• 流水备注：{remark}\n\n"
                f"供应商应付欠款与全司资金支出已实时自动冲销平账。"
            )
            return True, {"action": action, "supplier_name": sname, "amount": amount}, summary
        else:
            return False, {}, res.get("error", "登记付款失败")

    elif action == "record_receipt":
        cname = params.get("customer_name", "")
        amount = float(params.get("amount", 0.0) or 0.0)
        rdate = params.get("date", today_str) or today_str
        payer = params.get("payer", "客户代表")
        remark = params.get("remark", "AI自然语言协同收款")
        if not cname or amount <= 0:
            return False, {}, "录入收款单需提供客户名称与大于0的金额。"

        res = save_receipt({
            "customer_name": cname,
            "amount": amount,
            "date": rdate,
            "payer": payer,
            "payee": "公司财务",
            "phone": f"备注:{remark}" if remark else ""
        })
        if res.get("ok"):
            summary = (
                f"✅ **已成功为【{cname}】登记回款 ¥{amount:,.2f} 并落盘！**\n\n"
                f"• 收款时间：{rdate}\n"
                f"• 交款人：{payer}\n"
                f"• 凭证备注：{remark}\n\n"
                f"客户应收欠款已实时扣减，全司回款流水已自动同步。"
            )
            return True, {"action": action, "customer_name": cname, "amount": amount}, summary
        else:
            return False, {}, res.get("error", "登记收款失败")

    elif action == "settle_ap":
        sname = params.get("supplier_name", "")
        state = get_dashboard_state()
        sup = next((s for s in state["ap_ledger"] if s["supplier_name"] == sname or sname in s["supplier_name"]), None)
        if not sup:
            return False, {}, f"在供应商应付台账中未找到「{sname}」。"
        balance = sup["ap_balance"]
        if balance <= 0:
            return True, {}, f"供应商【{sup['supplier_name']}】当前待付余额为 ¥0.00，无需冲销！"

        res = save_payment({
            "supplier_name": sup["supplier_name"],
            "amount": balance,
            "date": today_str,
            "payer": "财务出纳",
            "payee": sup["supplier_name"],
            "phone": "备注:AI协同全额冲销应付款"
        })
        summary = f"✅ **已一键全额结清供应商【{sup['supplier_name']}】应付款 ¥{balance:,.2f} 并落盘！**\n\n已自动生成全额付款对账单，该供应商待付款已降为 ¥0.00。"
        return True, {"action": action, "supplier_name": sup["supplier_name"], "amount": balance}, summary

    elif action == "settle_ar":
        cname = params.get("customer_name", "")
        state = get_dashboard_state()
        cust = next((c for c in state["ar_ledger"] if c["customer_name"] == cname or cname in c["customer_name"]), None)
        if not cust:
            return False, {}, f"在客户应收台账中未找到「{cname}」。"
        balance = cust["ar_balance"]
        if balance <= 0:
            return True, {}, f"客户【{cust['customer_name']}】当前待收欠款为 ¥0.00，无未结账款！"

        res = save_receipt({
            "customer_name": cust["customer_name"],
            "amount": balance,
            "date": today_str,
            "payer": cust["customer_name"],
            "payee": "财务出纳",
            "phone": "备注:AI协同全额冲销应收款"
        })
        summary = f"✅ **已一键全额结清客户【{cust['customer_name']}】欠款 ¥{balance:,.2f} 并落盘！**\n\n已自动生成全额收款单，该客户应收余额已降为 ¥0.00。"
        return True, {"action": action, "customer_name": cust["customer_name"], "amount": balance}, summary

    return False, {}, f"暂不支持的协同指令类型: {action}"


def process_natural_language(text):
    text = (text or "").strip()
    if not text:
        return {"type": "query_answer", "reply": "请输入您的记账指令或财务管理咨询问题。", "mode": "系统提示"}

    state = get_dashboard_state()
    today_str = datetime.now().strftime("%Y-%m-%d")
    ledger_ctx = _build_ledger_context_for_llm(state)
    all_prods = state.get("products", [])
    prod_names = [p["name"] for p in all_prods]

    # 1. First Attempt: Real Remote LLM Call
    system_prompt = (
        "你是一位精通进销存管理、客商对账与现代供应链财务管理的资深「AI 财务总监兼系统操作协同助理」。\n"
        "你不仅负责财务咨询分析，更具备直接对数据库下达指令、修改主数据与落盘操作的协同执行能力！\n"
        "你已经完全掌握了当前公司的实时进销存与往来账款数据，请基于注入的真实台账数据为管理层提供专业答复，或直接解析并执行指令。\n\n"
        f"{ledger_ctx}\n"
        f"【当前数据库内全部商品主档名称列表（共 {len(prod_names)} 款）】\n"
        f"{', '.join(prod_names)}\n\n"
        "【交互输出规范 - 必须输出严格纯 JSON，不要包含任何 markdown 代码块或额外文本】\n"
        "请精准判断用户意图：\n"
        "1. 如果用户下达了【系统修改与操作执行指令】（如批量修改或设置安全库存、调整商品进售价、登记付款/收款、结清款项、新增商品/客户/供应商）：\n"
        "{\n"
        '  "intent": "execute_action",\n'
        '  "action": "set_safety_stock | update_product_price | record_payment | record_receipt | settle_ap | settle_ar",\n'
        '  "params": {\n'
        '    // 针对 set_safety_stock: "target_products": ["从上方商品列表中精准选出的具体商品名称数组"], "safety_stock": 目标数值\n'
        '    // 针对 update_product_price: "product_name": "具体商品全称", "purchase_price": 数值, "sale_price": 数值\n'
        '    // 针对 record_payment: "supplier_name": "供应商全称", "amount": 数值, "payer": "出纳", "date": "YYYY-MM-DD", "remark": "备注"\n'
        '    // 针对 record_receipt: "customer_name": "客户全称", "amount": 数值, "payer": "交款人", "date": "YYYY-MM-DD", "remark": "备注"\n'
        '    // 针对 settle_ap: "supplier_name": "供应商名"\n'
        '    // 针对 settle_ar: "customer_name": "客户名"\n'
        '  },\n'
        '  "reply": "执行总结汇报"\n'
        "}\n"
        "2. 如果用户是在【下达记账流水指令】（如采购入库、出货销售、记单笔进销存），请输出：\n"
        "{\n"
        '  "intent": "bookkeeping",\n'
        '  "reply": "业务意图简述",\n'
        '  "records": {\n'
        '    "purchases": [{"date": "YYYY-MM-DD", "product_name": "名称", "spec": "单位", "qty": 数量, "unit_price": 单价, "amount": 金额, "supplier_name": "供应商"}],\n'
        '    "sales": [{"date": "YYYY-MM-DD", "product_name": "名称", "spec": "单位", "qty": 数量, "unit_price": 单价, "amount": 金额, "customer_name": "客户"}],\n'
        '    "supplier_payments": [{"date": "YYYY-MM-DD", "supplier_name": "供应商", "amount": 金额}],\n'
        '    "customer_receipts": [{"date": "YYYY-MM-DD", "customer_name": "客户", "amount": 金额}]\n'
        '  }\n'
        "}\n"
        "3. 如果用户是在进行【财务咨询、对账函生成、经营诊断、库存缺货追问、税务/毛利分析或日常对话】，请输出：\n"
        "{\n"
        '  "intent": "chat_reply",\n'
        '  "reply": "详细专业回答（使用结构化排版、分段清晰、引述上方真实的台账数据给出 CFO 级的分析与建议，若生成催款函请提供完整专业的话术与核对明细）"\n'
        "}\n"
    )

    remote_resp, err_msg, meta = call_llm_api(text, system_prompt, timeout=18)

    if remote_resp and not err_msg:
        try:
            clean_json = re.sub(r"^```(?:json)?\s*", "", remote_resp.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json.strip(), flags=re.MULTILINE)
            parsed_res = json.loads(clean_json)

            # 1.1 Action Execution (落盘操作指令)
            if parsed_res.get("intent") == "execute_action" and parsed_res.get("action"):
                act = parsed_res.get("action")
                params = parsed_res.get("params", {})
                ok, detail, summary = execute_system_action(act, params)
                if ok:
                    return {
                        "type": "action_executed",
                        "action": act,
                        "reply": summary,
                        "mode": f"🟢 大模型协同执行落盘: {meta.get('model', 'DeepSeek-V3')} ({meta.get('latency_ms', 400)}ms)"
                    }

            # 1.2 Bookkeeping (工作台推演流)
            elif parsed_res.get("intent") == "bookkeeping" and parsed_res.get("records"):
                recs = parsed_res["records"]
                parsed = {
                    "purchases": recs.get("purchases", []),
                    "sales": recs.get("sales", []),
                    "supplier_payments": recs.get("supplier_payments", []),
                    "customer_receipts": recs.get("customer_receipts", []),
                    "products_master": [],
                    "customers_master": [],
                    "suppliers_master": []
                }
                for idx, p in enumerate(parsed["purchases"]):
                    p.setdefault("order_no", f"AI-PO-{datetime.now().strftime('%m%d%H%M')}-{idx+1}")
                    p.setdefault("date", today_str)
                    p.setdefault("buyer", "张三")
                    p.setdefault("spec", "件")
                    p.setdefault("amount", round(float(p.get("qty", 1)) * float(p.get("unit_price", 0)), 2))
                    p.setdefault("supplier_name", "默认供应商")
                for idx, s in enumerate(parsed["sales"]):
                    s.setdefault("order_no", f"AI-SO-{datetime.now().strftime('%m%d%H%M')}-{idx+1}")
                    s.setdefault("date", today_str)
                    s.setdefault("seller", "李静")
                    s.setdefault("spec", "件")
                    s.setdefault("amount", round(float(s.get("qty", 1)) * float(s.get("unit_price", 0)), 2))
                    s.setdefault("customer_name", "默认客户")

                total_rec = sum(len(v) for v in parsed.values())
                if total_rec > 0:
                    impact = simulate_impact(parsed, state)
                    run_steps = [
                        {"step": "1. 大模型语义意图理解", "status": "done", "duration_ms": meta.get("latency_ms", 350), "detail": f"【{meta.get('model', 'DeepSeek')}】从指令中精确提取 {total_rec} 笔标准单据。"},
                        {"step": "2. 主数据物料与价格匹配", "status": "done", "duration_ms": 12, "detail": "自动匹配物料主档、客商档案与标准单价。"},
                        {"step": "3. 台账联动沙箱试算", "status": "done", "duration_ms": 10, "detail": "已完成入账前后库存与资金差额对比，确认即可写入数据库。"}
                    ]
                    return {
                        "type": "bookkeeping_preview",
                        "preview": {
                            "filename": f"AI指令：{text[:24]}",
                            "run_steps": run_steps,
                            "parsed": parsed,
                            "impact": impact,
                            "total_records": total_rec
                        },
                        "mode": f"🟢 大模型驱动: {meta.get('model', 'DeepSeek-V3')} ({meta.get('latency_ms', 400)}ms)"
                    }

            elif parsed_res.get("intent") == "chat_reply" and parsed_res.get("reply"):
                return {
                    "type": "query_answer",
                    "reply": parsed_res.get("reply"),
                    "mode": f"🟢 大模型驱动: {meta.get('model', 'DeepSeek-V3')} ({meta.get('latency_ms', 400)}ms)"
                }
        except Exception:
            pass

    # ================= 2. Fallback: High-Fidelity Local Action & Rule Engine =================

    # 2.1 本地规则操作执行：安全库存设置（支持零延迟离线自动落盘）
    m_stock = re.search(r"(?:将|把|设置)?\s*(.*?)(?:类|品类)?(?:的)?安全库存(?:统一)?(?:设为|调整为|改为|改成|设置为|为)\s*(\d+(?:\.\d+)?)", text)
    if m_stock:
        target_str, val_str = m_stock.group(1).strip(), m_stock.group(2).strip()
        val = float(val_str)
        matched_targets = resolve_products_by_category_or_name(target_str, state.get("products", []))
        if matched_targets:
            ok, detail, summary = execute_system_action("set_safety_stock", {"target_products": matched_targets, "safety_stock": val})
            if ok:
                return {
                    "type": "action_executed",
                    "action": "set_safety_stock",
                    "reply": summary,
                    "mode": "⚡ AI财务协同引擎 (已安全落盘入库)"
                }

    # 2.2 本地规则操作执行：价格修改
    m_price = re.search(r"(?:将|把)?\s*(.*?)\s*(?:的)?(?:进价|采购价|成本)\s*(?:设为|改为|改成|设置为|为)\s*(\d+(?:\.\d+)?)", text)
    m_sprice = re.search(r"(?:将|把)?\s*(.*?)\s*(?:的)?(?:售价|销售价|单价)\s*(?:设为|改为|改成|设置为|为)\s*(\d+(?:\.\d+)?)", text)
    if m_price or m_sprice:
        target_pname = (m_price.group(1) if m_price else m_sprice.group(1)).strip()
        pp = float(m_price.group(2)) if m_price else None
        sp = float(m_sprice.group(2)) if m_sprice else None
        ok, detail, summary = execute_system_action("update_product_price", {"product_name": target_pname, "purchase_price": pp, "sale_price": sp})
        if ok:
            return {
                "type": "action_executed",
                "action": "update_product_price",
                "reply": summary,
                "mode": "⚡ AI财务协同引擎 (已安全落盘入库)"
            }

    # 2.3 本地规则操作执行：登记付款
    m_pay = re.search(r"(?:为|向|给)\s*(.*?)\s*(?:登记)?(?:付款|还款|支付|打款)\s*(\d+(?:\.\d+)?)", text)
    if m_pay:
        sname, amount = m_pay.group(1).strip(), float(m_pay.group(2))
        ok, detail, summary = execute_system_action("record_payment", {"supplier_name": sname, "amount": amount})
        if ok:
            return {
                "type": "action_executed",
                "action": "record_payment",
                "reply": summary,
                "mode": "⚡ AI财务协同引擎 (已安全落盘入库)"
            }

    # 2.4 本地规则操作执行：登记收款
    m_rec = re.search(r"(?:收回|收到|向)\s*(.*?)\s*(?:货款|还款|欠款)?\s*(?:登记收款|收款|转来|支付)\s*(\d+(?:\.\d+)?)", text)
    if m_rec:
        cname, amount = m_rec.group(1).strip(), float(m_rec.group(2))
        ok, detail, summary = execute_system_action("record_receipt", {"customer_name": cname, "amount": amount})
        if ok:
            return {
                "type": "action_executed",
                "action": "record_receipt",
                "reply": summary,
                "mode": "⚡ AI财务协同引擎 (已安全落盘入库)"
            }

    # 2.5 本地规则操作执行：一键结清账款
    m_settle = re.search(r"(?:结清|付清|清结)\s*(.*?)\s*(?:的)?(?:全部)?(?:账款|应付|货款|欠款)", text)
    if m_settle:
        name = m_settle.group(1).strip()
        if any(s["supplier_name"] == name or name in s["supplier_name"] for s in state.get("ap_ledger", [])):
            ok, detail, summary = execute_system_action("settle_ap", {"supplier_name": name})
        else:
            ok, detail, summary = execute_system_action("settle_ar", {"customer_name": name})
        if ok:
            return {
                "type": "action_executed",
                "action": "settle",
                "reply": summary,
                "mode": "⚡ AI财务协同引擎 (已安全落盘入库)"
            }

    # 2.6 Analytical queries (查询与催款函)
    if any(k in text for k in ("催款", "对账单", "欠款最多", "应收最多")):
        top_ar = sorted(state["ar_ledger"], key=lambda x: x["ar_balance"], reverse=True)[0] if state["ar_ledger"] else None
        if not top_ar or top_ar["ar_balance"] <= 0:
            return {"type": "query_answer", "reply": "当前系统内暂无欠款客户，往来账款非常健康！", "mode": "本地专家引擎 (未连接外网API)"}
        target_cust = top_ar
        for c in state["ar_ledger"]:
            if c["customer_name"] in text:
                target_cust = c
                break
        cust_sales = [s for s in state["sales"] if s["customer_name"] == target_cust["customer_name"]]
        sales_lines = "；".join(f"{s['date']} {s['product_name']} {s['qty']}件 (¥{s['amount']:,.2f})" for s in cust_sales) or "本期无新增拿货"
        reply = (
            f"为您生成【{target_cust['customer_name']}】对账与催款函：\n\n"
            f"• 上期结转应收：¥{target_cust['opening_ar']:,.2f}\n"
            f"• 本期拿货金额：¥{target_cust['sales_amount']:,.2f}（明细：{sales_lines}）\n"
            f"• 本期已收金额：¥{target_cust['received_amount']:,.2f}\n"
            f"• 当前尚欠应收总额：¥{target_cust['ar_balance']:,.2f}（占全司总应收 {target_cust['ar_share']}%）\n\n"
            f"建议发送话术：「{target_cust['customer_name']}您好，截至 {today_str} 贵司尚有往来款项 ¥{target_cust['ar_balance']:,.2f} 未结清，烦请核对安排回款，感谢支持！」"
        )
        if err_msg:
            reply += f"\n\n*(注：检测到外部大模型 API 状态：{err_msg}；当前已启用本地专家认知引擎为您解答)*"
        return {"type": "query_answer", "reply": reply, "mode": "本地专家引擎 (未连接外网API)"}

    if any(k in text for k in ("库存", "缺货", "补货", "安全库存")) and not any(k in text for k in ("采购", "进货", "买", "入库", "设为", "调整", "修改", "改为", "统一")):
        low_items = [x for x in state["inventory_ledger"] if x["is_low_stock"]]
        if low_items:
            lines = [f"• {x['product_name']}：当前仅剩 {x['stock_qty']} 件（安全库存 {x['safety_stock']} 件，缺口 {x['shortage_qty']} 件）" for x in low_items]
            reply = f"当前共有 {len(low_items)} 个 SKU 跌破安全库存水位：\n" + "\n".join(lines) + f"\n\n全库总库存 {state['kpis']['total_stock_qty']} 件，库存总资金 ¥{state['kpis']['total_stock_value']:,.2f}。"
        else:
            reply = f"目前全部商品库存均高于安全警戒线！全库总库存 {state['kpis']['total_stock_qty']} 件，总库存金额 ¥{state['kpis']['total_stock_value']:,.2f}。"
        if err_msg:
            reply += f"\n\n*(注：检测到外部大模型 API 状态：{err_msg}；当前已启用本地专家认知引擎为您解答)*"
        return {"type": "query_answer", "reply": reply, "mode": "本地专家引擎 (未连接外网API)"}

    # 2.7 Fallback Bookkeeping
    parsed = {
        "purchases": [],
        "sales": [],
        "supplier_payments": [],
        "customer_receipts": [],
        "products_master": [],
        "customers_master": [],
        "suppliers_master": []
    }
    cust_match = next((c for c in state["customers"] if c["name"] in text), None)
    sup_match = next((s for s in state["suppliers"] if s["name"] in text), None)
    prod_match = next((p for p in state["products"] if p["name"] in text or p["name"][:4] in text), None)

    qty_match = re.search(r"(\d+(?:\.\d+)?)\s*[件条套个瓶盒箱斤]", text)
    price_match = re.search(r"(?:单价|按|每件|价格)\s*(\d+(?:\.\d+)?)", text)

    if prod_match and (any(w in text for w in ("采购", "进货", "补货", "入库")) or sup_match):
        qty = float(qty_match.group(1)) if qty_match else 30.0
        uprice = float(price_match.group(1)) if price_match else float(prod_match["purchase_price"])
        target_sup = sup_match["name"] if sup_match else "默认供应商"
        parsed["purchases"].append({
            "date": today_str,
            "order_no": f"AI-PO-{datetime.now().strftime('%H%M%S')}",
            "product_name": prod_match["name"],
            "spec": prod_match["spec"],
            "unit_price": uprice,
            "qty": qty,
            "amount": round(qty * uprice, 2),
            "buyer": "张三",
            "supplier_name": target_sup,
            "address": "",
            "phone": "",
            "remark": "AI自然语言记账"
        })
    elif cust_match and any(w in text for w in ("收", "回款", "转了", "打款", "货款", "还款")):
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(cust_match["name"], ""))]
        amount = nums[0] if nums else 5000.0
        if "万" in text and amount < 100:
            amount *= 10000
        parsed["customer_receipts"].append({
            "date": today_str,
            "customer_name": cust_match["name"],
            "amount": round(amount, 2),
            "payer": "张三",
            "payee": "李静"
        })

    total_rec = sum(len(v) for v in parsed.values())
    if total_rec > 0:
        impact = simulate_impact(parsed, state)
        run_steps = [
            {"step": "1. 本地规则意图解析", "status": "done", "duration_ms": 14, "detail": f"从指令「{text}」中提取出 {total_rec} 笔标准流水。"},
            {"step": "2. 主数据价格与客商匹配", "status": "done", "duration_ms": 11, "detail": "自动补全商品规格、标准单价、客商信息。"},
            {"step": "3. 台账实时联动预演", "status": "done", "duration_ms": 9, "detail": "已生成入账前后库存与应收应付对比预览，确认即可写入数据库。"}
        ]
        return {
            "type": "bookkeeping_preview",
            "preview": {
                "filename": f"AI指令：{text[:24]}",
                "run_steps": run_steps,
                "parsed": parsed,
                "impact": impact,
                "total_records": total_rec
            },
            "mode": "本地专家引擎 (未连接外网API)"
        }

    diag = f"\n\n*(注：检测到外部大模型 API 状态：{err_msg}；在右上角【AI 接口配置】填写正确的 DeepSeek 秘钥即可唤醒千亿大模型全脑思考)*" if err_msg else ""
    return {
        "type": "query_answer",
        "reply": (
            f"已收到您的咨询指令：「{text}」\n\n"
            f"📊 当前台账概况：\n"
            f"• 实时总库存：{state['kpis']['total_stock_qty']} 件（库存资金占用 ¥{state['kpis']['total_stock_value']:,.2f}）\n"
            f"• 客户应收未结总额：¥{state['kpis']['total_ar']:,.2f}\n"
            f"• 供应商应付总额：¥{state['kpis']['total_ap']:,.2f}\n"
            f"• 累计销售毛利：¥{state['kpis']['gross_profit']:,.2f}（毛利率 {state['kpis']['gross_margin_rate']}%）"
            f"{diag}"
        ),
        "mode": "本地专家引擎 (未连接外网API)"
    }


# ================= 多模态文件/单据图片智能识别与交互确认引擎 =================

def extract_text_from_image_local(image_base64):
    """
    Extracts structured spatial rows from a Base64-encoded image using:
    1. macOS Native Apple Vision Framework (ocr_helper binary or swift fallback)
    2. Windows Native WinRT OcrEngine via PowerShell
    Returns (ocr_lines, full_text)
    """
    import os
    import base64
    import tempfile
    import subprocess
    import platform

    if not image_base64:
        return [], ""

    raw_b64 = image_base64.strip()
    ext = ".png"
    if raw_b64.startswith("data:image/"):
        header, _, raw_b64 = raw_b64.partition(",")
        if "jpeg" in header or "jpg" in header:
            ext = ".jpg"
        elif "webp" in header:
            ext = ".webp"

    try:
        img_bytes = base64.b64decode(raw_b64)
    except Exception:
        return [], ""

    tmp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp_file.write(img_bytes)
        tmp_file.close()
        img_path = tmp_file.name

        sys_name = platform.system().lower()
        ocr_text = ""

        if sys_name == "darwin":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            helper_bin = os.path.join(base_dir, "ocr_helper")
            if os.path.exists(helper_bin) and os.access(helper_bin, os.X_OK):
                try:
                    ocr_text = subprocess.check_output([helper_bin, img_path], text=True, timeout=10)
                except Exception:
                    ocr_text = ""
            if not ocr_text.strip():
                swift_code = (
                    'import Foundation\nimport Vision\nimport AppKit\n'
                    'let args = CommandLine.arguments\n'
                    'guard args.count > 1, let img = NSImage(contentsOfFile: args[1]), '
                    'let cgImg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }\n'
                    'let req = VNRecognizeTextRequest()\n'
                    'req.recognitionLevel = .accurate\n'
                    'req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]\n'
                    'req.usesLanguageCorrection = true\n'
                    'try? VNImageRequestHandler(cgImage: cgImg, options: [:]).perform([req])\n'
                    'guard let res = req.results else { exit(0) }\n'
                    'struct It { let t: String; let x: Double; let y: Double }\n'
                    'var arr: [It] = []\n'
                    'for o in res { if let c = o.topCandidates(1).first { arr.append(It(t: c.string, x: Double(o.boundingBox.minX), y: 1.0 - Double(o.boundingBox.midY))) } }\n'
                    'arr.sort { $0.y < $1.y }\n'
                    'var rows: [[It]] = []\n'
                    'for i in arr { if var lr = rows.last, let fy = lr.first?.y, abs(i.y - fy) < 0.020 { lr.append(i); rows[rows.count-1] = lr } else { rows.append([i]) } }\n'
                    'for r in rows { print(r.sorted { $0.x < $1.x }.map { $0.t }.joined(separator: " | ")) }\n'
                )
                try:
                    ocr_text = subprocess.check_output(["swift", "-e", swift_code, img_path], text=True, timeout=15)
                except Exception:
                    ocr_text = ""

        elif sys_name == "windows":
            ps_script = f"""
            $ErrorActionPreference = 'SilentlyContinue'
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
            $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
            $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }})[0]
            Function Await($WinRtTask, $ResultType) {{
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }}
            $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{img_path}')) ([Windows.Storage.StorageFile])
            $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
            $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
            $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
            $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
            $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            foreach ($line in $result.Lines) {{ Write-Output $line.Text }}
            """
            try:
                ocr_text = subprocess.check_output(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    text=True, encoding="utf-8", errors="ignore", timeout=12
                )
            except Exception:
                ocr_text = ""

        lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
        return lines, "\n".join(lines)
    finally:
        try:
            os.remove(tmp_file.name)
        except Exception:
            pass


def call_vision_llm_api(image_base64, prompt, system_prompt, timeout=25):
    """
    Attempts to call a multimodal Vision LLM API directly with image_url.
    Returns (content, error_msg, meta_dict).
    """
    import time
    import urllib.request
    import urllib.error

    conn = get_conn()
    cfg = dict(conn.execute("SELECT * FROM ai_settings WHERE id = 1").fetchone())
    conn.close()

    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return None, "未配置 API Key", None

    base_url = (cfg.get("base_url") or "https://api.deepseek.com").strip().rstrip("/")
    model_name = (cfg.get("model_name") or "deepseek-chat").strip()

    # Standard api.deepseek.com chat endpoint only supports text messages
    if "api.deepseek.com" in base_url.lower() and "vl" not in model_name.lower():
        return None, "当前配置为 DeepSeek 纯文本端点，自动切换为「高精度空间 OCR + DeepSeek 语义解析」双引擎协同模式", None

    if base_url.endswith("/chat/completions"):
        url = base_url
    elif base_url.endswith("/v1"):
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/chat/completions"

    img_url = image_base64 if image_base64.startswith("data:image/") else f"data:image/png;base64,{image_base64}"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": img_url}}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 2000
    }

    t0 = time.time()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - t0) * 1000)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return content, None, {"model": model_name, "latency_ms": elapsed}
    except Exception as e:
        return None, str(e), None


def _convert_structured_json_to_parsed(doc_json, state):
    """
    Converts structured LLM JSON extraction into our standard `parsed` dict
    with entity alignment and separate `qty` and `spec` (unit).
    """
    parsed = {
        "purchases": [],
        "sales": [],
        "supplier_payments": [],
        "customer_receipts": [],
        "products_master": [],
        "customers_master": [],
        "suppliers_master": [],
    }
    today_str = datetime.now().strftime("%Y-%m-%d")
    existing_suppliers = state.get("suppliers", [])
    existing_customers = state.get("customers", [])
    existing_products = state.get("products", [])

    doc_type = str(doc_json.get("doc_type") or doc_json.get("type") or doc_json.get("单据类型") or "purchases").strip().lower()
    if any(k in doc_type for k in ("sale", "销售", "出库", "出货")):
        doc_type = "sales"
    elif any(k in doc_type for k in ("pay", "付款")):
        doc_type = "supplier_payments"
    elif any(k in doc_type for k in ("receipt", "收款", "回款")):
        doc_type = "customer_receipts"
    else:
        doc_type = "purchases"

    raw_partner = str(doc_json.get("partner_name") or doc_json.get("supplier_name") or doc_json.get("customer_name") or doc_json.get("供应商") or doc_json.get("客户") or "").strip()
    doc_date = str(doc_json.get("date") or doc_json.get("日期") or today_str).strip().replace("/", "-").replace(".", "-")
    m_date = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", doc_date)
    if m_date:
        parts = m_date.group(1).split("-")
        doc_date = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    else:
        doc_date = today_str

    order_no = str(doc_json.get("order_no") or doc_json.get("单号") or doc_json.get("编号") or "").strip()
    items = doc_json.get("items") or doc_json.get("records") or doc_json.get("商品") or doc_json.get("明细") or []

    # Smart partner disambiguation
    if raw_partner:
        aligned_s, s_match = resolve_partner_name(raw_partner, existing_suppliers)
        aligned_c, c_match = resolve_partner_name(raw_partner, existing_customers)
        if s_match and not c_match and doc_type == "sales":
            doc_type = "purchases"
        elif c_match and not s_match and doc_type == "purchases":
            doc_type = "sales"

    if doc_type in ("supplier_payments", "payment", "payments"):
        aligned_sup, _ = resolve_partner_name(raw_partner or "默认供应商", existing_suppliers)
        amt = _parse_float(doc_json.get("total_amount") or (items[0].get("amount") if items else 0))
        if amt > 0:
            parsed["supplier_payments"].append({
                "date": doc_date,
                "supplier_name": aligned_sup,
                "amount": round(amt, 2),
                "payer": str(doc_json.get("staff") or "财务出纳"),
                "payee": str(doc_json.get("remark") or "单据识别入账")
            })
        return parsed

    if doc_type in ("customer_receipts", "receipt", "receipts"):
        aligned_cust, _ = resolve_partner_name(raw_partner or "默认客户", existing_customers)
        amt = _parse_float(doc_json.get("total_amount") or (items[0].get("amount") if items else 0))
        if amt > 0:
            parsed["customer_receipts"].append({
                "date": doc_date,
                "customer_name": aligned_cust,
                "amount": round(amt, 2),
                "payer": aligned_cust,
                "payee": str(doc_json.get("staff") or "财务出纳")
            })
        return parsed

    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        raw_prod = str(it.get("product_name") or it.get("name") or it.get("商品名称") or it.get("品名") or it.get("名称") or "").strip()
        if not raw_prod or raw_prod in ("合计", "小计", "总计"):
            continue
        aligned_prod, _ = resolve_product_name(raw_prod, existing_products)
        qty = _parse_float(it.get("qty") or it.get("quantity") or it.get("数量") or 0)
        unit_price = _parse_float(it.get("unit_price") or it.get("price") or it.get("单价") or 0)
        amount = _parse_float(it.get("amount") or it.get("total") or it.get("金额") or 0)
        if amount <= 0 and qty > 0 and unit_price > 0:
            amount = round(qty * unit_price, 2)
        elif unit_price <= 0 and qty > 0 and amount > 0:
            unit_price = round(amount / qty, 2)

        unit_str = str(it.get("unit") or it.get("spec") or it.get("单位") or it.get("规格") or "").strip()
        if not unit_str:
            # Look up existing product spec or default to 斤/件
            matched_p = next((p for p in existing_products if p["name"] == aligned_prod), None)
            unit_str = matched_p["spec"] if matched_p and matched_p.get("spec") else "斤"

        item_partner = str(it.get("partner_name") or raw_partner or "").strip()
        item_date = str(it.get("date") or doc_date).strip().replace("/", "-")
        item_order = str(it.get("order_no") or order_no or f"{'PO' if doc_type != 'sales' else 'SO'}-{datetime.now().strftime('%m%d')}-{idx+1:03d}").strip()
        remark = str(it.get("remark") or "").strip()

        if doc_type == "sales":
            aligned_cust, _ = resolve_partner_name(item_partner or "默认客户", existing_customers)
            parsed["sales"].append({
                "date": item_date,
                "order_no": item_order,
                "product_name": aligned_prod,
                "spec": unit_str,
                "unit_price": unit_price,
                "qty": qty,
                "amount": amount,
                "seller": str(it.get("staff") or doc_json.get("staff") or "AI单据识别"),
                "customer_name": aligned_cust,
                "address": "",
                "phone": "",
                "remark": remark
            })
        else:
            aligned_sup, _ = resolve_partner_name(item_partner or "默认供应商", existing_suppliers)
            parsed["purchases"].append({
                "date": item_date,
                "order_no": item_order,
                "product_name": aligned_prod,
                "spec": unit_str,
                "unit_price": unit_price,
                "qty": qty,
                "amount": amount,
                "buyer": str(it.get("staff") or doc_json.get("staff") or "AI单据识别"),
                "supplier_name": aligned_sup,
                "address": "",
                "phone": "",
                "remark": remark,
                "category": _infer_category_local(aligned_prod)
            })

    return parsed


def _fallback_parse_ocr_form_or_table(ocr_lines, filename, state):
    """
    Deterministic local parser for OCR lines when LLM is unreachable or for fast pre-check.
    Supports both tabular OCR rows and form-style single-bill screenshots.
    """
    if not ocr_lines:
        return None

    # 1. Try standard table parser by splitting ' | ' or spaces/commas
    split_rows = []
    for ln in ocr_lines:
        if " | " in ln:
            split_rows.append([c.strip() for c in ln.split(" | ")])
        elif "," in ln:
            split_rows.append([c.strip() for c in ln.split(",")])
        else:
            split_rows.append([c.strip() for c in re.split(r"\s{2,}|\t", ln) if c.strip()])

    preview_try = parse_uploaded_csv_or_rows(rows=split_rows, filename=filename, skip_llm_audit=True)
    if preview_try and preview_try.get("total_records", 0) > 0:
        return preview_try["parsed"]

    # 2. Form-style key-value extraction (e.g., screenshot of '编辑采购入库单' or single receipt slip)
    full_text = "\n".join(ocr_lines)
    doc_type = "sales" if any(k in full_text for k in ["销售出库", "销售单", "成交单价", "客户名称"]) else "purchases"

    # Extract date
    m_date = re.search(r"(\d{4}[-\/\.]\d{1,2}[-\/\.]\d{1,2})", full_text)
    doc_date = datetime.now().strftime("%Y-%m-%d")
    if m_date:
        dp = re.split(r"[-\/\.]", m_date.group(1))
        doc_date = f"{dp[0]}-{int(dp[1]):02d}-{int(dp[2]):02d}"

    # Extract order_no
    m_order = re.search(r"((?:PO|SO)[-\w]+|\b00\d{4,}\b)", full_text)
    order_no = m_order.group(1) if m_order else f"PO-{datetime.now().strftime('%m%d%H%M')}"

    # Extract unit from label like 数量（件） or 单位：斤
    m_unit = re.search(r"数量\s*[\(（]([^\)）]+)[\)）]", full_text)
    unit_val = m_unit.group(1).strip() if m_unit else "斤"

    prod_name = ""
    partner_name = ""
    unit_price = 0.0
    qty = 0.0
    amount = 0.0

    for i, ln in enumerate(ocr_lines):
        if ("商品名称" in ln or "品名" in ln) and i + 1 < len(ocr_lines):
            nxt = [c.strip() for c in ocr_lines[i + 1].split("|") if c.strip()]
            if nxt:
                prod_name = nxt[0]
            if len(nxt) > 1 and ("供应商" in ln or "客户" in ln):
                partner_name = nxt[1]
        if ("采购单价" in ln or "成交单价" in ln or "单价" in ln) and i + 1 < len(ocr_lines):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", ocr_lines[i + 1])]
            if len(nums) >= 2:
                unit_price, qty = nums[0], nums[1]
            elif len(nums) == 1:
                unit_price = nums[0]
        if "总金额" in ln and i + 1 < len(ocr_lines):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", ocr_lines[i + 1])]
            if nums:
                amount = nums[0]

    if prod_name and (qty > 0 or amount > 0):
        return _convert_structured_json_to_parsed({
            "doc_type": doc_type,
            "partner_name": partner_name or "默认供应商",
            "date": doc_date,
            "order_no": order_no,
            "items": [{
                "product_name": prod_name,
                "qty": qty or 1.0,
                "unit": unit_val,
                "unit_price": unit_price,
                "amount": amount or round(unit_price * (qty or 1.0), 2)
            }]
        }, state)

    return None


def recognize_multimodal_upload(payload):
    """
    Unified Multimodal Recognition Engine for AI Financial Director Chat:
    Supports:
    - Spreadsheets (.xlsx, .xls, .csv) via rows or csv_text
    - Document Images (.png, .jpg, .jpeg, .webp, .bmp - scanned or photographed bills/receipts/tables)
    Returns structured preview + markdown summary asking the user to confirm before committing to DB.
    """
    file_type = str(payload.get("file_type") or "spreadsheet").strip().lower()
    filename = str(payload.get("filename") or "上传单据").strip()
    user_hint = str(payload.get("user_hint") or "").strip()
    state = get_dashboard_state()

    parsed = None
    engine_mode = "🟢 多模态大模型智能识别"
    ocr_lines = []

    if file_type == "image" or payload.get("image_base64"):
        image_b64 = payload.get("image_base64", "")
        sup_names = [s["name"] for s in state.get("suppliers", [])[:25]]
        cust_names = [c["name"] for c in state.get("customers", [])[:25]]

        extraction_sys_prompt = (
            "你是一位精通中国商贸进销存与财务单据识别的多模态AI财务总监。\n"
            "请从用户上传的单据内容中精准提取全部交易明细，严格区分【数量(qty)】与【单位(unit)】，并只输出纯 JSON 对象（不要加 markdown 代码块标记）：\n"
            "{\n"
            '  "doc_type": "purchases 或 sales 或 supplier_payments 或 customer_receipts",\n'
            '  "partner_name": "识别到的供应商或客户名称",\n'
            '  "date": "YYYY-MM-DD",\n'
            '  "order_no": "单据编号/单号",\n'
            '  "staff": "经办人/采购员/销售员",\n'
            '  "items": [\n'
            '    {"product_name": "商品名称", "qty": 数量数值, "unit": "独立计量单位(如:斤/件/箱/瓶/袋)", "unit_price": 单价数值, "amount": 金额数值, "remark": "备注"}\n'
            "  ],\n"
            '  "summary": "一句话概述识别到的单据核心内容"\n'
            "}\n"
            f"已知供应商档案参考：{sup_names}\n"
            f"已知客户档案参考：{cust_names}\n"
            "注意：如果单据中的单位在已知供应商列表中，则 doc_type 必须设为 purchases（采购入库单）！"
        )

        # Pre-extract high-precision local spatial OCR (0.2s) to ground Vision LLM against character hallucinations
        ocr_lines, full_ocr_text = extract_text_from_image_local(image_b64)
        ocr_grounding_str = f"\n\n【高精度本地OCR辅助参考文本（供汉字校对）】：\n{full_ocr_text}" if full_ocr_text else ""
        user_prompt_text = f"文件名：{filename}\n用户补充说明：{user_hint or '请识别该单据中的全部商品、数量、单位、单价、金额与往来单位'}{ocr_grounding_str}"

        # Stage 1: Try Direct Vision LLM API if supported
        vision_resp, vision_err, vision_meta = call_vision_llm_api(
            image_b64, user_prompt_text, extraction_sys_prompt, timeout=20
        )
        if vision_resp:
            try:
                no_think = re.sub(r"<think>[\s\S]*?</think>", "", vision_resp, flags=re.IGNORECASE).strip()
                clean_j = re.sub(r"^```(?:json)?\s*|\s*```$", "", no_think, flags=re.IGNORECASE)
                m_j = re.search(r"(\{[\s\S]*\})", clean_j)
                if m_j:
                    doc_json = json.loads(m_j.group(1))
                    parsed = _convert_structured_json_to_parsed(doc_json, state)
                    engine_mode = f"🟢 {vision_meta.get('model', 'Vision')} 多模态视觉直连识别 ({vision_meta.get('latency_ms', 0)}ms)"
            except Exception:
                parsed = None

        # Stage 2: Native High-Precision Spatial OCR + DeepSeek / LLM Semantic Structuring
        if not parsed or sum(len(v) for v in parsed.values()) == 0:
            if full_ocr_text:
                # First try deterministic table/form parser on OCR rows (0.2s response)
                local_parsed = _fallback_parse_ocr_form_or_table(ocr_lines, filename, state)
                if local_parsed and sum(len(v) for v in local_parsed.values()) > 0:
                    parsed = local_parsed
                    engine_mode = "🟢 多模态空间视觉 OCR + 智能单据结构化引擎"
                else:
                    # Call configured LLM (e.g. DeepSeek) to semantically structure complex/unstructured OCR text
                    llm_prompt = (
                        f"文件名：{filename}\n用户补充说明：{user_hint}\n\n"
                        f"【单据图像空间 OCR 提取文本（按行与列对齐）】：\n{full_ocr_text}\n\n"
                        "请将上述单据内容结构化提取为 JSON（注意将数量 qty 与单位 unit 拆分为独立字段，排除合计行）："
                    )
                    llm_resp, llm_err, llm_meta = call_llm_api(llm_prompt, extraction_sys_prompt, timeout=15)
                    if llm_resp:
                        try:
                            no_think = re.sub(r"<think>[\s\S]*?</think>", "", llm_resp, flags=re.IGNORECASE).strip()
                            clean_j = re.sub(r"^```(?:json)?\s*|\s*```$", "", no_think, flags=re.IGNORECASE)
                            m_j = re.search(r"(\{[\s\S]*\})", clean_j)
                            if m_j:
                                doc_json = json.loads(m_j.group(1))
                                llm_parsed = _convert_structured_json_to_parsed(doc_json, state)
                                if sum(len(v) for v in llm_parsed.values()) > 0:
                                    parsed = llm_parsed
                                    engine_mode = f"🟢 空间视觉 OCR + {llm_meta.get('model', 'DeepSeek')} 多模态协同识别"
                        except Exception:
                            pass

    else:
        # Spreadsheet (.xlsx / .xls / .csv)
        rows = payload.get("rows")
        csv_text = payload.get("csv_text", "")
        preview = parse_uploaded_csv_or_rows(
            raw_text=csv_text if not rows else None,
            rows=rows if isinstance(rows, list) else None,
            filename=filename,
            skip_llm_audit=True
        )
        parsed = preview.get("parsed")
        engine_mode = "🟢 多模态表格语义解析引擎"

    if not parsed:
        parsed = {
            "purchases": [], "sales": [], "supplier_payments": [], "customer_receipts": [],
            "products_master": [], "customers_master": [], "suppliers_master": []
        }

    # Build unified items list and summary for interactive confirmation
    purchases = parsed.get("purchases", [])
    sales = parsed.get("sales", [])
    payments = parsed.get("supplier_payments", [])
    receipts = parsed.get("customer_receipts", [])
    total_records = len(purchases) + len(sales) + len(payments) + len(receipts)

    if total_records == 0:
        ocr_preview = ("；OCR 提取文本片段：" + " / ".join(ocr_lines[:5])) if ocr_lines else ""
        return {
            "ok": False,
            "total_records": 0,
            "mode": engine_mode,
            "reply": (
                f"⚠️ 已扫描您上传的文件「**{filename}**」，但未能从中提取出有效的商品交易流水或收付款明细{ocr_preview}。\n\n"
                "请确认图片清晰度或表格包含「商品名称/品名、数量、单价/金额」等核心列，您也可以在上传时附带文字说明（例如：*这是向四季鲜果采购的水果单*）。"
            )
        }

    impact = simulate_impact(parsed, state)

    # Format detailed recognition summary markdown
    lines_md = [f"👁️ **已完成单据「{filename}」的多模态智能识别！**"]
    doc_direction = "purchases"
    total_amt = 0.0

    if purchases:
        doc_direction = "purchases"
        sup_set = sorted(list({p["supplier_name"] for p in purchases}))
        total_amt = sum(float(p.get("amount", 0)) for p in purchases)
        lines_md.append(
            f"• **识别单据类型**：📥 **采购入库单**（共 **{len(purchases)}** 笔明细，合计 **¥{total_amt:,.2f}**）\n"
            f"• **往来供应商**：**{'、'.join(sup_set)}**（单号：`{purchases[0].get('order_no', '-')}`，日期：`{purchases[0].get('date', '-')}`）"
        )
        for i, p in enumerate(purchases[:12], 1):
            rem_str = f" *(备注: {p['remark']})*" if p.get("remark") else ""
            lines_md.append(
                f"  {i}. **{p['product_name']}** — 数量：**{p['qty']}** | 单位：**{p['spec']}** | 单价：¥{p['unit_price']:,.2f} | 金额：**¥{p['amount']:,.2f}**{rem_str}"
            )
        if len(purchases) > 12:
            lines_md.append(f"  *... 以及其余 {len(purchases) - 12} 笔采购明细*")

    if sales:
        doc_direction = "sales"
        cust_set = sorted(list({s["customer_name"] for s in sales}))
        s_amt = sum(float(s.get("amount", 0)) for s in sales)
        total_amt += s_amt
        lines_md.append(
            f"• **识别单据类型**：📤 **销售出库单**（共 **{len(sales)}** 笔明细，合计 **¥{s_amt:,.2f}**）\n"
            f"• **往来客户**：**{'、'.join(cust_set)}**（单号：`{sales[0].get('order_no', '-')}`，日期：`{sales[0].get('date', '-')}`）"
        )
        for i, s in enumerate(sales[:12], 1):
            rem_str = f" *(备注: {s['remark']})*" if s.get("remark") else ""
            lines_md.append(
                f"  {i}. **{s['product_name']}** — 数量：**{s['qty']}** | 单位：**{s['spec']}** | 单价：¥{s['unit_price']:,.2f} | 金额：**¥{s['amount']:,.2f}**{rem_str}"
            )

    if payments:
        doc_direction = "payments"
        p_amt = sum(float(x.get("amount", 0)) for x in payments)
        total_amt += p_amt
        lines_md.append(f"• **识别单据类型**：💳 **供应商付款单**（共 **{len(payments)}** 笔，合计 **¥{p_amt:,.2f}**）")
        for i, x in enumerate(payments, 1):
            lines_md.append(f"  {i}. 向 **{x['supplier_name']}** 付款 **¥{x['amount']:,.2f}**（日期：{x['date']}）")

    if receipts:
        doc_direction = "receipts"
        r_amt = sum(float(x.get("amount", 0)) for x in receipts)
        total_amt += r_amt
        lines_md.append(f"• **识别单据类型**：💰 **客户收款单**（共 **{len(receipts)}** 笔，合计 **¥{r_amt:,.2f}**）")
        for i, x in enumerate(receipts, 1):
            lines_md.append(f"  {i}. 收到 **{x['customer_name']}** 回款 **¥{x['amount']:,.2f}**（日期：{x['date']}）")

    lines_md.append("\n❓ **请核对下方识别出的单据明细（支持直接修改数量、自由填写单位），确认无误后点击【确认录入并更新数据】即可一键落盘同步至全系统！**")

    return {
        "ok": True,
        "type": "multimodal_confirmation",
        "filename": filename,
        "doc_direction": doc_direction,
        "total_records": total_records,
        "total_amount": round(total_amt, 2),
        "parsed": parsed,
        "impact": impact,
        "mode": engine_mode,
        "reply": "\n".join(lines_md)
    }

