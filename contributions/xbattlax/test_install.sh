#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$HERE/install.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE="$WORK/source"
WORKSPACE="$WORK/workspace"

git init -b main "$SOURCE" >/dev/null
git -C "$SOURCE" config user.name "OOMWOO installer test"
git -C "$SOURCE" config user.email "ci@example.invalid"

echo "release" > "$SOURCE/content.txt"
git -C "$SOURCE" add content.txt
git -C "$SOURCE" commit -m "release" >/dev/null
git -C "$SOURCE" tag v0.1.0
RELEASE_SHA="$(git -C "$SOURCE" rev-parse 'v0.1.0^{commit}')"

bash "$INSTALLER" \
  --workspace "$WORKSPACE" \
  --repository "$SOURCE" \
  --ref v0.1.0 \
  --skip-rosdep \
  --skip-build >/dev/null

CHECKOUT="$WORKSPACE/src/health-monitor"
[[ "$(git -C "$CHECKOUT" rev-parse HEAD)" == "$RELEASE_SHA" ]] ||
  fail "initial install did not resolve v0.1.0"
if git -C "$CHECKOUT" symbolic-ref -q HEAD >/dev/null; then
  fail "release checkout must use detached HEAD"
fi

echo "main moved" >> "$SOURCE/content.txt"
git -C "$SOURCE" add content.txt
git -C "$SOURCE" commit -m "move main" >/dev/null

bash "$INSTALLER" \
  --workspace "$WORKSPACE" \
  --repository "$SOURCE" \
  --ref v0.1.0 \
  --skip-rosdep \
  --skip-build >/dev/null
[[ "$(git -C "$CHECKOUT" rev-parse HEAD)" == "$RELEASE_SHA" ]] ||
  fail "reinstall drifted away from v0.1.0"

echo "local edit" >> "$CHECKOUT/content.txt"
if bash "$INSTALLER" \
  --workspace "$WORKSPACE" \
  --repository "$SOURCE" \
  --ref v0.1.0 \
  --skip-rosdep \
  --skip-build >"$WORK/dirty.out" 2>&1; then
  fail "installer overwrote a dirty checkout"
fi
grep -q "has local changes" "$WORK/dirty.out" ||
  fail "dirty-checkout failure was not explained"

echo "PASS: health-monitor installer pinning and dirty-checkout guard"
