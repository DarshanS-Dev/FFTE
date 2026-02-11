#!/bin/bash

echo "🚀 Starting FFTE Complete Demo..."
echo ""

# Step 1: Check if victim.py exists
if [ ! -f "victim.py" ]; then
    echo "❌ Error: victim.py not found!"
    echo "Create victim.py with:"
    echo '----------------------------------------'
    echo 'from fastapi import FastAPI'
    echo 'from pydantic import BaseModel'
    echo ''
    echo 'app = FastAPI()'
    echo ''
    echo 'class DivideInput(BaseModel):'
    echo '    a: int'
    echo '    b: int'
    echo ''
    echo '@app.post("/divide")'
    echo 'def divide(data: DivideInput):'
    echo '    return {"result": data.a // data.b}'
    echo '----------------------------------------'
    exit 1
fi

# Step 2: Start victim API in background
echo "1️⃣ Starting Victim API..."
uvicorn victim:app --reload &
API_PID=$!
echo "   API PID: $API_PID"
sleep 3  # Wait for API to start

# Step 3: Test API is running
echo ""
echo "2️⃣ Testing API connection..."
curl -s http://127.0.0.1:8000/openapi.json > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ API is running at http://127.0.0.1:8000"
else
    echo "   ❌ API failed to start"
    kill $API_PID
    exit 1
fi

# Step 4: Run expo demo
echo ""
echo "3️⃣ Running Expo Demo..."
python expo_demo.py

# Step 5: Run simple test
echo ""
echo "4️⃣ Running Simple Test..."
python simple_test.py

# Step 6: Run full FFTE (if it exists)
if [ -f "app.py" ]; then
    echo ""
    echo "5️⃣ Running Full FFTE Engine..."
    python app.py
fi

# Step 7: Cleanup
echo ""
echo "🛑 Stopping Victim API..."
kill $API_PID
echo ""
echo "✅ Demo Complete!"
echo ""
echo "💡 To run again, execute: ./run_all.sh"