@echo off
chcp 65001 >nul
title KHBD & SMAS Pro - Hệ Thống Soạn KHBD & Đồng Bộ SMAS
cls

echo ================================================================
echo    KHBD Pro - Soạn KHBD & Đồng Bộ Lịch Báo Giảng SMAS
echo    Trường TH & THCS Đăk Trôi - Giáo Viên: Trần Đức Tình
echo ================================================================
echo.
echo [*] Đang khởi động máy chủ cục bộ trên cổng 8765...
echo [*] Trình duyệt web sẽ tự động mở trong vài giây.
echo.

start "" "http://127.0.0.1:8765"
python server.py

pause
