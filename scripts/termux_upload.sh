#!/data/data/com.termux/files/usr/bin/bash
# termux_upload.sh — send MetaBlooms zip files to the sandbox receiver.
#
# Usage:
#   bash termux_upload.sh <SERVER_IP>
#
# Example:
#   bash termux_upload.sh 192.168.1.42
#
# The server IP is printed by receive_uploads.py when it starts.

set -euo pipefail

SERVER_IP="${1:-}"
PORT=8765
DOWNLOADS="/sdcard/Download"

FILE_1="claude_code_metablooms_pack.zip"
FILE_2="Metablooms_OS_HARDENED.zip"

# ── validate args ─────────────────────────────────────────────────────────────
if [[ -z "$SERVER_IP" ]]; then
    echo "Usage: bash termux_upload.sh <SERVER_IP>"
    echo "  The IP is printed by receive_uploads.py when it starts."
    exit 1
fi

# ── check curl available ──────────────────────────────────────────────────────
if ! command -v curl &>/dev/null; then
    echo "curl not found. Install it with: pkg install curl"
    exit 1
fi

# ── confirm server is reachable ───────────────────────────────────────────────
echo "Checking connection to $SERVER_IP:$PORT ..."
if ! curl -sf --connect-timeout 5 "http://$SERVER_IP:$PORT/health" >/dev/null; then
    echo "ERROR: Cannot reach http://$SERVER_IP:$PORT — is receive_uploads.py running?"
    exit 1
fi
echo "  Connected OK"
echo

# ── upload helper ─────────────────────────────────────────────────────────────
upload_file() {
    local name="$1"
    local path="$DOWNLOADS/$name"

    if [[ ! -f "$path" ]]; then
        echo "SKIP $name — not found in $DOWNLOADS"
        return 0
    fi

    echo "Uploading $name ($(du -sh "$path" | cut -f1)) ..."
    local response
    response=$(curl -sf \
        -X POST \
        -F "file=@${path};filename=${name}" \
        "http://$SERVER_IP:$PORT/upload")

    if [[ $? -eq 0 ]]; then
        echo "  $response"
    else
        echo "  ERROR uploading $name"
        return 1
    fi
}

# ── send both files ───────────────────────────────────────────────────────────
upload_file "$FILE_1"
upload_file "$FILE_2"

echo
echo "Done. Check the sandbox terminal for SHA256 receipts."
