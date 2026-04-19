import random
import sys
import time
from typing import List

import requests

ENDPOINTS = ["/", "/health"]
# endpoints that are expected to generate HTTP errors or unreachable hosts
ERROR_ENDPOINTS = ["/notfound", "/fail", "/invalid"]
# use an invalid base URL to trigger connection errors
INVALID_URLS = ["http://localhost:9999", "http://no-such-host.local"]

USER_AGENTS: List[str] = [
    "curl/7.68.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "python-requests/2.26.0",
]

# some fake IPs to send via X-Forwarded-For
IPS = [
    "192.168.1.10",
    "10.0.0.5",
    "203.0.113.42",
    "198.51.100.23",
]


def main(count: int = 20, error_rate: float = 0.2) -> None:
    """Send random requests to the local python app.

    Arguments:
        count: total number of requests to make.
        error_rate: fraction of iterations that deliberately try to
            generate an error (either by hitting a bad endpoint or using
            an unreachable host).
    """

    url_base = "http://localhost:8000"
    for i in range(count):
        # decide whether to produce an error on this iteration
        make_error = random.random() < error_rate

        if make_error:
            # choose between a bogus endpoint (404/5xx) or an invalid host
            if random.choice([True, False]):
                path = random.choice(ERROR_ENDPOINTS)
                url = url_base + path
            else:
                url = random.choice(INVALID_URLS)
                path = url  # used only for logging
        else:
            path = random.choice(ENDPOINTS)
            url = url_base + path

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "X-Forwarded-For": random.choice(IPS),
        }
        try:
            resp = requests.get(url, headers=headers, timeout=2)
            print(f"{i+1:02d}: {path} -> {resp.status_code}")
        except Exception as e:
            print(f"{i+1:02d}: {path} -> error: {e}")
        # small delay so logs will have different timestamps
        time.sleep(0.1)


if __name__ == "__main__":
    cnt = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
    main(cnt, rate)
