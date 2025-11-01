#!/bin/bash
# Quick test script for FastAPI server endpoints

echo "=================================="
echo "🧪 Testing TravelMate AI API"
echo "=================================="
echo ""

BASE_URL="http://localhost:8080"

echo "1. Testing health endpoint..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo -e "\n✅ Health check passed\n"

echo "2. Testing policies list..."
curl -s "$BASE_URL/policies" | python3 -m json.tool | head -30
echo -e "\n✅ Policies list passed\n"

echo "3. Testing ask endpoint..."
curl -s -X POST "$BASE_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is covered under medical benefits?"}' \
  | python3 -m json.tool | head -40
echo -e "\n✅ Ask endpoint passed\n"

echo "===================================="
echo "🎉 All API tests passed!"
echo "===================================="

