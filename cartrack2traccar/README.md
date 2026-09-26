# Cartrack to Traccar Bridge

Polls the Cartrack Fleet API for live vehicle positions and forwards them
to your local Traccar server using the OsmAnd HTTP protocol.

## Features

- Polls Cartrack `GET /vehicles/status` for all vehicles in your fleet
- Forwards lat/lon/speed/heading/ignition/odometer to Traccar via OsmAnd (port 5055)
- Handles Cartrack rate limits (429) with automatic back-off
- Exponential back-off on consecutive errors
- Auto-starts with Home Assistant (`boot: auto`)
- Configurable poll interval (default: 30 seconds)

## Installation

1. Copy this entire `cartrack2traccar/` folder to `/addons/cartrack2traccar/` on your Home Assistant instance
   - You can use the Samba, SSH, or File Editor add-ons to do this
2. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
3. Click the **⋮** menu (top right) → **Check for updates**
4. The "Cartrack to Traccar Bridge" should appear under **Local add-ons**
5. Click it, then click **Install**
6. Go to the **Configuration** tab and fill in your Cartrack credentials and settings
7. Start the add-on

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `cartrack_username` | Your Cartrack API username | (required) |
| `cartrack_password` | Your Cartrack API password | (required) |
| `cartrack_region` | Two-letter country code (e.g. `za`, `ng`, `ke`) | `za` |
| `traccar_host` | IP/hostname of your Traccar server | `10.0.0.247` |
| `traccar_osmand_port` | Traccar OsmAnd protocol port | `5055` |
| `poll_interval_seconds` | How often to poll Cartrack (seconds) | `30` |
| `log_level` | Logging verbosity (`debug`, `info`, `warning`, `error`) | `info` |

## Prerequisites

- Your Traccar server must have the OsmAnd protocol enabled on port 5055
- You need valid Cartrack API credentials (generated from Fleetweb → Settings → API Settings)
