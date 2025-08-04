#!/bin/bash

# --- Script to safely remove dosbox-staging and its orphaned dependencies ---

# This script first uninstalls the main package, then identifies and removes
# any dependencies that are no longer needed by any other installed Homebrew packages.

# WARNING: This script is intended to be run interactively. It will provide
# a list of dependencies to remove. Proceed with caution.
# This script performs the same function as `brew autoremove`, but
# provides more verbose output to help you understand what's happening.

# Step 1: Uninstall the main dosbox-staging package.
# This command only removes the main package, not its dependencies.
echo "--> Uninstalling dosbox-staging..."
brew uninstall dosbox-staging

# Check if the uninstallation was successful
if [ $? -eq 0 ]; then
    echo "dosbox-staging has been successfully uninstalled."
else
    echo "Failed to uninstall dosbox-staging. It may not be installed."
    exit 1
fi

echo ""
echo "--------------------------------------------------------"
echo "Step 2: Identifying orphaned dependencies."
echo "The next command will list all packages that were installed as"
echo "dependencies and are no longer required by any other installed package."
echo "This is a dry run of 'brew autoremove'."
echo "--------------------------------------------------------"
echo ""

# Use brew autoremove with --dry-run to list what would be removed
# We'll capture the output to a variable for later use
orphans=$(brew autoremove --dry-run)

if [ -z "$orphans" ]; then
    echo "No orphaned packages found. All of dosbox-staging's dependencies"
    echo "are still being used by other software on your system."
    echo ""
    echo "This is why 'brew autoremove' had no output when you ran it."
    echo "The safest action is to stop here."
    exit 0
else
    echo "The following packages can be safely removed:"
    echo "$orphans"
    echo ""
    read -p "Do you want to proceed with removing these packages? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Step 3: Remove the identified orphaned dependencies.
        # This is the actual execution of the `brew autoremove` command.
        echo "--> Removing orphaned dependencies..."
        brew autoremove
        echo "Orphaned dependencies have been removed."
    else
        echo "Aborting. No changes were made."
    fi
fi

