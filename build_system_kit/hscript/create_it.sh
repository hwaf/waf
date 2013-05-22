#!/bin/bash

D=$PWD
TOOLS="$D/hlib.py,batched_cc,compat,compat15,ocaml,go,cython,scala,erlang,cuda,gcj,boost,pep8,subprocess,parallel_debug"

pushd ../..
./waf-light configure build --tools=$TOOLS --prelude=$'\tfrom waflib.extras import hlib'
popd
cp ../../waf h-waf

