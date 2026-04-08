#!/usr/bin/env bash
# release.sh — bump version, tag, compute SHA256, update Homebrew tap formula
#
# Usage:   ./release.sh <version>
# Example: ./release.sh 5.2
#
# Assumes:
#   - All code changes and changelog are committed and on master
#   - Working tree is clean
#   - Remote is 'origin'
#   - Tap repo lives at TAP_DIR (default: sibling directory homebrew-rp)

set -euo pipefail

VERSION="${1:?Usage: $0 <version>}"
TAG="v${VERSION}"
REPO_URL="https://github.com/rtulke/rp"
TARBALL_URL="${REPO_URL}/archive/refs/tags/${TAG}.tar.gz"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAP_DIR="${TAP_DIR:-${SCRIPT_DIR}/../homebrew-rp}"

# -----------------------------------------------------------------------
# Preflight checks
# -----------------------------------------------------------------------

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: working tree is dirty — commit or stash changes first." >&2
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "${CURRENT_BRANCH}" != "master" ]]; then
    echo "Error: not on master (currently on '${CURRENT_BRANCH}')." >&2
    exit 1
fi

if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "Error: tag ${TAG} already exists." >&2
    exit 1
fi

if [[ ! -d "${TAP_DIR}/.git" ]]; then
    echo "Error: tap repo not found at '${TAP_DIR}'." >&2
    echo "  Clone or create it first, or set TAP_DIR=/path/to/homebrew-rp" >&2
    exit 1
fi

if [[ -n "$(git -C "${TAP_DIR}" status --porcelain)" ]]; then
    echo "Error: tap repo at '${TAP_DIR}' has uncommitted changes." >&2
    exit 1
fi

# -----------------------------------------------------------------------
# 1. Update VERSION in rp.py
# -----------------------------------------------------------------------

echo "→ Updating VERSION in rp.py to ${VERSION}"
sed -i '' "s/^VERSION = '[^']*'/VERSION = '${VERSION}'/" rp.py

# -----------------------------------------------------------------------
# 2. Commit version bump
# -----------------------------------------------------------------------

git add rp.py
git commit -m "Bump version to ${VERSION}"

# -----------------------------------------------------------------------
# 3. Create tag and push branch + tag
# -----------------------------------------------------------------------

echo "→ Creating tag ${TAG} and pushing"
git tag "${TAG}"
git push origin master "${TAG}"

# -----------------------------------------------------------------------
# 4. Compute SHA256 (retry until GitHub serves the tarball)
# -----------------------------------------------------------------------

echo "→ Waiting for GitHub tarball (up to 60 s)..."
SHA256=""
TMPFILE=$(mktemp)

for i in $(seq 1 12); do
    if curl -sfL -o "${TMPFILE}" "${TARBALL_URL}"; then
        SHA256=$(shasum -a 256 "${TMPFILE}" | awk '{print $1}')
        break
    fi
    echo "  attempt ${i}/12 — not yet available, retrying in 5 s..."
    sleep 5
done

rm -f "${TMPFILE}"

if [[ -z "${SHA256}" ]]; then
    echo "" >&2
    echo "Error: could not download tarball after 12 attempts." >&2
    echo "Compute SHA256 manually and update the tap formula:" >&2
    echo "  curl -sL ${TARBALL_URL} | shasum -a 256" >&2
    exit 1
fi

echo "  SHA256: ${SHA256}"

# -----------------------------------------------------------------------
# 5. Update Homebrew tap formula
# -----------------------------------------------------------------------

echo "→ Updating tap repo at ${TAP_DIR}"
sed -i '' "s|url \"[^\"]*\"|url \"${TARBALL_URL}\"|"  "${TAP_DIR}/Formula/rp.rb"
sed -i '' "s|sha256 \"[^\"]*\"|sha256 \"${SHA256}\"|" "${TAP_DIR}/Formula/rp.rb"
sed -i '' "s|version \"[^\"]*\"|version \"${VERSION}\"|" "${TAP_DIR}/Formula/rp.rb"

git -C "${TAP_DIR}" add Formula/rp.rb
git -C "${TAP_DIR}" commit -m "Update to ${TAG}"
git -C "${TAP_DIR}" push origin master

# -----------------------------------------------------------------------

echo ""
echo "✓ Release ${TAG} complete."
echo ""
echo "  Main repo : ${REPO_URL}"
echo "  Tap repo  : $(git -C "${TAP_DIR}" remote get-url origin 2>/dev/null || echo "${TAP_DIR}")"
echo ""
echo "Install / upgrade with:"
echo "  brew tap rtulke/rp"
echo "  brew install rp"
echo ""
echo "Or to upgrade an existing install:"
echo "  brew update && brew upgrade rp"
