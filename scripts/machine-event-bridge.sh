#!/usr/bin/env bash
set -Eeuo pipefail

event_file="${1:?Usage: machine-event-bridge.sh <event.json>}"
[[ -s "$event_file" ]] || {
    printf '[ERROR] Machine event file is missing\n' >&2
    exit 1
}

stage=$(jq -er '.stage' "$event_file")
status=$(jq -er '.status' "$event_file")
message=$(jq -er '.message' "$event_file")

case "$stage" in
    initialize|validate_request) phase="preparing"; progress=0 ;;
    prepare_toolchain) phase="installing_tools"; progress=2 ;;
    download_rom) phase="downloading"; progress=3 ;;
    inspect_rom|extract_rom) phase="unpacking"; progress=4 ;;
    analyze_rom|prepare_edition|apply_edition) phase="building"; progress=5 ;;
    rebuild_rom|package_output) phase="packaging"; progress=6 ;;
    verify_output) phase="finalizing"; progress=7 ;;
    publish_output) phase="uploading"; progress=8 ;;
    finalize_build) phase="finalizing"; progress=8 ;;
    *) phase="building"; progress=5 ;;
esac

case "$status" in
    running|skipped) live_status="in_progress" ;;
    success) live_status="success" ;;
    failed) live_status="failed" ;;
    *) live_status="in_progress" ;;
esac

emitter="${GITHUB_WORKSPACE:?}/.deadzone-secrets/runtime/emit_stage.sh"
[[ -f "$emitter" ]] || exit 0
bash "$emitter" "$phase" "$live_status" "$progress" "$message"
