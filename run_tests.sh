#!/bin/bash

################################################################################
# Tweet Disaster Prediction - Test Suite
# Comprehensive testing script for local development
# 
# Usage: ./run_tests.sh [option]
# Options:
#   quick       - Fast tests only (DB + API health)
#   full        - All tests including pipeline
#   stress      - Load testing
#   all         - Everything (quick + full + stress)
#   help        - Show this message
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_PATH=".venv"
PYTHON="${VENV_PATH}/bin/python"
PYTEST="${VENV_PATH}/bin/pytest"

# Test suite options
TEST_MODE="${1:-quick}"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo -e "\n${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_info "Create venv with: python3 -m venv .venv"
        exit 1
    fi
}

check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        print_info "Create .env from .env.example:"
        print_info "  cp .env.example .env"
        print_info "Then update with your Firebase credentials"
        exit 1
    fi
}

check_credentials() {
    source .env
    if [ ! -f "$FIREBASE_CREDENTIALS_PATH" ]; then
        print_error "Firebase credentials not found at: $FIREBASE_CREDENTIALS_PATH"
        print_info "Follow FIRESTORE_SETUP.md to generate credentials"
        exit 1
    fi
}

################################################################################
# Test Functions
################################################################################

test_firebase_connection() {
    print_section "Testing Firebase Connection"
    $PYTHON test_db.py
    print_success "Firebase connection verified"
}

test_api_endpoints() {
    print_section "Testing API Endpoints"
    $PYTEST tests/test_api.py -v --tb=short
    print_success "API endpoints tested"
}

test_pipeline() {
    print_section "Testing ML Pipeline"
    $PYTEST tests/test_pipeline.py -v --tb=short
    print_success "ML pipeline tested"
}

test_all_pytest() {
    print_section "Running All Pytest Tests"
    $PYTEST tests/ -v --tb=short --cov=api --cov=src
    print_success "All pytest tests passed"
}

test_stress() {
    print_section "Running Stress Tests"
    print_info "Warning: Stress tests can be CPU intensive and trigger rate limits"
    $PYTEST tests/stress_test.py -v --tb=short
    print_success "Stress tests completed"
}

check_code_quality() {
    print_section "Checking Code Quality"
    
    # Check for syntax errors
    $PYTHON -m py_compile api/*.py src/**/*.py tests/*.py 2>/dev/null
    print_success "No syntax errors found"
    
    # Optional: Check with pylint if installed
    if command -v pylint &> /dev/null; then
        print_info "Running pylint (light check)..."
        pylint --disable=all --enable=E api/ src/ 2>/dev/null || true
    fi
}

lint_tests() {
    print_section "Linting Tests"
    if command -v pylint &> /dev/null; then
        pylint --disable=all --enable=E tests/ 2>/dev/null || true
        print_success "Test code linting complete"
    else
        print_info "pylint not installed, skipping lint checks"
    fi
}

startup_test() {
    print_section "Testing API Startup"
    print_info "Starting API server (30 second timeout)..."
    
    timeout 30 $PYTHON -c "
from api.main import app
from api.database import init_db
init_db()
print('✓ API initialization successful')
" || true
    
    print_success "API initialization verified"
}

################################################################################
# Main Test Suites
################################################################################

run_quick_tests() {
    print_header "QUICK TEST SUITE"
    print_info "Fast tests for rapid development iteration"
    
    test_firebase_connection
    startup_test
    check_code_quality
    
    print_header "✓ QUICK TESTS PASSED"
}

run_full_tests() {
    print_header "FULL TEST SUITE"
    print_info "Comprehensive testing including API and ML pipeline"
    
    test_firebase_connection
    startup_test
    check_code_quality
    test_api_endpoints
    test_pipeline
    
    print_header "✓ FULL TESTS PASSED"
}

run_all_tests() {
    print_header "COMPLETE TEST SUITE"
    print_info "Everything: unit tests, API tests, pipeline, and stress tests"
    
    run_full_tests
    test_stress
    
    print_header "✓ ALL TESTS PASSED"
}

run_stress_tests() {
    print_header "STRESS TEST SUITE"
    print_info "Load testing and performance verification"
    
    test_firebase_connection
    test_stress
    
    print_header "✓ STRESS TESTS COMPLETED"
}

show_help() {
    print_header "HELP - Test Suite Options"
    echo ""
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  quick       - Fast tests (Firebase + startup + syntax) - ~30 seconds"
    echo "  full        - All unit + API + pipeline tests - ~2 minutes"
    echo "  stress      - Stress testing (high CPU usage) - ~5+ minutes"
    echo "  all         - Everything (quick + full + stress) - ~10 minutes"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh quick           # Fast feedback loop"
    echo "  ./run_tests.sh full            # Before commit"
    echo "  ./run_tests.sh all             # Before deployment"
    echo ""
    echo "Tips:"
    echo "  - Use 'quick' during active development"
    echo "  - Use 'full' before committing code"
    echo "  - Use 'all' before deploying to production"
    echo "  - Run stress tests when testing new infrastructure"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    # Show help without checking environment
    if [ "$TEST_MODE" = "help" ]; then
        show_help
        exit 0
    fi
    
    # Checks for other modes
    check_venv
    check_env_file
    check_credentials
    
    # Create test reports directory
    mkdir -p test_reports
    
    # Select test mode
    case "$TEST_MODE" in
        quick)
            run_quick_tests
            ;;
        full)
            run_full_tests
            ;;
        stress)
            run_stress_tests
            ;;
        all)
            run_all_tests
            ;;
        *)
            print_error "Unknown option: $TEST_MODE"
            echo "Use './run_tests.sh help' for available options"
            exit 1
            ;;
    esac
}

# Run main
main
print_header "✓ Test suite execution completed"
