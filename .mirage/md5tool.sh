#!/bin/bash
# Jordan Blackadar <blackadar@photodiagnostic.com>
# This script generates md5sums for a software release, or compares generated to actual md5sums.
# Must be run inside a folder of rpms.

md5regex='\|(.*) (.*)\|'

while getopts "gc" flag; do
    case "${flag}" in
        g)
          for f in *.rpm; do
              echo "|$(md5sum "$f")|" | tee -a md5.txt
            done
          ;;
        c)
          mapfile -t lines < md5.txt
            for line in "${lines[@]}"; do
              [[ $line =~ $md5regex ]]
              exp_hash="${BASH_REMATCH[1]}"
              file="${BASH_REMATCH[2]}"
              real_hash=($(md5sum "$file"))
              if [ $exp_hash == $real_hash ]; then
                echo "OK $file"
              else
                echo "MISMATCH $file (actual $real_hash expected $exp_hash)"
              fi
            done
          ;;
        *)
          echo "Usage: md5tool.sh <-g> <-c>"
          echo "-g Generate md5.txt"
          echo "-c Check md5.txt matches present files"
          ;;
    esac
done
