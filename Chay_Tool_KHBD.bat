@echo off
chcp 65001 >nul
title KHBD Pro - Trình Chuẩn Hoá Giáo Án Hàng Loạt
cls

echo ================================================================
echo    KHBD Pro - Trình Chuẩn Hoá & Đổi Tên Kế Hoạch Bài Dạy
echo    Trường TH & THCS Đăk Trôi - Giáo Viên: Lê Thị Phương Thảo
echo ================================================================
echo.
echo [*] Đang khởi động máy chủ cục bộ trên cổng 8765...
echo [*] Trình duyệt web sẽ tự động mở trong vài giây.
echo.

start "" "http://127.0.0.1:8765"
python server.py

pause
