#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://localhost:8000/api/resources/stats}"
DURATION_SECONDS="${2:-60}"

echo "Starting FinOps API load generator against ${TARGET_URL} for ${DURATION_SECONDS}s..."
END_TIME=$((SECONDS + DURATION_SECONDS))

while [ $SECONDS -lt $END_TIME ]; do
  for _ in {1..15}; do
    curl -s -o /dev/null "${TARGET_URL}" &
  done
  wait
done

echo "Load test completed."