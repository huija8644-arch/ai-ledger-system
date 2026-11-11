import os
import sys

# 必须在任何本系统业务模块导入之前，将程序根目录加入 sys.path 并切换工作目录
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
try:
    os.chdir(BASE_DIR)
except Exception:
    pass

import json
import webbrowser
import threading
import urllib.parse
import socket
import subprocess
import shutil
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from database import (
    init_db, get_dashboard_state, get_conn,
    reset_to_sample, reset_to_empty, clear_transactions_only,
    save_product, delete_product,
    save_customer, delete_customer,
    save_supplier, delete_supplier,
    save_purchase, delete_purchase,
    save_sale, delete_sale,
    save_payment, delete_payment,
    save_receipt, delete_receipt
)
from ai_engine import (
    parse_uploaded_csv_or_rows,
    commit_parsed_data,
    rollback_batch,
    delete_batch,
    clear_rolled_back_batches,
    process_natural_language,
    test_llm_connectivity,
    generate_financial_audit_memo,
    recognize_multimodal_upload
)


SAMPLE_SCENARIOS = {
    "restock_and_sales": {
        "filename": "2024-11下旬_紧急补货与新销售单(异构表头测试).csv",
        "description": "测试 AI 异构表头识别（使用“货品名称/进货量/供货商”等非标列名 + 简称“轻便系列运动衣 黑”），补货黑色运动衣 50 件解除缺货预警，并新增 2 笔销售与 1 笔客户3大额回款。",
        "csv_text": """发生日期,进货单号,货品名称,单位,进价,进货量,总金额,买手,供货商,联系地址,电话,备注
2024-11-22,A2020004,轻便系列运动衣 黑,件,76.92,50,3846.0,王三,公司2,郑州市金水区,18436***004,紧急补货解除预警
2024-11-22,A2020004,四季休闲服-黑色,件,256.61,15,3849.15,张珊,公司1,北京市房山区,13467***956,冬季备货
单据日期,出货单号,商品名称,计量单位,成交单价,出货量,总价,业务员,收货客户,收货地址,手机号
2024-11-23,A2020004,四季休闲服 紫色,件,401,18,7218.0,陈士园,客户4,湖北省武汉市,17777***156
2024-11-23,A2020005,轻便系列运动衣 蓝色,件,135,20,2700.0,杨澜月,客户1,北京市朝阳区,13047***202
记账日期,客户,联系地址,手机号,收款金额,转款人,出纳
2024-11-24,客户3,北京市丰台区,15027***013,15000,张三,李静
记账日期,供应商,联系地址,手机号,付款金额,打款人,出纳
2024-11-24,公司2,郑州市金水区,18436***004,3000,张三,李静
"""
    },
    "new_sku_and_settlement": {
        "filename": "2024-11月底_新品入库与往来集中结算单.csv",
        "description": "测试新增 SKU（四季休闲服 藏青色）自动建档入库、老客户集中回款核销应收账款。",
        "csv_text": """日期,采购单号,产品名称,规格,单价,数量,金额,采购员,供应商名称,地址,联系电话,备注
2024-11-26,A2020005,四季休闲服 藏青色,件,260.00,40,10400.0,张珊,公司3,天津市滨海新区,13695***288,新品首单入库
日期,销售单号,产品名称,规格,单价,数量,金额,销售员,客户名称,地址,联系电话
2024-11-27,A2020006,四季休闲服 藏青色,件,420.00,12,5040.0,魏莹雪,客户2,北京市怀柔区,13213***991
日期,客户名称,地址,联系电话,金额,交款人,收款人
2024-11-28,客户1,北京市朝阳区,13047***202,12000,张三,李静
2024-11-28,客户3,北京市丰台区,15027***013,10000,张三,李静
"""
    },
    "real_supplier_sheet": {
        "filename": "各供货商清单台账(1).xlsx",
        "description": "真实多供货商进货清单：包含西藏腾格商贸、四季鲜果、鑫鑫百货、科峰百威、友轩商行、锦锈生活等 6 家供货商，157 笔进货流水与 68 种商品物料。",
        "csv_text": open(os.path.join(BASE_DIR, "test_supplier_sheet.csv"), "r", encoding="utf-8").read() if os.path.exists(os.path.join(BASE_DIR, "test_supplier_sheet.csv")) else ""
    }
}


class LedgerRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/" or path == "/index.html":
            index_path = os.path.join(BASE_DIR, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_json({"error": "index.html not found"}, 404)
            return

        if path.startswith("/static/"):
            rel_path = path[len("/static/"):].lstrip("/\\")
            file_path = os.path.join(BASE_DIR, "static", rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = "application/javascript" if file_path.endswith(".js") else "application/octet-stream"
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_json({"error": "File not found"}, 404)
            return

        if path == "/api/state":
            state = get_dashboard_state()
            state["sample_scenarios"] = {
                k: {"filename": v["filename"], "description": v["description"]}
                for k, v in SAMPLE_SCENARIOS.items()
            }
            self._send_json(state)
            return

        if path == "/api/sample-csv":
            qs = urllib.parse.parse_qs(parsed_url.query)
            key = qs.get("key", ["restock_and_sales"])[0]
            sc = SAMPLE_SCENARIOS.get(key, SAMPLE_SCENARIOS["restock_and_sales"])
            csv_bytes = ("\ufeff" + sc["csv_text"]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(sc['filename'])}")
            self.send_header("Content-Length", str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        try:
            self._handle_post_inner()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json({
                "ok": False,
                "error": f"服务端处理异常: {str(e)}",
                "result": {
                    "ok": False,
                    "reply": f"⚠️ 识别处理遇到异常：{str(e)}"
                }
            }, 200)

    def _handle_post_inner(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

        # 1. System Initialization & Reset
        if path == "/api/system/initialize":
            mode = body.get("mode", "reset_sample")
            if mode == "empty":
                reset_to_empty()
            elif mode == "clear_tx":
                clear_transactions_only()
            else:
                reset_to_sample()
            self._send_json({"ok": True, "mode": mode, "state": get_dashboard_state()})
            return

        # 2. Upload Preview & Commit
        if path == "/api/upload/preview":
            scenario_key = body.get("scenario_key")
            if scenario_key and scenario_key in SAMPLE_SCENARIOS:
                sc = SAMPLE_SCENARIOS[scenario_key]
                preview = parse_uploaded_csv_or_rows(raw_text=sc["csv_text"], filename=sc["filename"])
            elif "rows" in body and isinstance(body["rows"], list):
                preview = parse_uploaded_csv_or_rows(rows=body["rows"], filename=body.get("filename", "上传Excel表格.xlsx"))
            else:
                preview = parse_uploaded_csv_or_rows(raw_text=body.get("csv_text", ""), filename=body.get("filename", "上传表格.csv"))

            auto_commit = bool(body.get("auto_commit", False))
            if auto_commit and preview["total_records"] > 0:
                commit_res = commit_parsed_data(
                    preview["parsed"],
                    source_name=preview["filename"],
                    source_type="file_upload",
                    parse_mode="AI 实时直通入账"
                )
                self._send_json({
                    "ok": True,
                    "auto_committed": True,
                    "preview": preview,
                    "commit_result": commit_res,
                    "state": get_dashboard_state()
                })
                return

            self._send_json({"ok": True, "auto_committed": False, "preview": preview})
            return

        if path == "/api/upload/commit":
            parsed_data = body.get("parsed", {})
            filename = body.get("filename", "新上传表格.csv")
            source_type = body.get("source_type", "file_upload")
            parse_mode = body.get("parse_mode", "AI 语义解析 + 人工确认")
            skip_duplicates = bool(body.get("skip_duplicates", True))
            commit_res = commit_parsed_data(
                parsed_data,
                source_name=filename,
                source_type=source_type,
                parse_mode=parse_mode,
                skip_duplicates=skip_duplicates
            )
            self._send_json({
                "ok": True,
                "commit_result": commit_res,
                "state": get_dashboard_state()
            })
            return

        # 3. Full CRUD Endpoints for Data Editing
        if path.startswith("/api/crud/"):
            entity = path.replace("/api/crud/", "").strip()
            action = body.get("action", "save")
            data = body.get("data", {})
            row_id = body.get("id") or data.get("id")

            res = {"ok": False, "error": "未知操作"}

            if entity == "product":
                res = delete_product(row_id) if action == "delete" else save_product(data)
            elif entity == "customer":
                res = delete_customer(row_id) if action == "delete" else save_customer(data)
            elif entity == "supplier":
                res = delete_supplier(row_id) if action == "delete" else save_supplier(data)
            elif entity == "purchase":
                res = delete_purchase(row_id) if action == "delete" else save_purchase(data)
            elif entity == "sale":
                res = delete_sale(row_id) if action == "delete" else save_sale(data)
            elif entity == "payment":
                res = delete_payment(row_id) if action == "delete" else save_payment(data)
            elif entity == "receipt":
                res = delete_receipt(row_id) if action == "delete" else save_receipt(data)

            if res.get("ok"):
                self._send_json({"ok": True, "state": get_dashboard_state()})
            else:
                self._send_json({"ok": False, "error": res.get("error", "操作失败")}, 400)
            return

        # 4. Natural Language Assistant & Multimodal File/Image Recognition
        if path == "/api/ai/multimodal_recognize":
            res = recognize_multimodal_upload(body)
            self._send_json({
                "ok": res.get("ok", False),
                "result": res,
                "reply": res.get("reply", ""),
                "state": get_dashboard_state()
            })
            return

        if path in ("/api/ai/chat", "/api/chat"):
            if body.get("image_base64") or body.get("rows") or body.get("csv_text"):
                res = recognize_multimodal_upload(body)
                self._send_json({
                    "ok": res.get("ok", False),
                    "result": res,
                    "reply": res.get("reply", ""),
                    "state": get_dashboard_state()
                })
                return
            text = body.get("text", "") or body.get("message", "")
            res = process_natural_language(text)
            self._send_json({
                "ok": True,
                "result": res,
                "reply": res.get("reply", ""),
                "state": get_dashboard_state()
            })
            return

        # 4.1 AI API Test Connection
        if path == "/api/ai/test_connection":
            test_res = test_llm_connectivity(body if body.get("api_key") else None)
            self._send_json(test_res)
            return

        # 4.2 Global Financial Audit Memo
        if path == "/api/ai/audit":
            state = get_dashboard_state()
            memo = generate_financial_audit_memo(state, focus_area=body.get("focus", "all"))
            self._send_json({"ok": True, "memo": memo})
            return

        # 5. Batch Rollback & Delete
        if path == "/api/batches/rollback":
            batch_id = int(body.get("batch_id", 0))
            res = rollback_batch(batch_id)
            self._send_json({"ok": res["ok"], "result": res, "state": get_dashboard_state()})
            return

        if path == "/api/batches/delete":
            batch_id = int(body.get("batch_id", 0))
            res = delete_batch(batch_id)
            self._send_json({"ok": res["ok"], "result": res, "state": get_dashboard_state()})
            return

        if path == "/api/batches/clear_rolled_back":
            res = clear_rolled_back_batches()
            self._send_json({"ok": res["ok"], "result": res, "state": get_dashboard_state()})
            return

        # 6. AI Settings
        if path == "/api/settings/ai":
            provider = body.get("provider", "deepseek")
            api_key = body.get("api_key", "").strip()
            base_url = body.get("base_url", "https://api.deepseek.com").strip()
            model_name = body.get("model_name", "deepseek-chat").strip()
            conn = get_conn()
            cur = conn.cursor()
            if api_key:
                cur.execute("""
                    UPDATE ai_settings
                    SET provider = ?, api_key = ?, base_url = ?, model_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (provider, api_key, base_url, model_name))
            else:
                cur.execute("""
                    UPDATE ai_settings
                    SET provider = ?, base_url = ?, model_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (provider, base_url, model_name))
            conn.commit()
            conn.close()

            # Test connection if key is present
            conn_test = test_llm_connectivity()
            self._send_json({"ok": True, "conn_test": conn_test, "state": get_dashboard_state()})
            return

        # 7. Legacy reset
        if path == "/api/reset":
            reset_to_sample()
            self._send_json({"ok": True, "state": get_dashboard_state()})
            return

        # 8. 系统安全退出 API (供客户端调用平滑关闭后台服务)
        if path == "/api/system/exit":
            self._send_json({"ok": True, "message": "极智台账核心服务已接收关闭指令，正在安全退出..."})
            def _shutdown():
                import time
                time.sleep(0.6)
                os._exit(0)
            threading.Thread(target=_shutdown, daemon=True).start()
            return

        self._send_json({"error": "Unknown endpoint"}, 404)

    def log_message(self, format, *args):
        pass


def open_native_window(url, width=1440, height=900):
    """优先使用原生独立 App 窗口 (Edge/Chrome --app 或 pywebview)，彻底隐藏地址栏与标签页"""
    # 1. Windows: 优先调用 Edge / Chrome 原生应用窗口模式
    if sys.platform == "win32":
        candidates = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for exe in candidates:
            if os.path.isfile(exe):
                app_data = os.path.expandvars(r"%LocalAppData%\SmartLedger\app_profile")
                try:
                    subprocess.Popen([
                        exe,
                        f"--app={url}",
                        f"--window-size={width},{height}",
                        f"--user-data-dir={app_data}",
                        "--no-first-run",
                        "--no-default-browser-check"
                    ])
                    return "windows_app"
                except Exception:
                    pass

    # 2. macOS: 优先检测 Edge / Chrome 原生 App 模式
    elif sys.platform == "darwin":
        for app in ["/Applications/Microsoft Edge.app", "/Applications/Google Chrome.app", "/Applications/Brave Browser.app"]:
            if os.path.isdir(app):
                try:
                    subprocess.Popen([
                        "open", "-na", app,
                        "--args",
                        f"--app={url}",
                        f"--window-size={width},{height}"
                    ])
                    return "mac_app"
                except Exception:
                    pass

    # 3. Linux: 优先检测 Chromium 核心
    elif sys.platform.startswith("linux"):
        for cmd in ["microsoft-edge", "google-chrome", "chromium-browser", "chromium"]:
            if shutil.which(cmd):
                try:
                    subprocess.Popen([cmd, f"--app={url}", f"--window-size={width},{height}"])
                    return "linux_app"
                except Exception:
                    pass

    # 4. 兜底方案：默认系统浏览器
    try:
        webbrowser.open(url)
        return "browser"
    except Exception:
        return "none"


def is_port_in_use(port=8765):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def run_server(port=8765):
    # 如果服务已在运行，直接唤起客户端窗口并退出当前多余进程
    if is_port_in_use(port):
        print(f"[*] 检测到端口 {port} 已被占用，正在验证现有极智台账服务...")
        try:
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/state")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    print(f"[✓] 极智台账服务已在运行 (http://127.0.0.1:{port})，直接唤起专属应用窗口。")
                    if "--window" in sys.argv or "--app" in sys.argv or getattr(sys, 'frozen', False):
                        open_native_window(f"http://127.0.0.1:{port}")
                    sys.exit(0)
        except Exception:
            pass

    init_db(force_reset=False)
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", port), LedgerRequestHandler)
    print(f"极智台账核心服务已就绪，正在监听: http://127.0.0.1:{port}")

    # 若为打包单文件 EXE 或显式指定窗口参数，自动唤起独立应用窗口
    if getattr(sys, 'frozen', False) or "--window" in sys.argv or "--app" in sys.argv:
        def _open():
            open_native_window(f"http://127.0.0.1:{port}")
        threading.Timer(0.8, _open).start()

    server.serve_forever()


if __name__ == "__main__":
    run_server()
