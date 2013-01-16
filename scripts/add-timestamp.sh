#!/bin/bash

scripts_dir=$(dirname "$0")

ts=$(git show --pretty=format:%ct HEAD | head -n 1)
date "+%Y-%m-%d %H:%M:%S %z" -d "1970-01-01 00:00 UTC $ts seconds" > $stamp

echo "GIT Revision: $(git rev-parse HEAD)" >> $stamp

res=$(sed -ne 's|^ref: refs/heads/||p' "$scripts_dir"/../.git/HEAD 2>/dev/null)
echo "GIT Branch: $res" >> $stamp



