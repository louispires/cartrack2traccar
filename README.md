# Cartrack → Traccar Home Assistant Repository

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg)](https://www.home-assistant.io/)
[![Traccar](https://img.shields.io/badge/Traccar-GPS%20Tracking-orange.svg)](https://www.traccar.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/louispires)

A complete fleet tracking solution integrating **Cartrack** GPS tracking into **Traccar** and **Home Assistant**.

[![Open your Home Assistant instance and show the add add-on repository dialog with this repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flouispires%2Fcartrack2traccar)

Includes:
1. **Cartrack to Traccar Bridge Add-on**: Automatically polls Cartrack's Fleet API and forwards live vehicle positions, speeds, headings, external voltage, TCU battery levels, and odometer data to Traccar via the OsmAnd HTTP protocol. Adaptive polling speeds up while a vehicle is moving.
2. **Traccar Fleet Lovelace Dashboard**: A modern, responsive Home Assistant dashboard with a keyless dark map, live route trails, vehicle dynamics gauges, and per-vehicle telemetry views (inspired by [DECS Home Systems](https://anchorapp100.github.io/globalguard/traccar.html)).

---

## 📁 Repository Structure

```
├── cartrack2traccar/          # Home Assistant Add-on
│   ├── cartrack2traccar.py    # Python bridge daemon
│   ├── config.yaml            # Add-on manifest and configuration schema
│   ├── Dockerfile             # Multi-architecture container build
│   ├── build.yaml             # Architecture build config
│   ├── run.sh                 # Container entrypoint script
│   └── translations/          # Language strings
├── dashboards/
│   └── traccar-fleet-dashboard.yaml  # Full Home Assistant Lovelace Dashboard config
├── repository.yaml            # Home Assistant Add-on Repository manifest
└── README.md
```

---

## 🚀 Home Assistant Add-on Installation

### 1. Add Repository to Home Assistant

**One click:**

[![Open your Home Assistant instance and show the add add-on repository dialog with this repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flouispires%2Fcartrack2traccar)

Then search the Add-on Store for **Cartrack to Traccar Bridge** and click **Install**.

**Manually:**

1. In Home Assistant, navigate to **Settings** → **Add-ons** → **Add-on Store**.
2. Click the three dots **⋮** (top right) → **Repositories**.
3. Add repository URL:
   ```text
   https://github.com/louispires/cartrack2traccar
   ```
4. Click **Add**, then close the modal.
5. In the Add-on Store, search for **Cartrack to Traccar Bridge** and click **Install**.

### 2. Configure the Add-on
Go to the **Configuration** tab of the add-on:

```yaml
cartrack_username: "YOUR_CARTRACK_API_USERNAME"
cartrack_password: "YOUR_CARTRACK_API_PASSWORD"
cartrack_region: "za"            # Country code: za, ng, ke, sa, etc.
traccar_host: "10.0.0.247"       # IP or hostname of your Traccar instance
traccar_osmand_port: 5055        # Default OsmAnd port
poll_interval_seconds: 30        # Polling frequency while parked
poll_interval_moving_seconds: 5  # Polling frequency while a vehicle is moving
stale_timeout_seconds: 180       # Mark vehicle stationary if telemetry stops (e.g. underground parking)
log_level: "info"
```

Start the add-on and toggle **Start on boot** and **Watchdog**.

---

## 🗺️ Enabling Reverse Geocoding in Traccar

To have Traccar resolve GPS coordinates into human-readable street addresses for `sensor.<vehicle>_address` (via OpenStreetMap Nominatim, no paid API key required):

1. Open `/addon_configs/a0d7b954_traccar/traccar.xml` (or `/share/traccar/traccar.xml`).
2. Add the following inside the `<properties>` block:

```xml
<entry key='geocoder.enable'>true</entry>
<entry key='geocoder.type'>nominatim</entry>
<entry key='geocoder.url'>https://nominatim.openstreetmap.org/reverse</entry>
```

3. Restart the **Traccar** add-on in Home Assistant.

---

## 📊 Traccar Fleet Dashboard

The dashboard configuration is located in [`dashboards/traccar-fleet-dashboard.yaml`](dashboards/traccar-fleet-dashboard.yaml).

### Views
* **Fleet Overview (`/traccar-fleet/fleet`)**:
  * Top status badges with live presence (Home/Away) and motion detection.
  * Live Dark Map tracking all fleet vehicles with 24-hour history trails.
  * Side-by-side vehicle cards with live speed, voltage, address, and quick navigation.
* **Vehicle Deep Dives (`/traccar-fleet/isuzu-kb250` & `/traccar-fleet/suzuki-jimny`)**:
  * 48-hour high-resolution route trail map.
  * Analog speedometer needle gauge with speed ranges.
  * Electrical diagnostics gauge (Supply/Alternator Voltage with low-battery warning thresholds).
  * Tracker backup battery level & Traccar server link status.

---

## 💖 Support / Sponsor

If you find this project useful and would like to support its ongoing development:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/louispires)

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
