#!/usr/bin/env python3
"""
update_data.py — daily data refresh for the dashboard.

Runs in GitHub Actions (see .github/workflows/update-data.yml). Two jobs,
both hitting the PUBLIC game/companion APIs directly — no API token, no
proxy/worker:

  1. data/countries.json — country bonus reference from warerastats. The
     browser can't fetch warerastats cross-origin (it only sends CORS
     headers for localhost), so we cache it server-side here and the page
     reads the committed file same-origin.

  2. data/wealth.json — appends one wealth snapshot per UTC day for the
     single tracked user, so the wealth chart grows over time. The latest
     reading wins for the current day (idempotent if run more than once).

Wealth is public: user.getUserById returns stats.wealth = {total, companies,
items, money, equipments, weapons} — the figures shown under WEALTH in-game.

Run:  python scripts/update_data.py
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_ID    = "69de159fa03070cad5b1cc09"   # toie
API_BASE   = "https://api2.warera.io/trpc"
WSTATS_URL = "https://api.warerastats.io/countries"
UA         = "warera-toie-dashboard/1.0 (+github actions)"

ROOT       = Path(__file__).resolve().parent.parent
DATA       = ROOT / "data"
WEALTH_KEYS = ("total", "companies", "items", "money", "equipments", "weapons")

MAX_RETRIES = 3
TIMEOUT     = 30


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def http_json(url):
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, TimeoutError) as e:
            last = e
            if attempt < MAX_RETRIES:
                time.sleep(3 * attempt)
    raise RuntimeError(f"GET failed after {MAX_RETRIES} attempts: {url} :: {last}")


def trpc(method, payload):
    inp = urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
    return (http_json(f"{API_BASE}/{method}?input={inp}") or {}).get("result", {}).get("data")


# ── countries.json ──────────────────────────────────────────────────────
def update_countries(now_iso):
    raw = http_json(WSTATS_URL)
    slim = [{
        "countryId":     c["countryId"],
        "name":          c.get("name"),
        "specializedItem": c.get("specializedItemCode") or None,
        "productionBonus": c.get("productionBonusPercentage") or 0,
        "industrialism": c.get("industrialism") or 0,
        "incomeTax":     c.get("incomeTaxPercentage") or 0,
    } for c in raw if c.get("countryId")]
    out = {"updatedAt": now_iso, "countries": slim}
    (DATA / "countries.json").write_text(
        json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"countries.json: wrote {len(slim)} countries")


# ── wealth.json ─────────────────────────────────────────────────────────
def update_wealth(now_iso, today):
    path = DATA / "wealth.json"
    rec = None
    if path.exists():
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            rec = None
    if not isinstance(rec, dict) or not isinstance(rec.get("snapshots"), list):
        rec = {"userId": USER_ID, "username": "toie", "snapshots": []}

    data = trpc("user.getUserById", {"userId": USER_ID})
    wealth = (data or {}).get("stats", {}).get("wealth")
    if not isinstance(wealth, dict) or wealth.get("total") is None:
        log("wealth.json: no wealth data returned; leaving file unchanged")
        return
    if data.get("username"):
        rec["username"] = data["username"]

    point = {"t": now_iso}
    for k in WEALTH_KEYS:
        v = wealth.get(k)
        if isinstance(v, (int, float)):
            point[k] = round(float(v), 2)

    snaps = rec["snapshots"]
    if snaps and isinstance(snaps[-1].get("t"), str) and snaps[-1]["t"][:10] == today:
        snaps[-1] = point          # replace today's existing point
        action = "replaced today's"
    else:
        snaps.append(point)
        action = "appended new"
    path.write_text(json.dumps(rec, separators=(",", ":")), encoding="utf-8")
    log(f"wealth.json: {action} point total=₿{point.get('total')} ({len(snaps)} total)")


def main():
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    today = now_iso[:10]
    DATA.mkdir(parents=True, exist_ok=True)
    update_countries(now_iso)
    update_wealth(now_iso, today)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
