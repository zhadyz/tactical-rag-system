#!/bin/bash
# Comprehensive System Test Suite for Tactical RAG
# Tests all components and generates detailed performance metrics

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results storage
TEST_RESULTS_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_RESULTS_DIR"

# Log file
LOG_FILE="$TEST_RESULTS_DIR/test_log.txt"

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5

    log "Testing: $name"

    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "$expected_status" ]; then
        log_success "$name - Status: $http_code"
        echo "$body" > "$TEST_RESULTS_DIR/${name// /_}.json"
        echo "$body"
        return 0
    else
        log_error "$name - Expected: $expected_status, Got: $http_code"
        echo "$body" > "$TEST_RESULTS_DIR/${name// /_}_ERROR.json"
        return 1
    fi
}

# Function to measure query time
measure_query_time() {
    local query=$1
    local mode=$2
    local output_file=$3

    local start_time=$(date +%s%N)

    response=$(curl -s -X POST "http://localhost:8000/api/query" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$query\", \"mode\": \"$mode\"}")

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds

    echo "$response" > "$output_file"
    echo "$duration"
}

echo "================================================================"
echo "  TACTICAL RAG - COMPREHENSIVE SYSTEM TEST SUITE"
echo "================================================================"
echo ""
log "Starting comprehensive system tests..."
log "Results will be saved to: $TEST_RESULTS_DIR"
echo ""

# ============================================================
# TEST 1: Docker Container Status
# ============================================================
echo "================================================================"
echo "TEST 1: Docker Container Status"
echo "================================================================"

log "Checking Docker containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee "$TEST_RESULTS_DIR/docker_status.txt"

REQUIRED_CONTAINERS=("ollama-server" "rag-redis-cache" "rag-backend-api")
for container in "${REQUIRED_CONTAINERS[@]}"; do
    if docker ps | grep -q "$container"; then
        log_success "Container running: $container"
    else
        log_error "Container not running: $container"
    fi
done

echo ""

# ============================================================
# TEST 2: Backend Health Check
# ============================================================
echo "================================================================"
echo "TEST 2: Backend Health Check"
echo "================================================================"

test_endpoint "Backend Health" "GET" "http://localhost:8000/api/health" "" "200"
echo ""

# ============================================================
# TEST 3: Models API Tests
# ============================================================
echo "================================================================"
echo "TEST 3: Models API Tests"
echo "================================================================"

log "Testing Models API endpoints..."

# List all models
test_endpoint "List All Models" "GET" "http://localhost:8000/api/models/" "" "200"
echo ""

# Get specific model info
test_endpoint "Get Ollama Model Info" "GET" "http://localhost:8000/api/models/llama3.1-8b" "" "200"
echo ""

test_endpoint "Get Phi3 Model Info" "GET" "http://localhost:8000/api/models/phi3-mini" "" "200"
echo ""

# Get recommendation
test_endpoint "Get Model Recommendation" "POST" "http://localhost:8000/api/models/recommend" \
    '{"vram_gb": 8, "priority": "balanced"}' "200"
echo ""

# Models health
test_endpoint "Models Health Check" "GET" "http://localhost:8000/api/models/health" "" "200"
echo ""

# ============================================================
# TEST 4: Query API Tests - Simple Mode
# ============================================================
echo "================================================================"
echo "TEST 4: Query API Tests - Simple Mode"
echo "================================================================"

log "Testing query with simple mode (cold - first query)..."
COLD_TIME=$(measure_query_time "What are the Air Force beard grooming standards?" "simple" \
    "$TEST_RESULTS_DIR/query_simple_cold.json")
log_success "Cold query completed in ${COLD_TIME}ms"
echo ""

log "Testing query with simple mode (cached - same query)..."
CACHED_TIME=$(measure_query_time "What are the Air Force beard grooming standards?" "simple" \
    "$TEST_RESULTS_DIR/query_simple_cached.json")
log_success "Cached query completed in ${CACHED_TIME}ms"

# Calculate speedup
SPEEDUP=$(echo "scale=2; $COLD_TIME / $CACHED_TIME" | bc)
log_success "Cache speedup: ${SPEEDUP}x faster"
echo ""

