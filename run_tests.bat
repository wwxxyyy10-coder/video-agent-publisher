@echo off
REM -*- coding: utf-8 -*-
REM سكريبت تشغيل الاختبارات على Windows

echo 🧪 بدء الاختبارات...
echo ==================

REM التحقق من المتطلبات
echo 📦 التحقق من المتطلبات...
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytest غير مثبت
    echo قم بتشغيل: pip install -r requirements-test.txt
    exit /b 1
)

echo ✅ pytest متوفر

REM تشغيل الاختبارات
echo.
echo 🚀 تشغيل الاختبارات...
echo.

REM اختبارات الوحدة
echo 📋 اختبارات الوحدة:
python -m pytest tests/ -v -m unit --tb=short

REM اختبارات التكامل
echo.
echo 🔗 اختبارات التكامل:
python -m pytest tests/ -v -m integration --tb=short

REM تقرير التغطية
echo.
echo 📊 إنشاء تقرير التغطية...
python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

echo.
echo ✅ انتهت الاختبارات!
echo 📈 يمكنك مراجعة تقرير التغطية في: htmlcov/index.html
