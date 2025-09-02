#!/bin/bash
# scripts/update-submodules.sh

# Ensure script fails on any error
set -e

echo "🔄 Updating Git submodules..."

# Update all submodules to latest commit on their tracked branch
git submodule update --remote

# Check if there are any changes
if git diff --quiet --ignore-submodules; then
    echo "✅ All submodules are up to date"
else
    echo "📝 Submodules updated. Please review changes:"
    git status --porcelain
    echo ""
    echo "💡 To commit the updates:"
    echo "   git add ."
    echo "   git commit -m 'Update submodules'"
fi
