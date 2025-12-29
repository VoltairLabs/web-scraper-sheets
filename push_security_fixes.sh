#!/bin/bash
# Script to push security fixes to GitHub

cd /Users/avi/Downloads/web-scraper-sheets || exit 1

echo "Checking git status..."
git status

echo ""
echo "Removing setup_env.sh from git tracking (if it exists)..."
git rm --cached setup_env.sh 2>/dev/null || echo "setup_env.sh not tracked in git"

echo ""
echo "Staging security fixes..."
git add .gitignore QUICKSTART.md setup_env.sh.example 2>/dev/null

echo ""
echo "Checking what will be committed..."
git status

echo ""
echo "Committing security fixes..."
git commit -m "Security: Remove hardcoded SerpAPI token from codebase

- Remove hardcoded SerpAPI token from setup_env.sh and QUICKSTART.md
- Add setup_env.sh to .gitignore to prevent future leaks
- Add setup_env.sh.example as a template for users"

echo ""
echo "Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Security fixes pushed to GitHub!"

