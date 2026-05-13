#!/usr/bin/env python3
"""
Downloads movie poster images from Amazon CDN and saves them to the
nginx static folder so they are served at /images/<filename>.

Run inside the API container:
    python scripts/download_posters.py

The save path /usr/share/nginx/html/images is the bind-mounted
frontend/images/ directory, so files written here are immediately
visible to nginx without a restart.
"""
import os

import httpx

SAVE_DIR = "/usr/share/nginx/html/images"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

POSTERS = [
    (
        "dune.jpg",
        "https://image.tmdb.org/t/p/w500/8b8R8l88Qje9dn9OE8PY05Nxl1X.jpg",
    ),
    (
        "oppenheimer.jpg",
        "https://m.media-amazon.com/images/M/MV5BMDBmYTZjNjUtN2M1MS00MTQ2LTk2ODgtNzc2M2Qy"
        "ZGE5NTVjXkEyXkFqcGdeQXVyNzAwMjU2MTY@._V1_.jpg",
    ),
    (
        "darkknight.jpg",
        "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg",
    ),
    (
        "interstellar.jpg",
        "https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZk"
        "NWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg",
    ),
    (
        "inception.jpg",
        "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_.jpg",
    ),
    (
        "batman.jpg",
        "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
    ),
    (
        "avatar.jpg",
        "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg",
    ),
    (
        "topgun.jpg",
        "https://m.media-amazon.com/images/M/MV5BZWYzOGEwNTgtNWU3NS00ZTQ0LWJkODUtMmVhMjIw"
        "MjA1ZmQwXkEyXkFqcGdeQXVyMjkwOTAyMDU@._V1_.jpg",
    ),
]


def main() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"Saving posters to {SAVE_DIR}\n")

    ok = failed = 0
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for filename, url in POSTERS:
            dest = os.path.join(SAVE_DIR, filename)
            print(f"  {filename:<22}", end=" ")
            try:
                r = client.get(url)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(r.content)
                print(f"✓  {len(r.content) // 1024} KB")
                ok += 1
            except Exception as exc:
                print(f"✗  {exc}")
                failed += 1

    print(f"\n{ok} downloaded, {failed} failed.")


if __name__ == "__main__":
    main()
