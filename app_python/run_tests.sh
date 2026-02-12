#!/bin/bash
echo "🧪 Running DevOps Info Service Tests"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Test Suite: DevOps Info Service ===${NC}"

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Not in virtual environment${NC}"
    read -p "Continue? (y/n): " choice
    [[ $choice != "y" ]] && exit 1
fi

# Install test dependencies
echo -e "\n1. Installing test dependencies..."
pip install pytest pytest-cov httpx pylint black ruff > /dev/null 2>&1

# Run linter
echo -e "\n2. Running linter (pylint)..."
pylint app.py --exit-zero

# Run formatter check
echo -e "\n3. Checking code formatting (black)..."
black app.py --check --diff

# Run security linter
echo -e "\n4. Running security check (bandit)..."
pip install bandit > /dev/null 2>&1
bandit -r app.py -f json 2>/dev/null | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    issues = data.get('metrics', {}).get('_totals', {}).get('issues', 0)
    if issues == 0:
        print('✅ No security issues found')
    else:
        print(f'⚠️  Found {issues} security issues')
except:
    print('⚠️  Could not parse bandit output')
"

# Run tests
echo -e "\n5. Running unit tests (pytest)..."
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Check test results
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi

# Generate coverage report
echo -e "\n6. Generating coverage report..."
python -m pytest tests/ --cov=app --cov-report=html --cov-report=xml --quiet

echo -e "\n${GREEN}=== Test Summary ==="
echo "✅ Linting completed"
echo "✅ Formatting checked"
echo "✅ Security analyzed"
echo "✅ Tests executed"
echo "✅ Coverage generated"
echo -e "====================${NC}"

echo -e "\n📊 Coverage report available at: htmlcov/index.html"
echo "📈 XML coverage report: coverage.xml"