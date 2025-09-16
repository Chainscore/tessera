#!/bin/bash
# scripts/update-deps.sh - Update all Git submodules to latest commits on their tracked branches

# Ensure script fails on any error
set -e

echo "🔄 Updating Git submodules..."
echo ""

# Show what branches are being tracked
echo "📋 Tracked branches:"
git config -f .gitmodules --get-regexp 'submodule\..*\.path' | while read key path; do
    submodule_name="${key#submodule.}"
    submodule_name="${submodule_name%.path}"
    branch=$(git config -f .gitmodules --get "submodule.$submodule_name.branch" 2>/dev/null || echo "main (default)")
    echo "   $path: $branch"
done

echo ""

# Update all submodules to latest commit on their tracked branch
git submodule init
git submodule update --remote

if [ -d "deps/test-suites" ]; then
    echo "   Updating test-suites submodules..."
    cd deps/test-suites
    git submodule init 
    git submodule update --remote --recursive
    cd ../..
fi

# Check if there are any changes
if git diff --quiet --ignore-submodules; then
    echo "✅ All submodules are up to date"
else
    echo "📝 Submodules updated. Please review changes:"
    git status --porcelain
    echo ""
    echo "💡 To commit the updates:"
    echo "   git add ."
    echo "   git commit -m 'Update submodules to latest commits'"
    echo ""
    echo "🔍 To see what changed in each submodule:"
    echo "   git submodule foreach 'git log --oneline HEAD~3..HEAD'"
fi
