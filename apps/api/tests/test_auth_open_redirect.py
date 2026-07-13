"""OAuth `next` redirect must stay same-origin — no open redirect.

The post-login redirect carries the minted Fuse JWT in the URL, so an
open redirect here leaks the token to an attacker's host. `startswith("/")`
alone is insufficient: scheme-relative `//evil.com` and `/\evil` are
treated as absolute by browsers.
"""

import pytest

from apps.api.app.features.auth.service import AuthService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _svc() -> AuthService:
    # _verify_oauth_state only touches self for JWT decode via settings —
    # a bare instance is enough to exercise the next-path guard through a
    # round-tripped state token.
    return AuthService.__new__(AuthService)


@pytest.mark.parametrize(
    ("next_in", "expected"),
    [
        ("/dashboard", "/dashboard"),
        ("/workflows/123", "/workflows/123"),
        # Open-redirect vectors → all fall back to /dashboard.
        ("//evil.com", "/dashboard"),
        ("//evil.com/path", "/dashboard"),
        ("/\\evil.com", "/dashboard"),
        ("https://evil.com", "/dashboard"),
        ("http://evil.com", "/dashboard"),
        ("evil.com", "/dashboard"),
        ("", "/dashboard"),
    ],
)
def test_oauth_next_stays_same_origin(next_in, expected):
    svc = _svc()
    state = svc._mint_oauth_state(next_in)
    assert svc._verify_oauth_state(state) == expected
