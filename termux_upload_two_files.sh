#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_URL="https://github.com/blobertplunk-hue/metablooms-uploads.git"
REPO_DIR="$HOME/metablooms-uploads"
BRANCH="main"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1"
    exit 1
  }
}

pick_one_file() {
  local picked
  picked="$(termux-file-picker 2>/dev/null || true)"
  if [ -z "${picked:-}" ]; then
    echo ""
    return 0
  fi
  picked="${picked#file://}"
  echo "$picked"
}

echo "== MetaBlooms simple upload =="
echo

need_cmd git
need_cmd gh
need_cmd termux-file-picker

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Cloning repo..."
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"

current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -n "$current_branch" ] && [ "$current_branch" != "$BRANCH" ]; then
  git checkout "$BRANCH" || true
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub login needed. A browser login will open."
  gh auth login --web --git-protocol https
fi

echo
read -r -p "Folder inside repo to upload into (blank = repo root): " DEST_SUBDIR
DEST_SUBDIR="${DEST_SUBDIR#./}"
DEST_PATH="$REPO_DIR"
if [ -n "$DEST_SUBDIR" ]; then
  DEST_PATH="$REPO_DIR/$DEST_SUBDIR"
  mkdir -p "$DEST_PATH"
fi

echo
echo "Pick FILE 1"
FILE1="$(pick_one_file)"
if [ -z "$FILE1" ] || [ ! -f "$FILE1" ]; then
  echo "No valid first file selected. Exiting."
  exit 1
fi
echo "Selected: $FILE1"

echo
echo "Pick FILE 2"
FILE2="$(pick_one_file)"
if [ -z "$FILE2" ] || [ ! -f "$FILE2" ]; then
  echo "No valid second file selected. Exiting."
  exit 1
fi
echo "Selected: $FILE2"

cp -f "$FILE1" "$DEST_PATH/$(basename "$FILE1")"
cp -f "$FILE2" "$DEST_PATH/$(basename "$FILE2")"

git add .

if git diff --cached --quiet; then
  echo "Nothing changed after copying files."
  exit 0
fi

echo
git status --short

echo
read -r -p "Commit message: " COMMIT_MSG
if [ -z "${COMMIT_MSG:-}" ]; then
  COMMIT_MSG="Upload two files from Termux"
fi

git commit -m "$COMMIT_MSG"
git push origin "$(git rev-parse --abbrev-ref HEAD)"

echo
echo "Done."
echo "Uploaded:"
echo " - $(basename "$FILE1")"
echo " - $(basename "$FILE2")"
echo "Repo: $REPO_URL"
