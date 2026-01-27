#!/bin/bash

echo "=== Startup Time Comparison ==="
echo ""

# Test Go
echo "Testing Go application..."
cd app_go
START=$(date +%s.%N)
PORT=8080 ./devops-info-service > /dev/null 2>&1 &
GO_PID=$!

# Wait for Go to be ready
while ! curl -s http://localhost:8080/health > /dev/null 2>&1; do
    sleep 0.01
done

END=$(date +%s.%N)
GO_TIME=$(echo "$END - $START" | bc)
echo "Go startup time: ${GO_TIME} seconds"

# Kill Go
kill $GO_PID
wait $GO_PID 2>/dev/null

sleep 1
cd ..

# Test Python
echo ""
echo "Testing Python application..."
cd app_python
START=$(date +%s.%N)
PORT=5000 python3 app.py > /dev/null 2>&1 &
PYTHON_PID=$!

# Wait for Python to be ready
while ! curl -s http://localhost:5000/health > /dev/null 2>&1; do
    sleep 0.01
done

END=$(date +%s.%N)
PYTHON_TIME=$(echo "$END - $START" | bc)
echo "Python startup time: ${PYTHON_TIME} seconds"

# Kill Python
kill $PYTHON_PID
wait $PYTHON_PID 2>/dev/null

cd ..

# Calculate ratio
RATIO=$(echo "scale=2; $PYTHON_TIME / $GO_TIME" | bc)

echo ""
echo "=== Results ==="
echo "Go:     ${GO_TIME}s"
echo "Python: ${PYTHON_TIME}s"
echo "Ratio:  Python is ${RATIO}x slower"
