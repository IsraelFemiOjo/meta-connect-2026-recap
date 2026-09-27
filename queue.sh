#!/bin/bash
ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
cd "$ROOT"
while pgrep -f "shotA_blend.py -- r3d/A" > /dev/null; do sleep 5; done
mkdir -p r3d/B r3d/C r3d/E
python3 shotB_blend.py -- r3d/B 1 261 > /tmp/blB.log 2>&1
python3 shotC_blend.py -- r3d/C 1 97 > /tmp/blC.log 2>&1
python3 shotE_blend.py -- r3d/E 1 121 > /tmp/blE.log 2>&1
echo ALLDONE > /tmp/queue.done
