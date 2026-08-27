@echo off
chcp 65001 > nul
title AESCON Maintenance App (F-MT-68)

echo ======================================================================
echo           AESCON MAINTENANCE - ระบบตรวจสอบและบันทึกการซ่อมบำรุง
echo           อ้างอิงเอกสาร F-MT-68-rev2 (แผนการบำรุงรักษาประจำปี 2026)
echo ======================================================================
echo.

cd /d "%~dp0"

:: Check database
if not exist "data\maintenance.db" (
    echo [INFO] ตรวจพบการเปิดใช้งานครั้งแรก กำลังนำเข้าข้อมูลเครื่องมือจากไฟล์ Excel...
    python import_data.py
    echo.
)

echo [INFO] กำลังเริ่มระบบเซิร์ฟเวอร์...
echo [INFO] เปิดโปรแกรมผ่านเบราว์เซอร์ที่: http://localhost:8000
echo.

:: Open browser after 2 seconds in background
start "" timeout /t 2 /nobreak >nul && start http://localhost:8000

:: Run Python Server
python server.py 8000

pause
