#! /bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: init.sh [PATH_TO_REPO_ROOT]" >&2
  exit 1
fi

HOOKSPATH="$( cd "$(dirname "$0")" ; pwd -P )"
GIT_DIR=`readlink -f $(git rev-parse --git-dir)`
REPOPATH=`realpath "$1"`
PROJECT_NAME=${REPOPATH##*/}
HOOKSPATH_REL=`realpath --relative-to="$REPOPATH" "$HOOKSPATH"`

if [ -f "$REPOPATH/CMakeLists.txt" ]; then
  echo "Folder already contains CMakeLists.txt!" >&2
  exit 1
fi

cat <<EOF >"$REPOPATH/CMakeLists.txt"
cmake_minimum_required(VERSION 2.8.3)
project($PROJECT_NAME)

add_subdirectory("$HOOKSPATH_REL" ".hooks")
create_git_hook()
EOF

SCRIPT_PATH=$REPOPATH/configure_hooks.sh
cat <<EOF >"$SCRIPT_PATH"
#!/bin/bash
CURDIR="\$( cd "\$(dirname "\$0")" ; pwd -P )"
TMP_DIR=/tmp/.git_hooks_build/$PROJECT_NAME
echo -n "Configuring hooks..."
rm -rf "\$TMP_DIR" && \\
  mkdir -p "\$TMP_DIR" && \\
  cd "\$TMP_DIR" && \\
  cmake "\$CURDIR" >/dev/null && echo " done."
EOF

chmod +x "$SCRIPT_PATH" && "$SCRIPT_PATH"
