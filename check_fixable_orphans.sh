#!/bin/bash
# Check for high-confidence fixable orphan refs

echo "=== Checking for High-Confidence Fixable Orphans ==="
echo ""

# Counter
FIXABLE=0

# 1. ELITEA-2392 - has _test suffix that shouldn't be there
echo "1. ELITEA-2392 (Settings AI Providers):"
echo "   Orphan: test_ai_providers_page_sections_load_without_error_test"
grep -r "def test_ai_providers_page_sections_load_without_error[^_]" automation/tests/ui/settings/ --include="*.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ FIXABLE: Test exists without _test suffix"
    ((FIXABLE++))
else
    echo "   ❌ Not found"
fi
echo ""

# 2. ELITEA-1814 - parameterized test base exists
echo "2. ELITEA-1814 (Artifacts Bucket Validation):"
echo "   Orphan: test_bucket_name_validation_rejects_invalid_format (no params)"
grep -r "def test_bucket_name_validation_rejects_invalid_format" automation/tests/ui/artifacts/ --include="*.py" 2>/dev/null | head -1
if [ $? -eq 0 ]; then
    echo "   ✅ FIXABLE: Base test exists with parameters"
    ((FIXABLE++))
else
    echo "   ❌ Not found"
fi
echo ""

# 3. Check for "move_conversation" tests - might have been consolidated
echo "3. ELITEA-2137/2138 (Move Conversation to Folder):"
grep -r "test_move_conversation" automation/tests/ui/chat/test_move_conversation_to_folder.py 2>/dev/null | grep "def " | head -3
FOUND=$(grep -r "test_move_conversation" automation/tests/ui/chat/test_move_conversation_to_folder.py 2>/dev/null | grep "def " | wc -l)
if [ $FOUND -gt 0 ]; then
    echo "   ℹ️  Found $FOUND move_conversation tests (check if consolidated)"
    if [ $FOUND -ge 2 ]; then
        echo "   ⚠️  POSSIBLY FIXABLE (2-4 refs could map to existing tests)"
    fi
fi
echo ""

# 4. Check conversation renaming tests
echo "4. Conversation Renaming (ELITEA-2099-2113):"
grep -r "test_rename_conversation" automation/tests/ui/chat/ --include="*.py" 2>/dev/null | grep "def " | wc -l
RENAME_FOUND=$(grep -r "test_rename_conversation" automation/tests/ui/chat/ --include="*.py" 2>/dev/null | grep "def " | wc -l)
echo "   Found $RENAME_FOUND rename_conversation tests"
if [ $RENAME_FOUND -gt 0 ]; then
    echo "   ⚠️  POSSIBLY FIXABLE (some refs might map to existing tests)"
fi
echo ""

# 5. Check folder tests
echo "5. Folder Management (ELITEA-2118-2147):"
grep -r "test.*folder" automation/tests/ui/chat/ --include="*.py" 2>/dev/null | grep "def " | wc -l
FOLDER_FOUND=$(grep -r "test.*folder" automation/tests/ui/chat/ --include="*.py" 2>/dev/null | grep "def " | wc -l)
echo "   Found $FOLDER_FOUND folder-related tests"
if [ $FOLDER_FOUND -gt 0 ]; then
    echo "   ⚠️  POSSIBLY FIXABLE (some refs might map to existing tests)"
fi
echo ""

# 6. Check hash search tests
echo "6. Hash Search (ELITEA-2206, 2469, 2470):"
grep -r "TestHashSearch" automation/tests/ui/chat/test_chat_interface.py 2>/dev/null
HASH_FOUND=$?
if [ $HASH_FOUND -eq 0 ]; then
    grep -r "def test.*hash" automation/tests/ui/chat/test_chat_interface.py 2>/dev/null | grep "def "
    HASH_COUNT=$(grep -r "def test.*hash" automation/tests/ui/chat/test_chat_interface.py 2>/dev/null | grep "def " | wc -l)
    echo "   Found $HASH_COUNT hash tests in TestHashSearch"
    if [ $HASH_COUNT -gt 0 ]; then
        echo "   ✅ FIXABLE: 2-3 refs likely map to existing hash search tests"
        ((FIXABLE+=2))
    fi
fi
echo ""

echo "=== SUMMARY ==="
echo "High-Confidence Fixable: $FIXABLE"
echo ""

