@echo off
cd /d "c:\Users\DHARM\Desktop\Projects\Claude Project\INTELLIGENT DATA PIPELINE BUILDER\backend"
uvicorn app.main:app --reload --port 8000
pause
