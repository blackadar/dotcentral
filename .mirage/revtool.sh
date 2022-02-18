#!/bin/bash
# Jordan Blackadar <blackadar@photodiagnostic.com>
# This script compares main and the release branch to detect changes in units and packages.
# If the unit has changed, but the revision number has not, the script will error.
# Must be run on a git checkout of the repository, with access to the repository.

units=("x_ray" "mscp" "motor" "imaging" "data_handler" "das" "Control/BCC" "Control/DCC" "Control/RCC"
       "ckct_common" "drivers" "tools")
ok=true

for unit in "${units[@]}"; do
  changes=$(git diff origin/release..origin/main -- "$unit" | wc -l)
  version_changed=$(git diff origin/release..origin/main -- "$unit"/CMakeLists.txt | grep -c "VERSION")

  if [ "$changes" -gt 0 ] && [ "$version_changed" -lt 1 ]; then
    echo "$unit has changes on main not in release, but does not have a changed version number!"
    ok=false
    fi
done

if $ok; then
  exit 0
        else
  exit 1
fi
