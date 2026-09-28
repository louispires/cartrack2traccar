# AGENTS.md

Home Assistant add-on repository. The add-on polls Cartrack Fleet API (`/rest/vehicles/status`) and forwards each vehicle position to Traccar via OsmAnd HTTP (GET query params, port 5055); a Lovelace dashboard visualises the resulting Traccar entities. User-facing docs: [README.md](README.md) (repo + dashboard), [cartrack2traccar/README.md](cartrack2traccar/README.md) (add-on).

## Layout

- [repository.yaml](repository.yaml) — HA add-on repository manifest; each add-on is a subfolder containing a `config.yaml`.
- [cartrack2traccar/cartrack2traccar.py](cartrack2traccar/cartrack2traccar.py) — entire app: env config → `fetch_vehicle_status()` → `forward_to_traccar()` per vehicle → `main()` poll loop with exponential back-off (max 300s).
- [cartrack2traccar/run.sh](cartrack2traccar/run.sh) — bashio entrypoint; maps HA add-on options to env vars, then `exec python3`.
- [cartrack2traccar/config.yaml](cartrack2traccar/config.yaml) — add-on manifest (version, arch, `options` defaults, `schema` types).
- [cartrack2traccar/translations/en.yaml](cartrack2traccar/translations/en.yaml) — UI labels for each option.
- [cartrack2traccar/Dockerfile](cartrack2traccar/Dockerfile) + [cartrack2traccar/build.yaml](cartrack2traccar/build.yaml) — Alpine 3.19 HA base images per arch.
- [dashboards/traccar-fleet-dashboard.yaml](dashboards/traccar-fleet-dashboard.yaml) — raw Lovelace config (pasted into HA's raw editor, not deployed by the add-on).
- `proxmox-jobs.sqlite3.*` at root are unrelated local artifacts — ignore, don't edit or commit.

## Conventions

- **Adding/renaming a config option touches 6 places** (all under `cartrack2traccar/`): `options` + `schema` in [config.yaml](cartrack2traccar/config.yaml), [translations/en.yaml](cartrack2traccar/translations/en.yaml), `export` in [run.sh](cartrack2traccar/run.sh), `os.environ.get` (with default) plus module docstring in [cartrack2traccar.py](cartrack2traccar/cartrack2traccar.py), and the Configuration table in [add-on README](cartrack2traccar/README.md) (also the YAML sample in root [README.md](README.md)). HA option names are `snake_case`; env vars are `UPPER_CASE` and may differ (e.g. `poll_interval_seconds` → `POLL_INTERVAL`).
- Bump `version` in [config.yaml](cartrack2traccar/config.yaml) for any shipped change — HA only offers updates on version change.
- Dependencies: stdlib + `requests` only. Installed via `apk` (`py3-*` packages) in [Dockerfile](cartrack2traccar/Dockerfile), not pip. New deps must exist as Alpine 3.19 packages or the Dockerfile must change.
- Secrets use schema type `password`. Never log credentials or full auth headers.
- Cartrack payload shape is not strictly known: field extraction uses `or`-chained fallbacks (nested `location` dict first, then top-level aliases). Keep that pattern when adding fields; wrap numeric casts in `try/except (ValueError, TypeError)`.
- Functions return empty/`False` on failure and log; only `main()` catches broad exceptions.

## Domain pitfalls

- Region `ke`/`sa` use `fleetapi-<region>.karooooo.com`; others use `fleetapi-<region>.cartrack.com`.
- Speed: Cartrack km/h → OsmAnd knots (`× 0.539957`).
- Odometer: values `> 10000` treated as meters and converted to km for `totalDistance` (heuristic; inline comment says 100000 — code is authoritative).
- Traccar device identifier = registration with spaces → `_`. Changing this breaks existing Traccar device mappings.
- Cartrack rate limit: 60 req/min; 429 honours `X-RateLimit-Retry-After-Seconds`.

## Dashboard

- Entity IDs (`device_tracker.<name>`, `sensor.<name>_{address,speed,altitude,supply_voltage,battery}`, `binary_sensor.<name>_{motion,status}`) come from HA's Traccar integration, named after the Traccar device name — not the bridge's registration-based identifier.
- Vehicle names (`suzuki_jimny`, `isuzu_kb250`) are hardcoded per view; adding a vehicle means duplicating a view and its fleet-overview section.
- Built-in cards only (no `custom:` cards / HACS). Keep it that way unless asked.
- `sensor.*_address` requires Traccar reverse geocoding (see root [README.md](README.md)).

## Run / test

No test suite or linter configured. Run locally (PowerShell, from `cartrack2traccar/`):

```powershell
$env:CARTRACK_USERNAME="..."; $env:CARTRACK_PASSWORD="..."; $env:TRACCAR_HOST="127.0.0.1"; $env:LOG_LEVEL="debug"
python cartrack2traccar.py
```

Container build (from `cartrack2traccar/`) needs the base image arg, e.g. `docker build --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19 .` ([run.sh](cartrack2traccar/run.sh) requires bashio, so it only works inside HA base images).
