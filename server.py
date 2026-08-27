import os
import sys
import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import datetime
import csv
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(DATA_DIR, "maintenance.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Keyword matching table for tool type
CHECKLIST_MAPPING = [
    (["สว่านไร้สาย", "แบตเตอรี่", "ไร้สาย", "dcd", "dcf"], "สว่านไร้สาย"),
    (["สว่าน", "drill"], "สว่าน"),
    (["หินเจียร", "หินเจียร์", "เจียร", "grinder", "ลูกหมู"], "หินเจียร์"),
    (["เลื่อยวงเดือน", "circular saw"], "เลื่อยวงเดือน"),
    (["เลื่อยจิ๊กซอว์", "จิ๊กซอว์", "jigsaw"], "เลื่อยจิ๊กซอว์"),
    (["เลื่อย", "saw"], "เลื่อยวงเดือน"),
    (["ปั๊มลม", "air compressor", "compressor"], "ปั๊มลม"),
    (["ปั๊มซับเมิร์ส", "submersible", "ไดโว่", "ไดโว่ดูดน้ำ"], "ปั๊มซับเมิร์ส"),
    (["ปั๊มน้ำอัตโนมัติ", "auto pump", "ปั๊มน้ำบ้าน"], "ปั๊มน้ำอัตโนมัติ"),
    (["ปั๊มน้ำหอยโข่ง", "หอยโข่ง", "centrifugal"], "ปั๊มน้ำหอยโข่ง"),
    (["เครื่องสูบน้ำแบบเครื่องยนต์", "สูบน้ำเครื่องยนต์", "engine pump"], "เครื่องสูบน้ำแบบเครื่องยนต์"),
    (["เครื่องสูบน้ำ", "ปั๊มน้ำ", "pump"], "เครื่องสูบน้ำ"),
    (["เครื่องตบดิน", "ตบดิน", "compactor"], "เครื่องตบดิน"),
    (["เครื่องกระทุ้งดิน", "กระทุ้งดิน", "tamping rammer"], "เครื่องกระทุ้งดิน"),
    (["รถบดดิน", "รถบด", "roller"], "รถบดดิน"),
    (["ถังดับเพลิง", "ดับเพลิง", "fire extinguisher"], "ถังดับเพลิง"),
    (["รอกไฟฟ้า", "hoist"], "รอกไฟฟ้า"),
    (["ชุดรอกสลิงไฟฟ้า", "รอกสลิง", "wire rope hoist"], "ชุดรอกสลิงไฟฟ้า"),
    (["รอกโซ่มือโยก", "รอกโซ่", "chain block", "lever block"], "รอกโซ่มือโยก"),
    (["คีมปลอกสาย", "ปลอกสาย", "wire stripper"], "คีมปลอกสาย"),
    (["คีมย้ำหางปลา", "ย้ำหางปลา", "crimper"], "คีมย้ำหางปลาไฮดรอลิก"),
    (["คีมล็อก", "คีมล็อค", "คีม", "plier"], "คีมล็อกปากตรง"),
    (["เครื่องขัดกระดาษทราย", "ขัดกระดาษทราย", "sander"], "เครื่องขัดกระดาษทราย"),
    (["เครื่องขัดปูนแมงปอ", "แมงปอ", "power trowel"], "เครื่องขัดปูนแมงปอ"),
    (["เครื่องขัดปูนแบบนั่ง", "ขัดปูนแบบนั่ง", "ride on trowel"], "เครื่องขัดปูนแบบนั่ง"),
    (["เครื่องขัดหน้าพื้น", "ขัดหน้าพื้น", "floor polisher"], "เครื่องขัดหน้าพื้น"),
    (["เครื่องขัดเงา", "ขัดเงา", "polisher"], "เครื่องขัดเงา"),
    (["ไฟเบอร์", "ตัดไฟเบอร์", "cut off machine"], "ไฟเบอร์"),
    (["เครื่องตัดจ๊อยส์", "ตัดจ๊อยส์", "joint cutter"], "เครื่องตัดจ๊อยส์"),
    (["เครื่องปาดปูน", "ปาดปูน", "screed"], "เครื่องปาดปูนรางยาว"),
    (["เครื่องผสมปูน", "ผสมปูน", "mixer"], "เครื่องผสมปูน"),
    (["พ็อกเก็ตเทปูน", "เทปูน", "concrete bucket"], "พ็อกเก็ตเทปูน"),
    (["วายจี้ปูนเบนซิน", "จี้ปูนเบนซิน", "vibrator engine"], "เครื่องวายจี้ปูนเบนซิน"),
    (["วายจี้ปูนไฟฟ้า", "จี้ปูน", "vibrator"], "เครื่องวายจี้ปูนไฟฟ้า"),
    (["หัวตัดแก๊ส", "ตัดแก๊ส", "gas cutter"], "หัวตัดแก๊ส"),
    (["เครื่องตัดกระเบื้อง", "ตัดกระเบื้อง", "tile cutter"], "เครื่องตัดกระเบื้อง"),
    (["เครื่องตัดองศา", "ตัดองศา", "miter saw"], "เครื่องตัดองศา"),
    (["เครื่องดัดเหล็ก", "ดัดเหล็ก", "bar bender", "rebar bender"], "เครื่องดัดเหล็ก"),
    (["เครื่องทดสอบโซล่า", "solar tester", "solar link", "solarmeter"], "เครื่องทดสอบโซล่า"),
    (["เครื่องเชื่อมท่อPPR", "เชื่อมท่อ", "ppr welder"], "เครื่องเชื่อมท่อPPR"),
    (["เครื่องเป่าลม", "เป่าลม", "blower"], "เครื่องเป่าลม"),
    (["ประแจทอร์ก", "torque wrench", "ประแจปอนด์"], "ประแจทอร์ก"),
    (["ชุดบล็อก", "ลูกบล็อก", "socket set", "บล็อกชุด"], "ชุดบล็อก"),
    (["บล็อกไฟฟ้า", "บล็อกลม", "impact wrench"], "ชุดบล็อก"),
    (["กรรไกรตัดเหล็ก", "กรรไกร", "cutter"], "คีมล็อกปากตรง"),
    (["ตู้เชื่อม", "เครื่องเชื่อม", "welder", "inverter"], "ตู้เชื่อม"),
    (["บันได", "ladder"], "บันได"),
    (["รถยนต์", "กระบะ", "เก๋ง", "car", "bmw", "toyota", "isuzu", "ford"], "รถยนต์"),
    (["แอนด์ลิฟต์", "x-lift", "scissor lift", "boom lift", "lift"], "แอนด์ลิฟต์")
]

def find_matched_tool_type(name, code="", category=""):
    text = f"{name} {code} {category}".lower()
    for keywords, chk_key in CHECKLIST_MAPPING:
        if any(k in text for k in keywords):
            return chk_key
    return "ทั่วไป"

class MaintenanceHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message, "success": False}, status=status)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static files & Homepage
        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
            return
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, rel_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            self.serve_file(file_path, mime_type or "application/octet-stream")
            return

        # API Endpoints
        try:
            if path == "/api/stats":
                self.handle_get_stats()
            elif path == "/api/categories":
                self.handle_get_categories()
            elif path == "/api/tools":
                self.handle_get_tools(query)
            elif path.startswith("/api/tools/"):
                tool_id = path.split("/")[-1]
                self.handle_get_tool_detail(tool_id)
            elif path == "/api/pm-schedule":
                self.handle_get_pm_schedule(query)
            elif path == "/api/checklists":
                self.handle_get_checklists(query)
            elif path == "/api/logs":
                self.handle_get_logs(query)
            elif path == "/api/export":
                self.handle_export_logs(query)
            else:
                self.send_error_json("Endpoint not found", status=404)
        except Exception as e:
            self.send_error_json(f"Server Error: {str(e)}", status=500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body_data = self.rfile.read(content_length)
            payload = json.loads(body_data.decode('utf-8')) if body_data else {}
        except Exception:
            self.send_error_json("Invalid JSON payload", status=400)
            return

        try:
            if path == "/api/maintenance":
                self.handle_post_maintenance(payload)
            elif path == "/api/tools":
                self.handle_post_tool(payload)
            else:
                self.send_error_json("Endpoint not found", status=404)
        except Exception as e:
            self.send_error_json(f"Server Error: {str(e)}", status=500)

    def serve_file(self, file_path, content_type):
        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_get_stats(self):
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM tools")
        total_tools = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tools WHERE status = 'ใช้งานได้'")
        active_tools = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tools WHERE status LIKE '%ชำรุด%' OR status LIKE '%ซ่อม%'")
        repair_tools = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pm_plans WHERE plan_value = '⚫'")
        total_pm_plans = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pm_plans WHERE plan_value = '⚫' AND actual_value IS NOT NULL AND actual_value != ''")
        completed_pm_plans = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM maintenance_logs")
        total_logs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM maintenance_logs WHERE result_status LIKE '%ชำรุด%' OR result_status LIKE '%บกพร่อง%'")
        defect_logs = cur.fetchone()[0]

        conn.close()

        pm_completion_rate = round((completed_pm_plans / total_pm_plans * 100), 1) if total_pm_plans > 0 else 0

        self.send_json({
            "success": True,
            "data": {
                "total_tools": total_tools,
                "active_tools": active_tools,
                "repair_tools": repair_tools,
                "total_pm_plans": total_pm_plans,
                "completed_pm_plans": completed_pm_plans,
                "pm_completion_rate": pm_completion_rate,
                "total_logs": total_logs,
                "defect_logs": defect_logs
            }
        })

    def handle_get_categories(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT category, COUNT(*) as count FROM tools GROUP BY category ORDER BY category ASC")
        rows = cur.fetchall()
        conn.close()

        categories = [{"category": r["category"], "count": r["count"]} for r in rows]
        self.send_json({"success": True, "data": categories})

    def handle_get_tools(self, query):
        q = query.get("q", [""])[0].strip()
        category = query.get("category", [""])[0].strip()
        status = query.get("status", [""])[0].strip()
        month = query.get("month", [""])[0].strip()
        week = query.get("week", [""])[0].strip()
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["50"])[0])
        offset = (page - 1) * limit

        conn = get_db()
        cur = conn.cursor()

        conditions = []
        params = []

        if q:
            conditions.append("(t.code LIKE ? OR t.name LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        if category and category != "all":
            conditions.append("t.category = ?")
            params.append(category)

        if status and status != "all":
            conditions.append("t.status = ?")
            params.append(status)

        if month:
            conditions.append("t.id IN (SELECT tool_id FROM pm_plans WHERE month_index = ? AND plan_value = '⚫')")
            params.append(int(month))

        if week:
            conditions.append("t.id IN (SELECT tool_id FROM pm_plans WHERE week_num_yearly = ? AND plan_value = '⚫')")
            params.append(int(week))

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_sql = f"SELECT COUNT(*) FROM tools t {where_clause}"
        cur.execute(count_sql, params)
        total_count = cur.fetchone()[0]

        data_sql = f"""
            SELECT t.id, t.code, t.name, t.category, t.status, t.location,
                   (SELECT COUNT(*) FROM pm_plans WHERE tool_id = t.id AND plan_value = '⚫') as pm_count,
                   (SELECT COUNT(*) FROM maintenance_logs WHERE tool_id = t.id) as log_count,
                   (SELECT MAX(maintenance_date) FROM maintenance_logs WHERE tool_id = t.id) as last_maintenance_date
            FROM tools t
            {where_clause}
            ORDER BY t.id ASC
            LIMIT ? OFFSET ?
        """
        cur.execute(data_sql, params + [limit, offset])
        rows = cur.fetchall()
        conn.close()

        tools = []
        for r in rows:
            d = dict(r)
            d["tool_type"] = find_matched_tool_type(d["name"], d["code"], d["category"])
            tools.append(d)

        self.send_json({
            "success": True,
            "data": tools,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        })

    def handle_get_checklists(self, query):
        tool_id = query.get("tool_id", [""])[0].strip()
        tool_type = query.get("tool_type", [""])[0].strip()

        conn = get_db()
        cur = conn.cursor()

        if tool_id:
            cur.execute("SELECT name, code, category FROM tools WHERE id = ?", (tool_id,))
            t = cur.fetchone()
            if t:
                tool_type = find_matched_tool_type(t["name"], t["code"], t["category"])

        if not tool_type:
            tool_type = "ทั่วไป"

        # Fetch daily checklist
        cur.execute("""
            SELECT item_no, item_text, standard_condition
            FROM checklist_templates
            WHERE tool_type = ? AND frequency = 'daily'
            ORDER BY item_no ASC
        """, (tool_type,))
        daily_items = [dict(r) for r in cur.fetchall()]

        if not daily_items:
            cur.execute("""
                SELECT item_no, item_text, standard_condition
                FROM checklist_templates
                WHERE tool_type = 'ทั่วไป' AND frequency = 'daily'
                ORDER BY item_no ASC
            """)
            daily_items = [dict(r) for r in cur.fetchall()]

        # Fetch monthly checklist
        cur.execute("""
            SELECT item_no, item_text, standard_condition
            FROM checklist_templates
            WHERE tool_type = ? AND frequency = 'monthly'
            ORDER BY item_no ASC
        """, (tool_type,))
        monthly_items = [dict(r) for r in cur.fetchall()]

        if not monthly_items:
            cur.execute("""
                SELECT item_no, item_text, standard_condition
                FROM checklist_templates
                WHERE tool_type = 'ทั่วไป' AND frequency = 'monthly'
                ORDER BY item_no ASC
            """)
            monthly_items = [dict(r) for r in cur.fetchall()]

        conn.close()

        self.send_json({
            "success": True,
            "tool_type": tool_type,
            "daily_checklist": daily_items,
            "monthly_checklist": monthly_items
        })

    def handle_get_tool_detail(self, tool_id):
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM tools WHERE id = ?", (tool_id,))
        tool_row = cur.fetchone()
        if not tool_row:
            conn.close()
            self.send_error_json("Tool not found", status=404)
            return

        tool = dict(tool_row)
        tool_type = find_matched_tool_type(tool["name"], tool["code"], tool["category"])
        tool["tool_type"] = tool_type

        # PM plans
        cur.execute("""
            SELECT month_name, month_index, week_index, week_num_yearly, plan_value, actual_value
            FROM pm_plans
            WHERE tool_id = ?
            ORDER BY week_num_yearly ASC
        """, (tool_id,))
        pm_plans = [dict(r) for r in cur.fetchall()]

        # Logs with inspection details
        cur.execute("""
            SELECT * FROM maintenance_logs
            WHERE tool_id = ?
            ORDER BY maintenance_date DESC, id DESC
        """, (tool_id,))
        log_rows = cur.fetchall()
        logs = []
        for lr in log_rows:
            log_dict = dict(lr)
            cur.execute("SELECT item_no, item_text, status_result, notes FROM inspection_details WHERE log_id = ? ORDER BY item_no ASC", (log_dict["id"],))
            log_dict["inspection_details"] = [dict(d) for d in cur.fetchall()]
            logs.append(log_dict)

        # Checklists for this tool
        cur.execute("SELECT item_no, item_text FROM checklist_templates WHERE tool_type = ? AND frequency = 'daily' ORDER BY item_no ASC", (tool_type,))
        daily_chk = [dict(r) for r in cur.fetchall()]
        if not daily_chk:
            cur.execute("SELECT item_no, item_text FROM checklist_templates WHERE tool_type = 'ทั่วไป' AND frequency = 'daily' ORDER BY item_no ASC")
            daily_chk = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT item_no, item_text FROM checklist_templates WHERE tool_type = ? AND frequency = 'monthly' ORDER BY item_no ASC", (tool_type,))
        monthly_chk = [dict(r) for r in cur.fetchall()]
        if not monthly_chk:
            cur.execute("SELECT item_no, item_text FROM checklist_templates WHERE tool_type = 'ทั่วไป' AND frequency = 'monthly' ORDER BY item_no ASC")
            monthly_chk = [dict(r) for r in cur.fetchall()]

        conn.close()

        self.send_json({
            "success": True,
            "data": {
                "tool": tool,
                "pm_plans": pm_plans,
                "logs": logs,
                "daily_checklist": daily_chk,
                "monthly_checklist": monthly_chk
            }
        })

    def handle_get_pm_schedule(self, query):
        month = query.get("month", [""])[0].strip()
        week = query.get("week", [""])[0].strip()
        category = query.get("category", [""])[0].strip()
        status_filter = query.get("status_filter", ["all"])[0].strip()

        conn = get_db()
        cur = conn.cursor()

        conditions = ["p.plan_value = '⚫'"]
        params = []

        if month:
            conditions.append("p.month_index = ?")
            params.append(int(month))

        if week:
            conditions.append("p.week_num_yearly = ?")
            params.append(int(week))

        if category and category != "all":
            conditions.append("t.category = ?")
            params.append(category)

        if status_filter == "done":
            conditions.append("p.actual_value IS NOT NULL AND p.actual_value != ''")
        elif status_filter == "pending":
            conditions.append("(p.actual_value IS NULL OR p.actual_value = '')")

        where_clause = " WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT p.id as plan_id, p.month_name, p.month_index, p.week_index, p.week_num_yearly,
                   p.plan_value, p.actual_value,
                   t.id as tool_id, t.code, t.name, t.category, t.status, t.location
            FROM pm_plans p
            JOIN tools t ON p.tool_id = t.id
            {where_clause}
            ORDER BY p.week_num_yearly ASC, t.code ASC
        """
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        items = []
        for r in rows:
            d = dict(r)
            d["tool_type"] = find_matched_tool_type(d["name"], d["code"], d["category"])
            items.append(d)

        self.send_json({
            "success": True,
            "total": len(items),
            "data": items
        })

    def handle_get_logs(self, query):
        q = query.get("q", [""])[0].strip()
        maintenance_type = query.get("type", [""])[0].strip()
        result_status = query.get("status", [""])[0].strip()
        start_date = query.get("start_date", [""])[0].strip()
        end_date = query.get("end_date", [""])[0].strip()
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["50"])[0])
        offset = (page - 1) * limit

        conn = get_db()
        cur = conn.cursor()

        conditions = []
        params = []

        if q:
            conditions.append("(t.code LIKE ? OR t.name LIKE ? OR l.inspector_name LIKE ? OR l.details LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

        if maintenance_type and maintenance_type != "all":
            conditions.append("l.maintenance_type = ?")
            params.append(maintenance_type)

        if result_status and result_status != "all":
            conditions.append("l.result_status = ?")
            params.append(result_status)

        if start_date:
            conditions.append("l.maintenance_date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("l.maintenance_date <= ?")
            params.append(end_date)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_sql = f"""
            SELECT COUNT(*) FROM maintenance_logs l
            JOIN tools t ON l.tool_id = t.id
            {where_clause}
        """
        cur.execute(count_sql, params)
        total_count = cur.fetchone()[0]

        data_sql = f"""
            SELECT l.*, t.code, t.name as tool_name, t.category
            FROM maintenance_logs l
            JOIN tools t ON l.tool_id = t.id
            {where_clause}
            ORDER BY l.maintenance_date DESC, l.id DESC
            LIMIT ? OFFSET ?
        """
        cur.execute(data_sql, params + [limit, offset])
        log_rows = cur.fetchall()

        logs = []
        for lr in log_rows:
            log_dict = dict(lr)
            cur.execute("SELECT item_no, item_text, status_result, notes FROM inspection_details WHERE log_id = ? ORDER BY item_no ASC", (log_dict["id"],))
            log_dict["inspection_details"] = [dict(d) for d in cur.fetchall()]
            logs.append(log_dict)

        conn.close()

        self.send_json({
            "success": True,
            "data": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        })

    def handle_export_logs(self, query):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT l.id, l.maintenance_date, t.code, t.name, t.category,
                   l.maintenance_type, l.result_status, l.inspector_name,
                   l.details, l.spare_parts, l.cost, l.created_at
            FROM maintenance_logs l
            JOIN tools t ON l.tool_id = t.id
            ORDER BY l.maintenance_date DESC, l.id DESC
        """)
        rows = cur.fetchall()

        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow([
            "ลำดับ", "วันที่ดำเนินการ", "รหัสเครื่องมือ", "ชื่อเครื่องมือ", "หมวดหมู่",
            "ประเภทการซ่อมบำรุง", "ผลการตรวจสอบ/ซ่อม", "ผู้ดำเนินการ/ช่าง",
            "รายละเอียดงาน", "อะไหล่ที่เปลี่ยน", "ค่าใช้จ่าย (บาท)", "หัวข้อตรวจเช็ค (Checklist)", "เวลาที่บันทึก"
        ])

        for r in rows:
            cur.execute("SELECT item_no, item_text, status_result FROM inspection_details WHERE log_id = ?", (r["id"],))
            details_list = [f"{d['item_no']}.{d['item_text']}: {d['status_result']}" for d in cur.fetchall()]
            chk_summary = " | ".join(details_list) if details_list else ""

            writer.writerow([
                r["id"], r["maintenance_date"], r["code"], r["name"], r["category"],
                r["maintenance_type"], r["result_status"], r["inspector_name"],
                r["details"] or "", r["spare_parts"] or "", r["cost"] or 0, chk_summary, r["created_at"]
            ])

        conn.close()
        csv_content = output.getvalue().encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename="AES_Maintenance_Logs.csv"')
        self.send_header('Content-Length', str(len(csv_content)))
        self.end_headers()
        self.wfile.write(csv_content)

    def handle_post_maintenance(self, payload):
        tool_id = payload.get("tool_id")
        maintenance_type = payload.get("maintenance_type", "PM ตามแผน")
        maintenance_date = payload.get("maintenance_date") or datetime.date.today().strftime("%Y-%m-%d")
        inspector_name = payload.get("inspector_name", "เจ้าหน้าที่ AESCON").strip()
        result_status = payload.get("result_status", "ปกติผ่านเกณฑ์")
        details = payload.get("details", "").strip()
        spare_parts = payload.get("spare_parts", "").strip()
        cost = float(payload.get("cost", 0) or 0)
        month_index = payload.get("month_index")
        week_index = payload.get("week_index")
        update_pm_actual = payload.get("update_pm_actual", True)
        checklist_items = payload.get("checklist_items", [])

        if not tool_id:
            self.send_error_json("tool_id is required", status=400)
            return

        conn = get_db()
        cur = conn.cursor()

        # Insert log
        cur.execute("""
            INSERT INTO maintenance_logs (
                tool_id, maintenance_type, maintenance_date, inspector_name,
                result_status, details, spare_parts, cost, month_index, week_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_id, maintenance_type, maintenance_date, inspector_name,
            result_status, details, spare_parts, cost, month_index, week_index
        ))
        log_id = cur.lastrowid

        # Insert inspection checklist details
        for it in checklist_items:
            cur.execute("""
                INSERT INTO inspection_details (log_id, item_no, item_text, status_result, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                log_id,
                it.get("item_no", 1),
                it.get("item_text", ""),
                it.get("status_result", "ปกติ (P)"),
                it.get("notes", "")
            ))

        # Update tool status
        if "ชำรุด" in result_status or "ปลดระวาง" in result_status:
            new_tool_status = "ชำรุด/ปลดระวาง"
        elif "รอซ่อม" in result_status or "รออะไหล่" in result_status:
            new_tool_status = "รอซ่อม/รออะไหล่"
        else:
            new_tool_status = "ใช้งานได้"

        cur.execute("UPDATE tools SET status = ? WHERE id = ?", (new_tool_status, tool_id))

        # Update PM Plan Actual if applicable
        if update_pm_actual:
            if month_index and week_index:
                cur.execute("""
                    UPDATE pm_plans
                    SET actual_value = ?
                    WHERE tool_id = ? AND month_index = ? AND week_index = ?
                """, (maintenance_date, tool_id, month_index, week_index))
            else:
                cur.execute("""
                    UPDATE pm_plans
                    SET actual_value = ?
                    WHERE id = (
                        SELECT id FROM pm_plans
                        WHERE tool_id = ? AND plan_value = '⚫' AND (actual_value IS NULL OR actual_value = '')
                        ORDER BY week_num_yearly ASC
                        LIMIT 1
                    )
                """, (maintenance_date, tool_id))

        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "message": "บันทึกการซ่อมบำรุงและรายการตรวจสอบเรียบร้อยแล้ว",
            "log_id": log_id
        })

    def handle_post_tool(self, payload):
        code = payload.get("code", "").strip()
        name = payload.get("name", "").strip()
        category = payload.get("category", "").strip()
        location = payload.get("location", "AESCON").strip()

        if not code or not name:
            self.send_error_json("รหัสและชื่อเครื่องมือจำเป็นต้องระบุ", status=400)
            return

        if not category:
            parts = code.split("-")
            category = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "AES-OTHER"

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO tools (code, name, category, location, status) VALUES (?, ?, ?, ?, 'ใช้งานได้')",
                        (code, name, category, location))
            tool_id = cur.lastrowid
            conn.commit()
            conn.close()
            self.send_json({"success": True, "tool_id": tool_id, "message": "เพิ่มเครื่องมือสำเร็จ"})
        except sqlite3.IntegrityError:
            conn.close()
            self.send_error_json(f"รหัสเครื่องมือ {code} มีอยู่ในระบบแล้ว", status=400)

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MaintenanceHandler)
    print(f"==================================================================")
    print(f"  AES Maintenance Web Application (with Checklist Integration)")
    print(f"  Local Access: http://localhost:{port}")
    print(f"==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run(port)
