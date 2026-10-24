#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${1:?Output executable path required}"
root=/srv/codex-hil-data/workspaces/rng-rpi
uhal="$root/experiments/upstream/ipbus-software/uhal"
deps="$root/build/uhal-deps/usr"
c++ -std=c++17 -O2 uhal_probe.cpp -o "$1" \
 -I"$uhal/uhal/include" -I"$uhal/log/include" -I"$uhal/grammars/include" -I"$deps/include" \
 -L"$uhal/uhal/lib" -L"$uhal/log/lib" -L"$uhal/grammars/lib" -L"$deps/lib/x86_64-linux-gnu" \
 -Wl,--disable-new-dtags,-rpath,"$uhal/uhal/lib:$uhal/log/lib:$uhal/grammars/lib:$deps/lib/x86_64-linux-gnu" \
 -lcactus_uhal_uhal -lcactus_uhal_log -lcactus_uhal_grammars -lboost_system -lboost_filesystem -lboost_regex -lboost_chrono -lpugixml -lpthread
