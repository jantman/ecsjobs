#!/bin/bash
if [ $# -eq 0 ]; then
    ECODE=0
else
    ECODE=1
fi
echo "this is a script pulled from GitHub"
>&2 echo "it will exit $ECODE (stderr)"
exit $ECODE
