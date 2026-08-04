#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing {name}")
    return value


def append_environment(values: dict[str, str]) -> None:
    path = Path(required("GITHUB_ENV"))
    with path.open("a", encoding="utf-8") as stream:
        for name, value in values.items():
            if "\n" in value or "\r" in value:
                raise SystemExit(f"Invalid multiline environment value: {name}")
            stream.write(f"{name}={value}\n")


def append_output(name: str, value: str) -> None:
    path = Path(required("GITHUB_OUTPUT"))
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"{name}={value}\n")


def signed_contract(project: str, request_id: str) -> dict:
    secret = required("BUILD_PROGRESS_SECRET")
    payload = {
        "schema_version": "1.0",
        "request_id": request_id,
        "project": project,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        required("CONTROL_BOT_CONTRACT_URL"),
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-DeadZone-Signature": signature,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        response_body = response.read()
        response_signature = response.headers.get("X-DeadZone-Signature", "")
    expected = hmac.new(secret.encode(), response_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, response_signature):
        raise SystemExit("Invalid Control Bot response signature")
    value = json.loads(response_body)
    if not isinstance(value, dict):
        raise SystemExit("Control Bot contract is not an object")
    return value


def resolve_bot(project: str, code: str, request_id: str) -> dict[str, str]:
    pattern = rf"DZ-{re.escape(code)}-[0-9]{{8}}-[0-9]{{4}}"
    if not re.fullmatch(pattern, request_id):
        raise SystemExit(f"Invalid {project} request ID")

    contract = signed_contract(project, request_id)
    if contract.get("request_id") != request_id or contract.get("project") != project:
        raise SystemExit("Private build contract mismatch")

    source_url = str((contract.get("source") or {}).get("url") or "")
    builder = contract.get("builder") or {}
    live = contract.get("live_message") or {}
    builder_id = int(builder.get("telegram_user_id") or 0)
    builder_slug = str(builder.get("slug") or "")
    builder_name = str(builder.get("display_name") or builder.get("username") or builder_slug or "DeadZone Builder")
    language = "ar" if str(contract.get("language") or "").lower() == "ar" else "en"
    chat_id = int(live.get("chat_id") or 0)
    message_id = int(live.get("message_id") or 0)

    if not source_url.startswith("https://"):
        raise SystemExit("Private ROM source URL is invalid")
    if builder_id <= 0 or not re.fullmatch(r"[a-z0-9_.-]{1,48}", builder_slug):
        raise SystemExit("Builder identity is invalid")
    if chat_id == 0 or message_id <= 0:
        raise SystemExit("Live message contract is missing")

    print(f"::add-mask::{source_url}")
    return {
        "REQUEST_ID": request_id,
        "ROM_URL_B64": base64.b64encode(source_url.encode()).decode(),
        "BUILDER_ID": str(builder_id),
        "BUILDER_SLUG": builder_slug,
        "BUILDER_NAME_B64": base64.b64encode(builder_name.encode()).decode(),
        "DEADZONE_LANGUAGE": language,
        "TELEGRAM_MSG_CHAT_ID": str(chat_id),
        "TELEGRAM_MSG_ID": str(message_id),
        "REQUEST_SOURCE": "telegram",
        "DEADZONE_CONTROLLED_BUILD": "1",
    }


def resolve_manual(project: str, code: str) -> dict[str, str]:
    source_url = os.environ.get("INPUT_ROM_LINK", "").strip()
    if not source_url.startswith("https://"):
        raise SystemExit("Manual build requires an HTTPS ROM link")
    print(f"::add-mask::{source_url}")
    builder_name = os.environ.get("INPUT_BUILDER_LABEL", "").strip() or required("GITHUB_ACTOR")
    language = "ar" if os.environ.get("INPUT_LANGUAGE", "").strip().lower() == "ar" else "en"
    return {
        "REQUEST_ID": f"DZ-{code}-DIRECT-{required('GITHUB_RUN_ID')}",
        "ROM_URL_B64": base64.b64encode(source_url.encode()).decode(),
        "BUILDER_ID": "0",
        "BUILDER_SLUG": "github",
        "BUILDER_NAME_B64": base64.b64encode(builder_name.encode()).decode(),
        "DEADZONE_LANGUAGE": language,
        "REQUEST_SOURCE": "github",
        "DEADZONE_CONTROLLED_BUILD": "0",
    }


def main() -> int:
    project = required("DEADZONE_PROJECT")
    code = required("DEADZONE_PROJECT_CODE")
    request_id = os.environ.get("INPUT_REQUEST_ID", "").strip()
    if request_id:
        values = resolve_bot(project, code, request_id)
        mode = "bot"
    else:
        values = resolve_manual(project, code)
        mode = "manual"
    values["BUILD_STARTED_AT"] = datetime.now(timezone.utc).isoformat()
    append_environment(values)
    append_output("mode", mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