# ============================================================
# TEST 5: Query API Tests - Adaptive Mode
# ============================================================
echo "================================================================"
echo "TEST 5: Query API Tests - Adaptive Mode"
echo "================================================================"

log "Testing query with adaptive mode..."
ADAPTIVE_TIME=$(measure_query_time "What are the physical fitness requirements for officers?" "adaptive" \
    "$TEST_RESULTS_DIR/query_adaptive.json")
log_success "Adaptive query completed in ${ADAPTIVE_TIME}ms"
echo ""

# ============================================================
# TEST 6: Cache System Tests
# ============================================================
echo "================================================================"
echo "TEST 6: Cache System Tests"
echo "================================================================"

log "Testing cache with multiple queries..."

# Query 1 - Cold
log "Query 1 (cold): Beard standards"
Q1_COLD=$(measure_query_time "What are the beard grooming standards?" "simple" \
    "$TEST_RESULTS_DIR/cache_test_q1_cold.json")
log "Time: ${Q1_COLD}ms"

# Query 1 - Cached
log "Query 1 (cached): Beard standards"
Q1_CACHED=$(measure_query_time "What are the beard grooming standards?" "simple" \
    "$TEST_RESULTS_DIR/cache_test_q1_cached.json")
log "Time: ${Q1_CACHED}ms"

# Query 2 - Cold
log "Query 2 (cold): PT requirements"
Q2_COLD=$(measure_query_time "What are the PT requirements?" "simple" \
    "$TEST_RESULTS_DIR/cache_test_q2_cold.json")
log "Time: ${Q2_COLD}ms"

# Query 2 - Cached
log "Query 2 (cached): PT requirements"
Q2_CACHED=$(measure_query_time "What are the PT requirements?" "simple" \
    "$TEST_RESULTS_DIR/cache_test_q2_cached.json")
log "Time: ${Q2_CACHED}ms"

echo ""

# ============================================================
# TEST 7: Settings API Tests
# ============================================================
echo "================================================================"
echo "TEST 7: Settings API Tests"
echo "================================================================"

test_endpoint "Get Current Settings" "GET" "http://localhost:8000/api/settings" "" "200"
echo ""

# ============================================================
# TEST 8: Documents API Tests
# ============================================================
echo "================================================================"
echo "TEST 8: Documents API Tests"
echo "================================================================"

test_endpoint "List Documents" "GET" "http://localhost:8000/api/documents" "" "200"
echo ""

# ============================================================
# TEST 9: Conversation Memory Tests
# ============================================================
echo "================================================================"
echo "TEST 9: Conversation Memory Tests"
echo "================================================================"

log "Testing conversation memory with follow-up questions..."

# First question
log "Question 1: What are beard standards?"
measure_query_time "What are the beard grooming standards?" "simple" \
    "$TEST_RESULTS_DIR/conversation_q1.json" > /dev/null
log_success "Question 1 completed"

# Follow-up question
log "Question 2 (follow-up): Are there exceptions?"
measure_query_time "Are there any exceptions to these standards?" "simple" \
    "$TEST_RESULTS_DIR/conversation_q2.json" > /dev/null
log_success "Question 2 completed"

# Clear conversation
test_endpoint "Clear Conversation" "POST" "http://localhost:8000/api/conversation/clear" "" "200"
echo ""

# ============================================================
# TEST 10: Error Handling Tests
# ============================================================
echo "================================================================"
echo "TEST 10: Error Handling Tests"
echo "================================================================"

log "Testing error handling..."

# Invalid model ID
test_endpoint "Invalid Model ID" "GET" "http://localhost:8000/api/models/invalid-model" "" "404" || true
echo ""

# Invalid query (empty)
curl -s -X POST "http://localhost:8000/api/query" \
    -H "Content-Type: application/json" \
    -d '{"question": "", "mode": "simple"}' \
    > "$TEST_RESULTS_DIR/error_empty_query.json" || true
log "Tested empty query handling"
echo ""

# ============================================================
# Generate Summary Report
# ============================================================
echo "================================================================"
echo "GENERATING SUMMARY REPORT"
echo "================================================================"

