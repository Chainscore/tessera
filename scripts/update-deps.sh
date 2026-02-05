#!/bin/bash
# scripts/update-deps.sh - Update test-suites submodule to latest commit

# Ensure script fails on any error
set -e

echo "🔄 Updating test-suites submodule..."
echo ""

# Show what branch is being tracked
echo "📋 Tracked branch:"
git config -f .gitmodules --get-regexp 'submodule\..*\.path' | while read key path; do
    submodule_name="${key#submodule.}"
    submodule_name="${submodule_name%.path}"
    branch=$(git config -f .gitmodules --get "submodule.$submodule_name.branch" 2>/dev/null || echo "main (default)")
    echo "   $path: $branch"
done

echo ""

# Update submodule to latest commit on tracked branch
git submodule init
git submodule update --remote

if [ -d "test-suites" ]; then
    echo "   Updating test-suites nested submodules..."
    cd test-suites
    git submodule init
    git submodule update --remote --recursive
    cd ..
fi

# Check if there are any changes
if git diff --quiet --ignore-submodules; then
    echo "✅ Submodule is up to date"
else
    echo "📝 Submodule updated. Please review changes:"
    git status --porcelain
    echo ""
    echo "💡 To commit the updates:"
    echo "   git add ."
    echo "   git commit -m 'Update test-suites submodule to latest commit'"
    echo ""
    echo "🔍 To see what changed:"
    echo "   git submodule foreach 'git log --oneline HEAD~3..HEAD'"
fi
