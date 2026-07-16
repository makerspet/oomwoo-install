#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Unit-test enable_updates_pocket() from install_oomwoo_runtime_jazzy.sh.
#
# ROS 2 debs are built against a current Ubuntu (release + updates). An image
# carrying only <codename> and <codename>-security leaves ROS dependencies
# unsatisfiable. The installer repairs that; these cases pin the behaviour:
#
#   1. a broken image gains -updates on the ARCHIVE stanza only
#   2. the SECURITY stanza is never touched (updates must not come from the
#      security URI)
#   3. running twice does not duplicate the suite
#   4. an already-correct file is left byte-for-byte alone
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../ubuntu/install_oomwoo_runtime_jazzy.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# Pull in the real function; stub the parts that would touch the machine.
sudo() { "$@"; }
apt() { :; }
eval "$(sed -n '/^enable_updates_pocket()/,/^}/p' "$SCRIPT")"

make_broken() {
  cat > "$1" <<'EOF'
Types: deb
URIs: http://ports.ubuntu.com/ubuntu-ports/
Suites: noble
Components: main restricted universe multiverse

Types: deb
URIs: http://ports.ubuntu.com/ubuntu-ports/
Suites: noble-security
Components: main restricted universe multiverse
EOF
}

# --- 1 + 2: repairs the archive stanza, leaves the security stanza alone ------
make_broken "$WORK/broken.sources"
OOMWOO_APT_SOURCES="$WORK/broken.sources" enable_updates_pocket >/dev/null

grep -qE '^Suites: noble noble-updates$' "$WORK/broken.sources" \
  || fail "archive stanza did not gain noble-updates: $(grep '^Suites:' "$WORK/broken.sources")"
grep -qE '^Suites: noble-security$' "$WORK/broken.sources" \
  || fail "security stanza was modified (updates must not come from the security URI)"
echo "ok  1+2  archive stanza repaired, security stanza untouched"

# --- 3: idempotent -----------------------------------------------------------
OOMWOO_APT_SOURCES="$WORK/broken.sources" enable_updates_pocket >/dev/null
[ "$(grep -c 'noble-updates' "$WORK/broken.sources")" -eq 1 ] \
  || fail "second run duplicated noble-updates"
echo "ok  3     idempotent"

# --- 4: no-op on an already-correct file -------------------------------------
cat > "$WORK/good.sources" <<'EOF'
Types: deb
URIs: http://ports.ubuntu.com/ubuntu-ports/
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse

Types: deb
URIs: http://ports.ubuntu.com/ubuntu-ports/
Suites: noble-security
Components: main restricted universe multiverse
EOF
cp "$WORK/good.sources" "$WORK/good.orig"
OOMWOO_APT_SOURCES="$WORK/good.sources" enable_updates_pocket >/dev/null
diff -q "$WORK/good.orig" "$WORK/good.sources" >/dev/null \
  || fail "an already-correct sources file was modified"
echo "ok  4     no-op on a healthy file"

echo "PASS: enable_updates_pocket"