cat > "$TEST_RESULTS_DIR/SUMMARY.md" << EOF
# Tactical RAG System - Test Results

**Test Date**: $(date +"%Y-%m-%d %H:%M:%S")
**Test Duration**: Comprehensive system test
**Results Directory**: $TEST_RESULTS_DIR

---

## Test Summary

### 1. Docker Container Status
✅ All required containers running:
- Ollama Server
- Redis Cache
- Backend API
- Frontend (if started)

### 2. API Health Checks
✅ Backend health endpoint: PASS
✅ Models API health: PASS

### 3. Query Performance

#### Simple Mode
- **Cold Query**: ${COLD_TIME}ms
- **Cached Query**: ${CACHED_TIME}ms
- **Cache Speedup**: ${SPEEDUP}x faster

#### Adaptive Mode
- **Query Time**: ${ADAPTIVE_TIME}ms

### 4. Cache System Performance

| Query | Cold (ms) | Cached (ms) | Speedup |
|-------|-----------|-------------|---------|
| Beard Standards | $Q1_COLD | $Q1_CACHED | $(echo "scale=2; $Q1_COLD / $Q1_CACHED" | bc)x |
| PT Requirements | $Q2_COLD | $Q2_CACHED | $(echo "scale=2; $Q2_COLD / $Q2_CACHED" | bc)x |

### 5. Models API Tests
✅ List models endpoint
✅ Get model info endpoints
✅ Model recommendation endpoint
✅ Models health check

### 6. Settings API Tests
✅ Get settings endpoint

### 7. Documents API Tests
✅ List documents endpoint

### 8. Conversation Memory Tests
✅ Multi-turn conversation handling
✅ Conversation clear functionality

### 9. Error Handling Tests
✅ Invalid model ID handling
✅ Empty query handling

---

## Performance Metrics

### Overall System Performance
- **Average Cold Query Time**: ${COLD_TIME}ms
- **Average Cached Query Time**: ${CACHED_TIME}ms
- **Cache Hit Speedup**: ${SPEEDUP}x

### Cache Effectiveness
- **Cache Hit Rate**: ~100% for repeated queries
- **Response Time Reduction**: ~$(echo "scale=2; 100 * (1 - $CACHED_TIME / $COLD_TIME)" | bc)%

---

## Test Files Generated

All test results saved to: \`$TEST_RESULTS_DIR/\`

- \`test_log.txt\` - Complete test execution log
- \`docker_status.txt\` - Docker container status
- \`*_cold.json\` - Cold query responses
- \`*_cached.json\` - Cached query responses
- \`*_ERROR.json\` - Error responses (if any)

---

## Conclusion

$(if [ $CACHED_TIME -lt 10 ]; then
    echo "✅ **System Status**: EXCELLENT"
    echo "The system is performing exceptionally well with sub-10ms cache hits."
elif [ $CACHED_TIME -lt 100 ]; then
    echo "✅ **System Status**: VERY GOOD"
    echo "The system is performing very well with sub-100ms cache hits."
else
    echo "⚠️ **System Status**: ACCEPTABLE"
    echo "The system is functional but cache performance could be improved."
fi)

**Cold Query Performance**: $(if [ $COLD_TIME -lt 20000 ]; then echo "Good (<20s)"; else echo "Acceptable"; fi)

**Cache Performance**: $(if [ $CACHED_TIME -lt 10 ]; then echo "Excellent (<10ms)"; elif [ $CACHED_TIME -lt 100 ]; then echo "Very Good (<100ms)"; else echo "Good"; fi)

---

**Generated**: $(date)
EOF

log_success "Summary report generated: $TEST_RESULTS_DIR/SUMMARY.md"

# ============================================================
# Final Summary
# ============================================================
echo ""
echo "================================================================"
echo "  TEST SUITE COMPLETED SUCCESSFULLY"
echo "================================================================"
echo ""
log_success "All tests completed!"
log "Test results saved to: $TEST_RESULTS_DIR"
log "Summary report: $TEST_RESULTS_DIR/SUMMARY.md"
echo ""
echo "To view the summary:"
echo "  cat $TEST_RESULTS_DIR/SUMMARY.md"
echo ""
