#!/bin/bash
# SCP-ECG Tools Quick Start Script

echo "================================"
echo " SCP-ECG Tools Quick Start"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✓ Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Run tests
echo ""
echo "Running tests..."
python tests/test_scp_tools.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ All tests passed"
else
    echo "✗ Some tests failed - please check"
fi

# Check data files
echo ""
echo "Checking data files..."
original_count=$(ls data/original/*.SCP 2>/dev/null | wc -l)
anon_count=$(ls data/anonymized/*.SCP 2>/dev/null | wc -l)
echo "✓ Original files: $original_count"
echo "✓ Anonymized files: $anon_count"

# Demo commands
echo ""
echo "================================"
echo " Ready to use! Try these:"
echo "================================"
echo ""
echo "1. View ECG information:"
echo "   python scp_tools.py info data/original/ECG_20170504_163507_123456789.SCP"
echo ""
echo "2. Visualize ECG (requires display):"
echo "   python scp_tools.py view data/original/ECG_20170504_163507_123456789.SCP"
echo ""
echo "3. Anonymize a file:"
echo "   python scp_tools.py anonymize data/original/ECG_20170504_163507_123456789.SCP"
echo ""
echo "4. Get help:"
echo "   python scp_tools.py --help"
echo ""
echo "================================"