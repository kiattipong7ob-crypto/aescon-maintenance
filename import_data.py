import os
import sys
import glob
import sqlite3
import json
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

# Target project directory
PROJECT_DIR = r"D:\AESCON Maintenance\Maintenance AES\แอปตรวจสอบเครื่องมือภายในบริษัท"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
STATIC_DIR = os.path.join(PROJECT_DIR, "static")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "maintenance.db")

# Locate source excel file
excel_files = glob.glob(r"C:\Users\Admin\Desktop\**\F-MT-68*.xlsx", recursive=True)
if not excel_files:
    excel_files = glob.glob(r"C:\Users\Admin\Downloads\**\F-MT-68*.xlsx", recursive=True)

if not excel_files:
    print("ERROR: Could not find F-MT-68 Excel file.")
    sys.exit(1)

EXCEL_FILE = excel_files[0]
print(f"Reading Excel source from: {EXCEL_FILE}")

# Initialize SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.executescript("""
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT DEFAULT 'ใช้งานได้',
    location TEXT DEFAULT 'AESCON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pm_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    month_index INTEGER NOT NULL,
    week_index INTEGER NOT NULL, -- 1 to 4 or 5
    week_num_yearly INTEGER NOT NULL, -- 1 to 48
    plan_value TEXT, -- '⚫' or null
    actual_value TEXT, -- completed date/status or null
    FOREIGN KEY(tool_id) REFERENCES tools(id)
);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    maintenance_type TEXT NOT NULL, -- 'PM ตามแผน', 'แจ้งซ่อมฉุกเฉิน / ชำรุด', 'เปลี่ยนอะไหล่', 'ตรวจเช็คสภาพ'
    maintenance_date TEXT NOT NULL,
    inspector_name TEXT NOT NULL,
    result_status TEXT NOT NULL, -- 'ปกติผ่านเกณฑ์', 'ซ่อมเสร็จสมบูรณ์', 'มีข้อบกพร่อง/รอซ่อม', 'รออะไหล่', 'ปลดระวาง/ชำรุด'
    details TEXT,
    spare_parts TEXT,
    cost REAL DEFAULT 0,
    month_index INTEGER,
    week_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tool_id) REFERENCES tools(id)
);

CREATE INDEX IF NOT EXISTS idx_tools_code ON tools(code);
CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_pm_plans_tool_id ON pm_plans(tool_id);
CREATE INDEX IF NOT EXISTS idx_pm_plans_week ON pm_plans(week_num_yearly);
CREATE INDEX IF NOT EXISTS idx_logs_tool_id ON maintenance_logs(tool_id);
""")

conn.commit()

# Clear existing data in tools and pm_plans before re-import
cursor.execute("DELETE FROM pm_plans")
cursor.execute("DELETE FROM tools")
conn.commit()

print("Opening Excel sheet 'F68 V.2'...")
wb = openpyxl.load_workbook(EXCEL_FILE, read_only=True)
ws = wb['F68 V.2']

# Month names mapping
MONTH_NAMES = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

# Read rows
tools_inserted = 0
plans_inserted = 0

rows = list(ws.iter_rows(values_only=True))
print(f"Total rows in sheet: {len(rows)}")

# Build schedule week mapping from header (Row 4 & 5)
# In row 5, col 4 to 51 (index 3 to 50) correspond to weeks 1-4 across 12 months (48 weeks)
week_columns = []
current_month_idx = 0
for col_idx in range(3, len(rows[4])):
    w_val = str(rows[4][col_idx]).strip() if rows[4][col_idx] is not None else ""
    if 'week' in w_val.lower():
        # calculate month (every 4 weeks = 1 month)
        m_idx = len(week_columns) // 4
        w_idx = (len(week_columns) % 4) + 1
        m_name = MONTH_NAMES[m_idx] if m_idx < len(MONTH_NAMES) else f"เดือน {m_idx+1}"
        yearly_week = len(week_columns) + 1
        week_columns.append({
            "col_index": col_idx,
            "month_name": m_name,
            "month_index": m_idx + 1,
            "week_index": w_idx,
            "week_num_yearly": yearly_week
        })
    if len(week_columns) >= 48:
        break

print(f"Mapped {len(week_columns)} weeks across 12 months.")

tool_batch = []
plan_batch = []

seen_codes = {}

for r_idx in range(5, len(rows)):
    row = rows[r_idx]
    if len(row) < 3:
        continue
    name = str(row[0]).strip() if row[0] is not None else ""
    code = str(row[1]).strip() if row[1] is not None else ""
    target = str(row[2]).strip() if row[2] is not None else ""

    if target == 'P' and code:
        # Determine category prefix (e.g. AES-A01 from AES-A01-0001)
        parts = code.split('-')
        if len(parts) >= 2:
            category = f"{parts[0]}-{parts[1]}"
        else:
            category = "AES-OTHER"

        # Check for duplicate code in Excel and handle gracefully
        if code in seen_codes:
            unique_code = f"{code}_{seen_codes[code]}"
            seen_codes[code] += 1
        else:
            unique_code = code
            seen_codes[code] = 1

        cursor.execute("INSERT INTO tools (code, name, category, status) VALUES (?, ?, ?, ?)",
                       (unique_code, name, category, "ใช้งานได้"))
        tool_id = cursor.lastrowid
        tools_inserted += 1

        # Check PM plan dots across weeks
        for w_info in week_columns:
            c_idx = w_info["col_index"]
            cell_val = str(row[c_idx]).strip() if c_idx < len(row) and row[c_idx] is not None else ""
            has_dot = 1 if ('⚫' in cell_val or '●' in cell_val or 'x' in cell_val.lower() or 'p' in cell_val.lower() or cell_val != '') else 0

            if has_dot:
                plan_batch.append((
                    tool_id,
                    w_info["month_name"],
                    w_info["month_index"],
                    w_info["week_index"],
                    w_info["week_num_yearly"],
                    "⚫",
                    None
                ))

        if len(plan_batch) >= 1000:
            cursor.executemany("""
                INSERT INTO pm_plans (tool_id, month_name, month_index, week_index, week_num_yearly, plan_value, actual_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, plan_batch)
            plans_inserted += len(plan_batch)
            plan_batch = []

if plan_batch:
    cursor.executemany("""
        INSERT INTO pm_plans (tool_id, month_name, month_index, week_index, week_num_yearly, plan_value, actual_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, plan_batch)
    plans_inserted += len(plan_batch)

conn.commit()
wb.close()

print(f"--- Import Finished Successfully! ---")
print(f"Total Tools Imported: {tools_inserted}")
print(f"Total PM Plan Scheduled Items: {plans_inserted}")
print(f"Database saved to: {DB_PATH}")

conn.close()
