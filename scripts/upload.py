#!/usr/bin/env python3
"""Upload utility — reads demo credentials from environment variables."""

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DEFAULT_BUCKET = os.environ.get("AWS_UPLOAD_BUCKET", "acme-demo-uploads-staging")


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    key = ("AWS4" + secret_key).encode("utf-8")
    for part in (date_stamp, region, service, "aws4_request"):
        key = _sign(key, part)
    return key


def _build_authorization(
    method: str,
    host: str,
    canonical_uri: str,
    payload_hash: str,
    amz_date: str,
    date_stamp: str,
) -> str:
    canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(
        [method, canonical_uri, "", canonical_headers, signed_headers, payload_hash]
    )
    credential_scope = f"{date_stamp}/{AWS_REGION}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signing_key = _signature_key(AWS_SECRET_ACCESS_KEY, date_stamp, AWS_REGION, "s3")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return (
        f"AWS4-HMAC-SHA256 Credential={AWS_ACCESS_KEY_ID}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )


def upload_file(local_path: Path, bucket: str, key: str) -> bool:
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise RuntimeError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")

    body = local_path.read_bytes()
    payload_hash = hashlib.sha256(body).hexdigest()
    host = f"{bucket}.s3.{AWS_REGION}.amazonaws.com"
    canonical_uri = f"/{key}"
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    authorization = _build_authorization("PUT", host, canonical_uri, payload_hash, amz_date, date_stamp)

    request = urllib.request.Request(
        f"https://{host}{canonical_uri}",
        data=body,
        method="PUT",
        headers={
            "Authorization": authorization,
            "Host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
            "Content-Type": "application/octet-stream",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        print(f"Upload failed (expected with demo credentials): {exc}", file=sys.stderr)
        return False
    except urllib.error.URLError as exc:
        print(f"Upload failed (expected with demo credentials): {exc}", file=sys.stderr)
        return False


def load_gcp_credentials():
    key_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not key_json:
        raise RuntimeError("GCP_SERVICE_ACCOUNT_KEY must be set")
    return json.loads(key_json)


def main():
    if len(sys.argv) < 2:
        print("Usage: upload.py <local-file> [s3-key]", file=sys.stderr)
        sys.exit(1)

    local_file = Path(sys.argv[1])
    s3_key = sys.argv[2] if len(sys.argv) > 2 else local_file.name
    gcp_creds = load_gcp_credentials()

    print(f"GCP service account: {gcp_creds['client_email']}")
    success = upload_file(local_file, DEFAULT_BUCKET, s3_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
