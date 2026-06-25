"""
[PHASE6] Web Application Firewall (WAF) Middleware.
Detects and blocks common web attacks: SQL injection, XSS, path traversal,
command injection, etc. Following OWASP Top 10 + ModSecurity CRS rules.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("adam_prism.waf")

OWASP_TOP_10_PATTERNS = {
    "sql_injection": [
        r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table)",
        r"(?i)(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(?i)('|)\s*;\s*(drop|delete|update|insert|select)",
        r"(?i)(\bexec\b|\bexecute\b).*(\bxp_cmdshell\b|\bsp_executesql\b)",
    ],
    "xss": [
        r"(?i)<script[^>]*>",
        r"(?i)javascript\s*:",
        r"(?i)on(load|error|click|mouse|focus|blur|change|submit)\s*=",
        r"(?i)eval\s*\(",
        r"(?i)document\.(cookie|write|location)",
        r"(?i)<iframe[^>]*>",
    ],
    "path_traversal": [
        r"\.\./\.\.",
        r"%2e%2e",
        r"\.\.%2f",
        r"/etc/(passwd|shadow)",
        r"\\\\(windows|system32)",
    ],
    "command_injection": [
        r"[;&|`$]\s*(rm|wget|curl|nc|netcat|bash|sh|cmd|powershell)\b",
        r"\b(rm\s+-rf|chmod\s+777)\b",
        r"(?i)(exec|system|passthru|popen|proc_open)\s*\(",
    ],
    "ldap_injection": [
        r"[()|*\\]",
        r"(?i)(\(|\))\s*(\||\&)\s*(\(|\))",
    ],
    "xxe": [
        r"<!ENTITY",
        r"<!DOCTYPE\s+.*\s+SYSTEM",
    ],
    "ssrf": [
        r"(?i)(file|gopher|dict|ldap|ftp)://",
        r"(?i)169\.254\.169\.254",  # AWS metadata
        r"(?i)metadata\.google\.internal",
    ],
    "nosql_injection": [
        r"\$ne\s*=",
        r"\$gt\s*=",
        r"\$regex\s*:",
    ],
    "jwt_attack": [
        r"(?i)alg\s*:\s*[\"']none[\"']",
        r"eyJhbGciOiJub25l",  # alg=none base64
    ],
    "ssti": [
        r"\{\{.*\}\}",
        r"\$\{.*\}",
        r"<%.*%>",
    ],
    "open_redirect": [
        r"(?i)https?://[^/]*(evil|attacker|malicious)",
    ],
}


class WAFAction(Enum):
    ALLOW = "allow"
    LOG = "log"
    BLOCK = "block"


@dataclass
class WAFMatch:
    category: str
    pattern: str
    matched_text: str
    severity: str  # low, medium, high, critical


class WebApplicationFirewall:
    """
    [PHASE6] Detect common web attacks in HTTP request payloads.

    Operates on:
    - Query parameters
    - Path
    - Headers (selective)
    - Request body (JSON, form)
    """

    def __init__(self, mode: WAFAction = WAFAction.LOG, max_payload_size: int = 1024 * 100):
        self.mode = mode
        self.max_payload_size = max_payload_size
        self._patterns_by_category: dict[str, list[re.Pattern]] = {}
        for category, patterns in OWASP_TOP_10_PATTERNS.items():
            self._patterns_by_category[category] = [
                re.compile(p) for p in patterns
            ]
        self._stats: dict[str, int] = {}

    def scan_text(self, text: str, source: str = "unknown") -> list[WAFMatch]:
        """[PHASE6] Scan a text for malicious patterns."""
        if not text or len(text) > self.max_payload_size:
            return []

        matches: list[WAFMatch] = []
        for category, patterns in self._patterns_by_category.items():
            for pattern in patterns:
                m = pattern.search(text)
                if m:
                    severity = self._severity_for(category)
                    matches.append(
                        WAFMatch(
                            category=category,
                            pattern=pattern.pattern,
                            matched_text=m.group(0)[:200],
                            severity=severity,
                        )
                    )
                    self._stats[category] = self._stats.get(category, 0) + 1
                    logger.warning(
                        f"[WAF] {severity.upper()} {category} detected in {source}: "
                        f"{m.group(0)[:80]}"
                    )
        return matches

    def _severity_for(self, category: str) -> str:
        """[PHASE6] Map attack category to severity."""
        return {
            "sql_injection": "critical",
            "command_injection": "critical",
            "xxe": "high",
            "ssrf": "high",
            "xss": "high",
            "path_traversal": "high",
            "ssti": "high",
            "nosql_injection": "high",
            "jwt_attack": "critical",
            "open_redirect": "medium",
            "ldap_injection": "medium",
        }.get(category, "low")

    def is_safe(self, text: str, source: str = "unknown") -> tuple[bool, list[WAFMatch]]:
        """[PHASE6] Quick check: is this text safe?"""
        matches = self.scan_text(text, source)
        if not matches:
            return True, []

        if self.mode == WAFAction.BLOCK:
            return False, matches
        # LOG mode: always allow but log
        return True, matches

    def get_stats(self) -> dict[str, int]:
        """[PHASE6] Get WAF detection stats."""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """[PHASE6] Reset detection stats."""
        self._stats.clear()


# [PHASE6] Singleton
_waf: WebApplicationFirewall | None = None


def get_waf() -> WebApplicationFirewall:
    """[PHASE6] Get the singleton WAF."""
    global _waf
    if _waf is None:
        # Read mode from env
        import os

        mode_str = os.environ.get("ADAM_WAF_MODE", "log")
        mode = {
            "allow": WAFAction.ALLOW,
            "log": WAFAction.LOG,
            "block": WAFAction.BLOCK,
        }.get(mode_str, WAFAction.LOG)
        _waf = WebApplicationFirewall(mode=mode)
    return _waf
