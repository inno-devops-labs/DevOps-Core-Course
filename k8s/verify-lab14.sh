#!/bin/bash
# LAB14 — File Verification Script
# Run this to verify all required files have been created

echo "======================================"
echo "LAB14 — File Verification"
echo "======================================"
echo ""

# Change to project directory
cd "$(dirname "$0")/.." || exit 1

echo "📁 Checking Helm Chart Templates..."
echo ""

files_ok=0
files_total=0

check_file() {
    local file=$1
    local desc=$2
    files_total=$((files_total + 1))
    if [ -f "$file" ]; then
        local lines=$(wc -l < "$file")
        echo "✅ $desc"
        echo "   Location: $file"
        echo "   Lines: $lines"
        files_ok=$((files_ok + 1))
    else
        echo "❌ $desc"
        echo "   Missing: $file"
    fi
    echo ""
}

# Check templates
check_file "k8s/devops-info-python/templates/rollout-canary.yaml" "Canary Rollout Template"
check_file "k8s/devops-info-python/templates/rollout-bluegreen.yaml" "Blue-Green Rollout Template"
check_file "k8s/devops-info-python/templates/service-canary.yaml" "Canary Service"
check_file "k8s/devops-info-python/templates/service-preview.yaml" "Preview Service"
check_file "k8s/devops-info-python/templates/analysistemplate.yaml" "Analysis Template"

echo "📄 Checking Documentation Files..."
echo ""

# Check documentation
check_file "k8s/ROLLOUTS.md" "Main Lab Documentation"
check_file "k8s/LAB14-COMMANDS.md" "Terminal Commands Guide"
check_file "k8s/LAB14-IMPLEMENTATION-SUMMARY.md" "Implementation Summary"
check_file "k8s/LAB14-QUICK-START.md" "Quick Start Guide"
check_file "k8s/LAB14-DELIVERABLES-INDEX.md" "Deliverables Index"

echo "⚙️  Checking Configuration..."
echo ""

if grep -q "rollout:" "k8s/devops-info-python/values.yaml"; then
    echo "✅ values.yaml updated with rollout section"
    files_ok=$((files_ok + 1))
else
    echo "❌ values.yaml missing rollout configuration"
fi
files_total=$((files_total + 1))
echo ""

echo "📊 Verification Summary"
echo "======================================"
echo "Files Created: $files_ok / $files_total"

if [ $files_ok -eq $files_total ]; then
    echo ""
    echo "✅ All files created successfully!"
    echo ""
    echo "Next Steps:"
    echo "1. Read: k8s/LAB14-QUICK-START.md"
    echo "2. Run: commands from PART 0 onwards"
    echo "3. Capture: screenshots to k8s/screenshots/lab14/"
    echo "4. Verify: completion with checklist in k8s/ROLLOUTS.md"
    exit 0
else
    echo ""
    echo "❌ Some files are missing. Please review the output above."
    exit 1
fi
