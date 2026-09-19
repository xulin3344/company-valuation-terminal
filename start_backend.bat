@echo off
cd /d "C:\Users\30404\Desktop\每天一个有价值的项目\公司估值器\backend"
"C:\Users\30404\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -m uvicorn app.api.main:app --port 8000 --host 127.0.0.1 --reload