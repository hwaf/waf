#!/bin/bash

D=$PWD
pushd ../..
./waf-light configure build --tools=$D/hlib.py --prelude=$'\tfrom waflib.extras import hlib\n\thlib.start(cwd, VERSION, wafdir)\n\tsys.exit(0)'
popd
cp ../../waf h-waf

