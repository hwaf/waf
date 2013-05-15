#!/bin/bash

D=$PWD
pushd ../..
./waf-light configure build --tools=$D/hlib.py --prelude=$'\tfrom waflib.extras import hlib'
popd
cp ../../waf h-waf

