"""
Gemini Key Manager - API Key Rotation System
Primary key used first. On 429 rate limit, automatically rotates to next fallback key.
Resets back to primary after a cooldown period.
"""

import time
import threading
from typing import Optional
from google import genai

import os
from dotenv import load_dotenv
load_dotenv()

# Key configuration - loaded from .env
PRIMARY_KEY = os.getenv("GEMINI_API_KEY_PRIMARY") or os.getenv("GOOGLE_API_KEY")
FALLBACK_KEYS = [
    k for k in [
        os.getenv("GEMINI_API_KEY_FALLBACK_1"),
        os.getenv("GEMINI_API_KEY_FALLBACK_2"),
        os.getenv("GEMINI_API_KEY_FALLBACK_3"),
        os.getenv("GEMINI_API_KEY_FALLBACK_4"),
    ] if k  # only include keys that are set
]
ALL_KEYS = [PRIMARY_KEY] + FALLBACK_KEYS
KEY_COOLDOWN_SECONDS = 62  # 1 min + buffer  # How long before a rate-limited key is retried
# Conservative strategy controls:
# - max keys attempted per request (default: 1 = only primary-style single attempt)
# - whether to wait when all keys are cooling down (default: false = fail fast)
MAX_KEYS_PER_REQUEST = max(1, int(os.getenv("GEMINI_MAX_KEYS_PER_REQUEST", "1")))
WAIT_WHEN_ALL_KEYS_LIMITED = os.getenv("GEMINI_WAIT_ON_ALL_LIMITED", "false").lower() == "true"


class GeminiKeyManager:
    """
    Manages 5 Gemini API keys with automatic rotation on 429 rate limit.
    - Always starts with primary key
    - On 429, marks key as rate-limited and rotates to next available key
    - After cooldown period, key becomes available again
    - Thread-safe for concurrent requests
    """

    def __init__(self):
        self._keys = ALL_KEYS[:]
        self._current_index = 0
        self._rate_limited_until = {}  # key -> timestamp when it becomes available again
        self._lock = threading.Lock()
        self._clients = {}  # key -> genai.Client (cached)

        # Pre-create all clients
        for key in self._keys:
            self._clients[key] = genai.Client(api_key=key)

        print(f"GeminiKeyManager: {len(self._keys)} keys loaded (1 primary + {len(FALLBACK_KEYS)} fallbacks)")

    def get_client(self, wait_if_all_limited: bool = True) -> tuple:
        """
        Get the current active client and its key index.
        Returns: (client, key_index, key_label)
        """
        with self._lock:
            now = time.time()

            # Try from current index, wrap around
            for attempt in range(len(self._keys)):
                idx = (self._current_index + attempt) % len(self._keys)
                key = self._keys[idx]

                # Check if this key is still rate-limited
                if key in self._rate_limited_until:
                    if now < self._rate_limited_until[key]:
                        remaining = self._rate_limited_until[key] - now
                        label = "PRIMARY" if idx == 0 else f"FALLBACK-{idx}"
                        print(f"  KeyManager: {label} still rate-limited ({remaining:.0f}s remaining), trying next...")
                        continue
                    else:
                        # Cooldown expired — key available again
                        del self._rate_limited_until[key]

                # This key is available
                label = "PRIMARY" if idx == 0 else f"FALLBACK-{idx}"
                return self._clients[key], idx, label

            # All keys are rate-limited
            # Either fail fast or wait for the soonest key
            if not wait_if_all_limited:
                raise Exception("All keys are currently rate-limited")

            # Use the one whose cooldown expires soonest
            soonest_key = min(self._rate_limited_until, key=self._rate_limited_until.get)
            soonest_idx = self._keys.index(soonest_key)
            wait = max(0, self._rate_limited_until[soonest_key] - now)
            label = "PRIMARY" if soonest_idx == 0 else f"FALLBACK-{soonest_idx}"
            print(f"  KeyManager: All keys rate-limited! Waiting {wait:.1f}s for {label}...")
            time.sleep(wait + 0.1)
            del self._rate_limited_until[soonest_key]
            return self._clients[soonest_key], soonest_idx, label

    def mark_rate_limited(self, key_index: int):
        """Mark a key as rate-limited. It won't be used again until cooldown expires."""
        with self._lock:
            key = self._keys[key_index]
            self._rate_limited_until[key] = time.time() + KEY_COOLDOWN_SECONDS
            label = "PRIMARY" if key_index == 0 else f"FALLBACK-{key_index}"
            print(f"  KeyManager: {label} rate-limited. Cooldown: {KEY_COOLDOWN_SECONDS}s")

            # Advance current index to next available key
            self._current_index = (key_index + 1) % len(self._keys)

    def generate(self, model: str, contents: str, stop_event: threading.Event = None) -> str:
        """
        Conservative if/else-style key usage:
        - Try PRIMARY first.
        - Optionally try limited fallbacks (controlled by GEMINI_MAX_KEYS_PER_REQUEST).
        - Fail fast if all are cooling down (unless GEMINI_WAIT_ON_ALL_LIMITED=true).
        Uses streaming to abort early if stop_event is set.
        """
        last_error = None
        tried = set()
        max_attempts = min(len(self._keys), MAX_KEYS_PER_REQUEST)

        for attempt in range(max_attempts):
            client, idx, label = self.get_client(wait_if_all_limited=WAIT_WHEN_ALL_KEYS_LIMITED)
            if idx in tried:
                break
            tried.add(idx)
            try:
                print(f"  KeyManager: Using {label} key")
                if stop_event and stop_event.is_set():
                    print("  [ABORTED] Generate aborted before starting.")
                    return "ABORTED"
                
                response_stream = client.models.generate_content_stream(model=model, contents=contents)
                full_text = []
                for chunk in response_stream:
                    if stop_event and stop_event.is_set():
                        print("  [ABORTED] Stopping Gemini generation mid-stream.")
                        return "".join(full_text)
                    if chunk.text:
                        full_text.append(chunk.text)
                return "".join(full_text)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    print(f"  KeyManager: {label} hit rate limit (429)")
                    self.mark_rate_limited(idx)
                    last_error = e
                    continue
                else:
                    raise e

        raise Exception(
            f"Gemini request failed after {len(tried)} key attempt(s). "
            f"Max allowed per request: {MAX_KEYS_PER_REQUEST}. Last error: {last_error}"
        )

    def status(self) -> dict:
        """Return current status of all keys."""
        now = time.time()
        result = []
        for i, key in enumerate(self._keys):
            label = "PRIMARY" if i == 0 else f"FALLBACK-{i}"
            is_limited = key in self._rate_limited_until and now < self._rate_limited_until[key]
            remaining = max(0, self._rate_limited_until.get(key, 0) - now)
            result.append({
                "label": label,
                "key_hint": key[:12] + "...",
                "available": not is_limited,
                "rate_limited_for_seconds": round(remaining) if is_limited else 0
            })
        return {"keys": result, "active_index": self._current_index}


# Singleton instance shared across all modules
_key_manager = None
_manager_lock = threading.Lock()

def get_key_manager() -> GeminiKeyManager:
    """Get the singleton GeminiKeyManager instance."""
    global _key_manager
    if _key_manager is None:
        with _manager_lock:
            if _key_manager is None:
                _key_manager = GeminiKeyManager()
    return _key_manager


