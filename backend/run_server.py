"""启动后端服务器。"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)