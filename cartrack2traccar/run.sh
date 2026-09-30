#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Read config from Home Assistant add-on options
export CARTRACK_USERNAME="$(bashio::config 'cartrack_username')"
export CARTRACK_PASSWORD="$(bashio::config 'cartrack_password')"
export CARTRACK_REGION="$(bashio::config 'cartrack_region')"
export TRACCAR_HOST="$(bashio::config 'traccar_host')"
export TRACCAR_OSMAND_PORT="$(bashio::config 'traccar_osmand_port')"
export POLL_INTERVAL="$(bashio::config 'poll_interval_seconds')"
export POLL_INTERVAL_MOVING="$(bashio::config 'poll_interval_moving_seconds')"
export STALE_TIMEOUT="$(bashio::config 'stale_timeout_seconds')"
export LOG_LEVEL="$(bashio::config 'log_level')"

bashio::log.info "Starting Cartrack to Traccar Bridge..."
bashio::log.info "  Region: ${CARTRACK_REGION}"
bashio::log.info "  Traccar: ${TRACCAR_HOST}:${TRACCAR_OSMAND_PORT}"
bashio::log.info "  Poll interval: ${POLL_INTERVAL}s (moving: ${POLL_INTERVAL_MOVING}s)"
bashio::log.info "  Stale timeout: ${STALE_TIMEOUT}s"

exec python3 /cartrack2traccar.py
