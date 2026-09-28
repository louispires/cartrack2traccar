#!/usr/bin/env python3
"""
Cartrack → Traccar Bridge

Polls the Cartrack Fleet API for vehicle positions and forwards them
to a local Traccar server via the OsmAnd HTTP protocol (port 5055).

Environment variables (set by run.sh from HA add-on config):
  CARTRACK_USERNAME         Cartrack API username
  CARTRACK_PASSWORD         Cartrack API password
  CARTRACK_REGION           Two-letter region code (e.g. "za")
  TRACCAR_HOST              Traccar server hostname/IP
  TRACCAR_OSMAND_PORT       Traccar OsmAnd protocol port (default 5055)
  POLL_INTERVAL             Seconds between polls (default 30)
  POLL_INTERVAL_MOVING      Seconds between polls while any vehicle is moving (default 5)
  LOG_LEVEL                 Logging level (debug/info/warning/error)
"""

import logging
import os
import sys
import time
import urllib.parse
from datetime import datetime, timezone

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CARTRACK_USERNAME = os.environ.get("CARTRACK_USERNAME", "")
CARTRACK_PASSWORD = os.environ.get("CARTRACK_PASSWORD", "")
CARTRACK_REGION = os.environ.get("CARTRACK_REGION", "za")
TRACCAR_HOST = os.environ.get("TRACCAR_HOST", "10.0.0.247")
TRACCAR_OSMAND_PORT = int(os.environ.get("TRACCAR_OSMAND_PORT", "5055"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
POLL_INTERVAL_MOVING = max(1, int(os.environ.get("POLL_INTERVAL_MOVING", "5")))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()

# Cartrack base URL — Kenya and Saudi Arabia use karooooo.com domain
if CARTRACK_REGION.lower() in ("ke", "sa"):
    CARTRACK_BASE_URL = f"https://fleetapi-{CARTRACK_REGION.lower()}.karooooo.com"
else:
    CARTRACK_BASE_URL = f"https://fleetapi-{CARTRACK_REGION.lower()}.cartrack.com"

TRACCAR_OSMAND_URL = f"http://{TRACCAR_HOST}:{TRACCAR_OSMAND_PORT}"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("cartrack2traccar")

# ---------------------------------------------------------------------------
# Cartrack API client
# ---------------------------------------------------------------------------


def fetch_vehicle_status() -> list[dict]:
    """
    GET /rest/vehicles/status — returns the latest snapshot for all vehicles.
    Rate limit: 60 requests per minute.

    Returns a list of vehicle status dicts from the Cartrack API.
    """
    url = f"{CARTRACK_BASE_URL}/rest/vehicles/status"
    headers = {"Accept": "application/json"}

    log.debug("Fetching vehicle status from %s", url)

    try:
        resp = requests.get(
            url,
            auth=(CARTRACK_USERNAME, CARTRACK_PASSWORD),
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        log.error("Network error calling Cartrack API: %s", exc)
        return []

    if resp.status_code == 429:
        retry_after = resp.headers.get("X-RateLimit-Retry-After-Seconds", "60")
        log.warning("Rate limited by Cartrack API — waiting %ss", retry_after)
        time.sleep(int(retry_after))
        return []

    if resp.status_code == 401:
        log.error(
            "Authentication failed (HTTP 401). Check credentials and region (%s).",
            CARTRACK_REGION,
        )
        return []

    if resp.status_code != 200:
        log.error(
            "Cartrack API returned HTTP %d: %s",
            resp.status_code,
            resp.text[:500],
        )
        return []

    try:
        body = resp.json()
    except ValueError:
        log.error("Failed to parse JSON response from Cartrack")
        return []

    # The response is typically {"data": [...]} or a bare list
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        return body.get("data", body.get("vehicles", []))
    return []


def is_moving(vehicle: dict) -> bool:
    """True if the vehicle has ignition on or a non-zero speed."""
    ignition = vehicle.get("ignition")
    if ignition is not None and str(ignition).strip().lower() in ("true", "1", "on", "yes"):
        return True
    try:
        return float(vehicle.get("speed") or 0) > 0
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Traccar OsmAnd forwarder
# ---------------------------------------------------------------------------

# Persistent HTTP session for Traccar forwarding
_traccar_session = requests.Session()


def forward_to_traccar(vehicle: dict) -> bool:
    """
    Send a single vehicle position to Traccar via the OsmAnd HTTP protocol.

    Expected vehicle dict fields (Cartrack API):
      - registration (str): vehicle registration / plate number
      - latitude (float)
      - longitude (float)
      - speed (float): speed in km/h
      - heading / bearing (float): direction in degrees
      - timestamp / lastUpdated (str): ISO 8601 timestamp
      - ignition (bool, optional)
      - odometer (float, optional)
    """
    # Extract registration as the device identifier
    device_id = vehicle.get("registration") or vehicle.get("vehicleId")
    if not device_id:
        log.debug("Skipping vehicle with no registration: %s", vehicle)
        return False

    # Sanitise device ID for use as Traccar identifier
    device_id = str(device_id).strip().replace(" ", "_")

    # Extract coordinates (Cartrack /vehicles/status nests them under "location")
    loc = vehicle.get("location") if isinstance(vehicle.get("location"), dict) else {}
    lat = loc.get("latitude") or loc.get("lat") or vehicle.get("latitude") or vehicle.get("lat")
    lon = loc.get("longitude") or loc.get("lon") or loc.get("lng") or vehicle.get("longitude") or vehicle.get("lon") or vehicle.get("lng")

    if lat is None or lon is None:
        log.debug("Skipping %s — no coordinates in vehicle payload: %s", device_id, vehicle)
        return False

    # Parse timestamp
    ts_raw = (
        loc.get("updated")
        or vehicle.get("event_ts")
        or vehicle.get("timestamp")
        or vehicle.get("lastUpdated")
        or vehicle.get("gpsTimestamp")
        or vehicle.get("last_updated")
    )
    if ts_raw:
        # Try parsing ISO/date format, or pass raw timestamp
        try:
            # Handle space-separated date and tz, e.g. "2023-01-01 12:00:00+00:00"
            clean_ts = str(ts_raw).replace("Z", "+00:00").replace(" ", "T")
            ts = int(datetime.fromisoformat(clean_ts).timestamp())
        except (ValueError, TypeError):
            try:
                ts = int(float(ts_raw))
            except (ValueError, TypeError):
                ts = int(time.time())
    else:
        ts = int(time.time())

    # Build OsmAnd query parameters
    params = {
        "id": device_id,
        "lat": float(lat),
        "lon": float(lon),
        "timestamp": ts,
        "valid": "true",
    }

    # Optional fields
    speed = vehicle.get("speed")
    if speed is not None:
        try:
            # Cartrack returns km/h; Traccar OsmAnd default unit is knots
            params["speed"] = round(float(speed) * 0.539957, 2)
        except (ValueError, TypeError):
            pass

    heading = vehicle.get("bearing") or vehicle.get("heading") or vehicle.get("direction")
    if heading is not None:
        try:
            params["bearing"] = float(heading)
        except (ValueError, TypeError):
            pass

    altitude = vehicle.get("altitude")
    if altitude is not None:
        try:
            params["altitude"] = float(altitude)
        except (ValueError, TypeError):
            pass

    # Forward custom attributes
    ignition = vehicle.get("ignition")
    if ignition is not None:
        params["ignition"] = str(ignition).lower()

    odometer = vehicle.get("odometer") or vehicle.get("mileage")
    if odometer is not None:
        try:
            # If odometer > 100000, Cartrack sends meters -> convert to km for Traccar totalDistance
            odo_val = float(odometer)
            params["totalDistance"] = round(odo_val / 1000.0, 2) if odo_val > 10000 else round(odo_val, 2)
        except (ValueError, TypeError):
            pass

    # Battery (TCU battery percentage)
    batt = vehicle.get("tcu_percentage") or vehicle.get("tcu_battery_percentage")
    if batt is not None:
        try:
            params["batt"] = float(batt)
        except (ValueError, TypeError):
            pass

    # External battery voltage
    vext = vehicle.get("vext")
    if vext is not None:
        try:
            params["power"] = float(vext)
        except (ValueError, TypeError):
            pass

    # Position description / address from Cartrack
    pos_desc = loc.get("position_description")
    if pos_desc:
        params["address"] = pos_desc

    # Send to Traccar
    try:
        resp = _traccar_session.get(TRACCAR_OSMAND_URL, params=params, timeout=10)
        if resp.status_code == 200:
            log.debug("Forwarded %s → Traccar (lat=%.5f lon=%.5f)", device_id, float(lat), float(lon))
            return True
        else:
            log.warning(
                "Traccar returned HTTP %d for %s: %s",
                resp.status_code,
                device_id,
                resp.text[:200],
            )
            return False
    except requests.RequestException as exc:
        log.error("Failed to forward %s to Traccar: %s", device_id, exc)
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    log.info("=" * 60)
    log.info("Cartrack → Traccar Bridge starting")
    log.info("  Cartrack region : %s", CARTRACK_REGION)
    log.info("  Cartrack API URL: %s", CARTRACK_BASE_URL)
    log.info("  Traccar OsmAnd  : %s", TRACCAR_OSMAND_URL)
    log.info("  Poll interval   : %ds (moving: %ds)", POLL_INTERVAL, POLL_INTERVAL_MOVING)
    log.info("=" * 60)

    if not CARTRACK_USERNAME or not CARTRACK_PASSWORD:
        log.error("Cartrack credentials not configured! Set cartrack_username and cartrack_password in add-on config.")
        sys.exit(1)

    consecutive_errors = 0
    moving = False

    while True:
        try:
            vehicles = fetch_vehicle_status()

            if vehicles:
                success_count = 0
                for v in vehicles:
                    if forward_to_traccar(v):
                        success_count += 1

                now_moving = any(is_moving(v) for v in vehicles)
                if now_moving != moving:
                    log.info(
                        "Vehicle motion %s — polling every %ds",
                        "detected" if now_moving else "stopped",
                        POLL_INTERVAL_MOVING if now_moving else POLL_INTERVAL,
                    )
                moving = now_moving

                log.info(
                    "Poll complete: %d/%d vehicles forwarded to Traccar",
                    success_count,
                    len(vehicles),
                )
                consecutive_errors = 0
            else:
                log.warning("No vehicles returned from Cartrack API")
                consecutive_errors += 1

        except Exception:
            log.exception("Unexpected error in main loop")
            consecutive_errors += 1

        # Back-off on repeated errors (max 5 min)
        if consecutive_errors > 0:
            backoff = min(POLL_INTERVAL * (2 ** min(consecutive_errors, 5)), 300)
            log.info("Backing off for %ds (consecutive errors: %d)", backoff, consecutive_errors)
            time.sleep(backoff)
        else:
            time.sleep(POLL_INTERVAL_MOVING if moving else POLL_INTERVAL)


if __name__ == "__main__":
    main()
