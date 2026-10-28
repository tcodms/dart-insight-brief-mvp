"""Service configuration, separate from legacy Agent credentials."""

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / '.service-data'
    origin: str = 'http://127.0.0.1:5173'
    secret: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    google_id: str = ''
    google_secret: str = ''
    cookie_secure: bool = False
    max_upload_bytes: int = 20 * 1024 * 1024
    session_seconds: int = 7 * 24 * 3600

    @property
    def google_configured(self) -> bool:
        return bool(self.google_id and self.google_secret and len(self.secret) >= 32)

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / '.env.service', override=False)
        origin = os.getenv('SERVICE_ORIGIN', 'http://127.0.0.1:5173').rstrip('/')
        url = urlsplit(origin)
        if url.scheme not in ('http', 'https') or not url.hostname or url.path or url.query or url.fragment or url.username:
            raise ValueError('SERVICE_ORIGIN must be a single HTTP(S) origin')
        secure = os.getenv('SERVICE_COOKIE_SECURE', 'false').lower() == 'true'
        if url.hostname not in ('127.0.0.1', 'localhost', '::1') and (url.scheme != 'https' or not secure):
            raise ValueError('Non-local deployment requires HTTPS and secure cookies')
        secret = os.getenv('SERVICE_SESSION_SECRET', '')
        google_id = os.getenv('GOOGLE_CLIENT_ID', '')
        google_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        if (google_id or google_secret) and len(secret) < 32:
            raise ValueError('Set SERVICE_SESSION_SECRET to at least 32 characters')
        return cls(data_dir=Path(os.getenv('SERVICE_DATA_DIR', str(ROOT / '.service-data'))).resolve(),
                   origin=origin, secret=secret or secrets.token_urlsafe(48),
                   google_id=google_id, google_secret=google_secret, cookie_secure=secure)
