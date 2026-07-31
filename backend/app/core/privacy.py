"""
backend.app.core.privacy
~~~~~~~~~~~~~~~~~~~~~~~~
Handles encryption-at-rest (AES-256 GCM) for biometric records and
athlete pseudonymization (HMAC-SHA256) to ensure health compliance (GDPR/HIPAA).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.core.config import settings


class Pseudonymizer:
    """Secure pseudonymization system for athlete identifiers."""

    def __init__(self, salt: str) -> None:
        self._salt = salt.encode("utf-8")

    def pseudonymize(self, athlete_id: str) -> str:
        """Hash the athlete_id using HMAC-SHA256 and truncate to create a clean secure pseudo-ID."""
        h = hmac.new(self._salt, athlete_id.encode("utf-8"), hashlib.sha256)
        # Create a shorter, readable hash representation prepended with 'PSN-'
        return f"PSN-{h.hexdigest()[:12].upper()}"


class BiometricEncryptor:
    """Encryption-at-rest utility using AES-256 GCM."""

    def __init__(self, key_base64: str) -> None:
        try:
            self._key = base64.b64decode(key_base64)
            if len(self._key) != 32:
                # Fallback / derivation if decoding is not 32 bytes
                self._key = hashlib.sha256(self._key).digest()
        except Exception:
            # Fallback to key derivation if base64 decoding fails
            self._key = hashlib.sha256(key_base64.encode("utf-8")).digest()
        
        self._aesgcm = AESGCM(self._key)

    def encrypt_data(self, data: Any) -> str:
        """Serialize data to JSON, encrypt via AES-GCM, and return base64 string."""
        serialized = json.dumps(data)
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, serialized.encode("utf-8"), None)
        # Prepend nonce (12 bytes) to ciphertext
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode("utf-8")

    def decrypt_data(self, ciphertext_base64: str) -> Any:
        """Decrypt base64 ciphertext via AES-GCM and deserialize JSON data."""
        combined = base64.b64decode(ciphertext_base64)
        if len(combined) < 13:
            raise ValueError("Ciphertext is too short.")
        nonce = combined[:12]
        ciphertext = combined[12:]
        decrypted = self._aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted.decode("utf-8"))


# Global instances initialized with settings variables
pseudonymizer = Pseudonymizer(salt=settings.jwt_secret_key)
biometric_encryptor = BiometricEncryptor(key_base64=settings.encryption_key)
