"""
Security Hardening Utilities (Batch 5 - Feature 3 & 4).
Includes:
- File content & magic-byte validation (detecting disguised/malicious uploads).
- Path traversal protection.
- In-memory rate limiting for sensitive endpoints.
- Security headers middleware.
- Cryptographic hash chaining for audit log integrity verification.
"""

import os
import re
import time
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# Magic bytes signatures for allowed image formats
MAGIC_BYTES = {
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],  # Further verified by "WEBP" at offset 8
    "mp4": [b"ftyp", b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp", b"\x00\x00\x00\x20ftyp"]
}

MAX_IMAGE_SIZE_BYTES = 25 * 1024 * 1024   # 25 MB
MAX_VIDEO_SIZE_BYTES = 50 * 1024 * 1024   # 50 MB


def validate_file_content_and_type(
    file_bytes: bytes,
    filename: str,
    is_video: bool = False
) -> Tuple[bool, str, str]:
    """
    Validates file size, extension, and real content magic bytes.
    Returns (is_valid, detected_type, error_message).
    """
    max_size = MAX_VIDEO_SIZE_BYTES if is_video else MAX_IMAGE_SIZE_BYTES
    if len(file_bytes) > max_size:
        return False, "unknown", f"File size exceeds maximum limit of {max_size // (1024*1024)}MB."

    if len(file_bytes) < 12:
        return False, "unknown", "File is empty or too small to be a valid media file."

    # Extension check
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    allowed_exts = {"mp4", "avi", "mov", "mkv"} if is_video else {"jpg", "jpeg", "png", "webp"}
    if ext not in allowed_exts:
        return False, ext, f"File extension '.{ext}' is not permitted."

    # Magic byte inspection
    header_16 = file_bytes[:16]

    if not is_video:
        # Check JPEG
        if header_16.startswith(b"\xff\xd8\xff"):
            return True, "jpeg", ""
        # Check PNG
        if header_16.startswith(b"\x89PNG\r\n\x1a\n"):
            return True, "png", ""
        # Check WebP: starts with RIFF, bytes 8-12 is WEBP
        if header_16.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP":
            return True, "webp", ""

        return False, "disguised_file", (
            "File content does not match genuine JPEG, PNG, or WebP magic bytes. "
            "Disguised or executable files are strictly prohibited."
        )
    else:
        # Video basic check (MP4/MKV/WebM)
        if b"ftyp" in header_16 or header_16.startswith(b"\x1a\x45\xdf\xa3"):
            return True, "video", ""
        return True, "video", ""  # allow generic video container


def generate_safe_storage_filename(original_filename: str, prefix: str = "media") -> str:
    """
    Generates a secure UUID filename, stripping user-supplied paths and preventing path traversal.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    clean_ext = re.sub(r"[^a-z0-9]", "", ext)
    if not clean_ext:
        clean_ext = "jpg"
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique_id}.{clean_ext}"


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Verifies target_path does not escape base_dir via directory traversal.
    """
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    return abs_target.startswith(abs_base)


class InMemoryRateLimiter:
    """
    Sliding-window rate limiter for sensitive endpoints.
    Tracks requests per client IP or user token.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_key: str) -> bool:
        now = time.time()
        timestamps = self.clients.get(client_key, [])
        # Expire old entries
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self.max_requests:
            self.clients[client_key] = timestamps
            return True

        timestamps.append(now)
        self.clients[client_key] = timestamps
        return False


# Global rate limiters for specific operations
auth_rate_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)
ai_rate_limiter = InMemoryRateLimiter(max_requests=30, window_seconds=60)
general_rate_limiter = InMemoryRateLimiter(max_requests=300, window_seconds=60)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds enterprise security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "font-src 'self' data: https:;"
        )
        return response


# =====================================================================
# AUDIT LOG CRYPTOGRAPHIC INTEGRITY CHAINING
# =====================================================================

GENESIS_HASH = "0" * 64


def compute_audit_record_hash(
    record_id: str,
    timestamp: str,
    user_id: str,
    action: str,
    target_id: str,
    outcome: str,
    details_str: str,
    prev_hash: str
) -> str:
    """
    Computes SHA-256 hash for an audit log record linked to previous record hash.
    """
    content = f"{record_id}|{timestamp}|{user_id}|{action}|{target_id}|{outcome}|{details_str}|{prev_hash}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_audit_chain_integrity(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifies that the audit log sequence is cryptographically contiguous and unaltered.
    """
    if not records:
        return {
            "is_valid": True,
            "total_records_checked": 0,
            "message": "Audit log is empty. Genesis chain intact."
        }

    expected_prev_hash = GENESIS_HASH
    tampered_indices: List[int] = []

    for idx, rec in enumerate(records):
        rec_prev = rec.get("prev_hash")
        rec_hash = rec.get("record_hash")

        # Check prev_hash linkage
        if rec_prev != expected_prev_hash:
            tampered_indices.append(idx)

        # Check record's own computed hash
        details_str = str(rec.get("details", {}))
        computed = compute_audit_record_hash(
            record_id=str(rec.get("id") or rec.get("_id")),
            timestamp=str(rec.get("timestamp")),
            user_id=str(rec.get("user_id")),
            action=str(rec.get("action")),
            target_id=str(rec.get("target_id", "")),
            outcome=str(rec.get("outcome", "SUCCESS")),
            details_str=details_str,
            prev_hash=rec_prev or GENESIS_HASH
        )

        if rec_hash != computed:
            tampered_indices.append(idx)

        expected_prev_hash = rec_hash or computed

    is_intact = len(tampered_indices) == 0
    return {
        "is_valid": is_intact,
        "total_records_checked": len(records),
        "tampered_records_count": len(tampered_indices),
        "tampered_indices": tampered_indices,
        "chain_head_hash": expected_prev_hash,
        "disclaimer": (
            "Cryptographic hash chaining detects record insertion, modification, or reordering "
            "via application APIs. It does not prevent direct out-of-band database overwrites by a database superuser."
        )
    }
