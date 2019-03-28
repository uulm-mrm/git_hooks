#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: remove_hooks.sh /path/to/repository" >&2
  exit 1
fi
cd $1 || exit 2
find . -name ".git" -type d | xargs -n1 -I _DIR_ find _DIR_ -name "*.config.yaml" -exec rm {} \;                
find . -name ".git" -type d | xargs -n1 -I _DIR_ find _DIR_ -name "pre-commit" -exec rm {} \;                   
find . -name "run_hooks" -exec rm {} \;                                                                  
