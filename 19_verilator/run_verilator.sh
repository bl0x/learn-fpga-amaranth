#!/bin/bash

set -e

echo "Make sure:"
echo "  - you've compiled a design previously, so build/top.v exists"
echo "  - you've added the snippet.v to the 'top' module in build/top.v"
echo ""
read -n 1 -s -r -p "Press any key to continue or Ctrl-C to stop."

cd 19_verilator/.. || cd ../19_verilator/..

# generate C++ sources in 'obj_dir'
verilator \
	-DBENCH \
	-DBOARD_FREQ=12 \
	-Wno-fatal \
	--top-module soc \
	-cc -exe \
	19_verilator/sim_main.cpp \
	build/top.v

# compile C++ sources
make -C obj_dir -j8 -f Vsoc.mk

# run the simulation
./obj_dir/Vsoc
