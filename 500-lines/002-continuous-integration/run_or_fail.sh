#!/bin/bash

# helper error function
# grabs first arg, removes from args list.
# executes next arg.
# if failure, write explanation to stderr,
# then exit with code of 1

run_or_fail() {
  local explanation=$1
  shift 1
  "$@"
  if [ $? != 0 ]; then
    echo $explanation 1>&2
    exit 1
  fi
}
