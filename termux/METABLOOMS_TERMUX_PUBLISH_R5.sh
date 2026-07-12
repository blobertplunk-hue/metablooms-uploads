#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

# MetaBlooms OS R5 one-command Termux release publisher.
# Safe to rerun: it replaces only the two canonical assets on tag metablooms-os-r5.

REPO="${METABLOOMS_RELEASE_REPO:-blobertplunk-hue/metablooms-os-runtime}"
TAG="${METABLOOMS_RELEASE_TAG:-metablooms-os-r5}"
TARGET_BRANCH="${METABLOOMS_RELEASE_TARGET:-main}"
EXPECTED_SHA="5866f9754b922c77653cd0745fe27bb729902c4332b43f542221d6ba7c823c2b"
EXPECTED_SIZE="170394097"
CANONICAL_NAME="METABLOOMS_OS_STAGE071N_V4_R5_REPAIRED_CANDIDATE_20260711T1518.tar.zst"
SIDECAR_NAME="${CANONICAL_NAME}.sha256"
TITLE="MetaBlooms OS R5"
ARCHIVE_OVERRIDE="${METABLOOMS_ARCHIVE:-}"
DRY_RUN=0

while (($#)); do
  case "$1" in
    --archive)
      [[ $# -ge 2 ]] || { printf 'ERROR: --archive requires a path\n' >&2; exit 2; }
      ARCHIVE_OVERRIDE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      cat <<'HELP'
Usage: bash METABLOOMS_TERMUX_PUBLISH_R5.sh [--archive PATH] [--dry-run]

Without options, the script finds the verified R5 archive in Android Downloads,
installs required Termux packages, opens GitHub browser authentication if needed,
and creates or updates release tag metablooms-os-r5.
HELP
      exit 0
      ;;
    *)
      printf 'ERROR: unknown option: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_DIR="${HOME}/metablooms-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/metablooms-r5-release-${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

fail() {
  printf '\nFAILED: %s\nLog: %s\n' "$*" "$LOG_FILE" >&2
  exit 2
}

on_error() {
  local rc=$?
  printf '\nFAILED at line %s (exit %s).\nLog: %s\n' "$1" "$rc" "$LOG_FILE" >&2
  exit "$rc"
}
trap 'on_error "$LINENO"' ERR

step() { printf '\n==> %s\n' "$*"; }

step "MetaBlooms OS R5 publisher starting"
printf 'Repository: %s\nTag: %s\n' "$REPO" "$TAG"

if [[ "${PREFIX:-}" != *com.termux* ]] && [[ "${METABLOOMS_ALLOW_NON_TERMUX_TEST:-0}" != "1" ]]; then
  fail "This script must be run inside Termux."
fi

step "Installing required Termux packages"
if [[ "${METABLOOMS_SKIP_PACKAGE_INSTALL:-0}" != "1" ]]; then
  command -v pkg >/dev/null 2>&1 || fail "Termux package manager 'pkg' is unavailable."
  if ! pkg install -y gh coreutils findutils; then
    step "Refreshing Termux package indexes and retrying"
    pkg update -y
    pkg install -y gh coreutils findutils
  fi
fi
for cmd in gh sha256sum stat find cmp; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Required command was not installed: $cmd"
done

# Build a bounded list of locations. No recursive scan of the whole phone.
declare -a SEARCH_DIRS=()
add_dir() {
  local d="$1"
  [[ -n "$d" && -d "$d" && -r "$d" ]] || return 0
  local existing
  for existing in "${SEARCH_DIRS[@]:-}"; do
    [[ "$existing" == "$d" ]] && return 0
  done
  SEARCH_DIRS+=("$d")
}
add_dir "$PWD"
DOWNLOAD_ACCESS=0
add_download_dir() {
  local before="${#SEARCH_DIRS[@]}"
  add_dir "$1"
  if ((${#SEARCH_DIRS[@]} > before)); then
    DOWNLOAD_ACCESS=1
  fi
  return 0
}
add_download_dir "${HOME}/storage/downloads"
if [[ -n "${EXTERNAL_STORAGE:-}" ]]; then
  add_download_dir "${EXTERNAL_STORAGE}/Download"
fi
add_download_dir "/storage/emulated/0/Download"
add_download_dir "/sdcard/Download"

if ((DOWNLOAD_ACCESS == 0)) && command -v termux-setup-storage >/dev/null 2>&1; then
  step "Requesting Android Downloads access"
  termux-setup-storage || true
  printf 'Tap Allow in the Android permission window, return to Termux, then press Enter.\n'
  read -r _
  add_download_dir "${HOME}/storage/downloads"
  if [[ -n "${EXTERNAL_STORAGE:-}" ]]; then
    add_download_dir "${EXTERNAL_STORAGE}/Download"
  fi
  add_download_dir "/storage/emulated/0/Download"
  add_download_dir "/sdcard/Download"
fi
((DOWNLOAD_ACCESS == 1)) || fail "Android Downloads is not accessible. Run termux-setup-storage, tap Allow, and rerun this script."

step "Locating and verifying the downloaded R5 archive"
ARCHIVE=""
if [[ -n "$ARCHIVE_OVERRIDE" ]]; then
  [[ -f "$ARCHIVE_OVERRIDE" ]] || fail "Archive path does not exist: $ARCHIVE_OVERRIDE"
  ARCHIVE="$(cd "$(dirname "$ARCHIVE_OVERRIDE")" && pwd)/$(basename "$ARCHIVE_OVERRIDE")"
else
  while IFS= read -r -d '' candidate; do
    size="$(stat -c '%s' "$candidate" 2>/dev/null || printf '0')"
    [[ "$size" == "$EXPECTED_SIZE" ]] || continue
    printf 'Checking: %s\n' "$candidate"
    digest="$(sha256sum "$candidate" | awk '{print $1}')"
    if [[ "$digest" == "$EXPECTED_SHA" ]]; then
      ARCHIVE="$candidate"
      break
    fi
  done < <(
    for dir in "${SEARCH_DIRS[@]}"; do
      find "$dir" -maxdepth 1 -type f \( -iname '*.zst' -o -iname '*.tar.zst' \) -print0 2>/dev/null
    done
  )
fi
[[ -n "$ARCHIVE" ]] || fail "The verified 170,394,097-byte R5 .zst archive was not found in Android Downloads. Download the archive, leave its filename unchanged, and rerun."

ACTUAL_SIZE="$(stat -c '%s' "$ARCHIVE")"
[[ "$ACTUAL_SIZE" == "$EXPECTED_SIZE" ]] || fail "Archive size mismatch: expected=$EXPECTED_SIZE actual=$ACTUAL_SIZE"
ACTUAL_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || fail "Archive SHA-256 mismatch: expected=$EXPECTED_SHA actual=$ACTUAL_SHA"
printf 'Verified archive: %s\nSHA-256: %s\nSize: %s bytes\n' "$ARCHIVE" "$ACTUAL_SHA" "$ACTUAL_SIZE"

if ((DRY_RUN)); then
  printf '\nDRY RUN PASS. No GitHub changes were made.\nLog: %s\n' "$LOG_FILE"
  exit 0
fi

step "Authenticating GitHub CLI"
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  printf 'A GitHub browser sign-in will open. Approve the login for your GitHub account.\n'
  gh auth login --hostname github.com --git-protocol https --web --scopes repo
fi
if ! gh repo view "$REPO" --json nameWithOwner --jq '.nameWithOwner' >/dev/null 2>&1; then
  step "Refreshing GitHub authorization for private repository access"
  gh auth refresh --hostname github.com --scopes repo
fi
gh repo view "$REPO" --json nameWithOwner --jq '.nameWithOwner' >/dev/null \
  || fail "Authenticated account cannot access $REPO."

step "Preparing canonical release assets"
WORK_ROOT="$(mktemp -d "${TMPDIR:-$HOME}/metablooms-r5-release.XXXXXX")"
cleanup() { rm -rf "$WORK_ROOT"; }
trap cleanup EXIT
STAGED_ARCHIVE="$WORK_ROOT/$CANONICAL_NAME"
STAGED_SIDECAR="$WORK_ROOT/$SIDECAR_NAME"

if [[ "$(basename "$ARCHIVE")" == "$CANONICAL_NAME" ]]; then
  STAGED_ARCHIVE="$ARCHIVE"
else
  printf 'Normalizing the release filename. The downloaded archive is not modified.\n'
  cp --reflink=auto "$ARCHIVE" "$STAGED_ARCHIVE" \
    || fail "Could not create the temporary canonical copy. Free at least 200 MB and rerun."
fi
printf '%s  %s\n' "$EXPECTED_SHA" "$CANONICAL_NAME" > "$STAGED_SIDECAR"
(
  cd "$(dirname "$STAGED_ARCHIVE")"
  sha256sum -c "$STAGED_SIDECAR"
)

cat > "$WORK_ROOT/RELEASE_NOTES.md" <<NOTES
MetaBlooms OS Stage071N V4 R5 repaired candidate.

- SHA-256: \`$EXPECTED_SHA\`
- Validated archive size: 170,394,097 bytes
- Repository seed includes the repaired multi-agent SARP convergence workflow.

Release assets are transport artifacts. They do not independently authorize implementation, promotion, merge, hosted publication, or broader rollout.
NOTES

step "Publishing GitHub Release $TAG"
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  gh release upload "$TAG" "$STAGED_ARCHIVE" "$STAGED_SIDECAR" \
    --repo "$REPO" --clobber
else
  gh release create "$TAG" "$STAGED_ARCHIVE" "$STAGED_SIDECAR" \
    --repo "$REPO" \
    --target "$TARGET_BRANCH" \
    --title "$TITLE" \
    --notes-file "$WORK_ROOT/RELEASE_NOTES.md"
fi

step "Verifying remote release assets"
REMOTE_ARCHIVE_SIZE="$(gh api "repos/$REPO/releases/tags/$TAG" \
  --jq ".assets[] | select(.name == \"$CANONICAL_NAME\") | .size")"
REMOTE_SIDECAR_SIZE="$(gh api "repos/$REPO/releases/tags/$TAG" \
  --jq ".assets[] | select(.name == \"$SIDECAR_NAME\") | .size")"
[[ "$REMOTE_ARCHIVE_SIZE" == "$EXPECTED_SIZE" ]] \
  || fail "Remote archive missing or wrong size: expected=$EXPECTED_SIZE actual=${REMOTE_ARCHIVE_SIZE:-missing}"
[[ -n "$REMOTE_SIDECAR_SIZE" && "$REMOTE_SIDECAR_SIZE" -gt 0 ]] \
  || fail "Remote SHA-256 sidecar is missing or empty."

VERIFY_DIR="$WORK_ROOT/verify"
mkdir -p "$VERIFY_DIR"
gh release download "$TAG" --repo "$REPO" --pattern "$SIDECAR_NAME" --dir "$VERIFY_DIR"
cmp -s "$STAGED_SIDECAR" "$VERIFY_DIR/$SIDECAR_NAME" \
  || fail "Downloaded release sidecar does not match the locally generated sidecar."

RELEASE_URL="$(gh release view "$TAG" --repo "$REPO" --json url --jq '.url')"

printf '\n============================================================\n'
printf 'SUCCESS: MetaBlooms OS R5 release is published and verified.\n'
printf 'Release: %s\n' "$RELEASE_URL"
printf 'Archive: %s\n' "$CANONICAL_NAME"
printf 'SHA-256: %s\n' "$EXPECTED_SHA"
printf 'Remote size: %s bytes\n' "$REMOTE_ARCHIVE_SIZE"
printf 'Log: %s\n' "$LOG_FILE"
printf '============================================================\n'
