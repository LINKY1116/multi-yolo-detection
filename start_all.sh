#!/bin/bash

cd "$(dirname "$0")"

echo "启动后端 Flask..."
python app.py &
BACKEND_PID=$!

echo "启动前端 Vue..."
cd frontend
npm run serve &
FRONTEND_PID=$!

echo ""
echo "后端：http://localhost:5001"
echo "前端：http://localhost:8080"
echo ""
echo "按 Ctrl+C 可同时停止前后端"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait
