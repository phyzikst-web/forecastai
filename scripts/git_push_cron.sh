#!/bin/bash
# Move to the repository directory
cd /Users/phyzik/Desktop/forecastai

# Remove any leftover git index lock files to prevent stuck processes
rm -f .git/index.lock

# Push any locally committed changes to GitHub
git push origin main >> /Users/phyzik/Desktop/forecastai/scripts/git_push_cron.log 2>&1
