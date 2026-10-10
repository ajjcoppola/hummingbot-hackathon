#!/usr/bin/env bash
# Install watchdog/reporter systemd units on Hermes.
# Run on the droplet as a user with sudo:
#   sudo ./scripts/hermes/install_systemd.sh [--enable]
# --enable: systemctl enable --now (only when Hermes owns the race; not while Mac is primary).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UNIT_SRC="${ROOT}/scripts/hermes/systemd"
ENABLE=0
if [[ "${1:-}" == "--enable" ]]; then
  ENABLE=1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "re-run with sudo" >&2
  exit 1
fi

RUN_USER="${SUDO_USER:-${USER}}"
if [[ "$RUN_USER" == "root" ]]; then
  echo "Set SUDO_USER or pass a non-root owner; refusing User=root in units" >&2
  exit 1
fi

if ! command -v zsh >/dev/null 2>&1; then
  echo "zsh required (launch_mainnet_*.sh). apt-get install -y zsh" >&2
  exit 1
fi

for unit in hummingbot-mainnet-watchdog.service hummingbot-mainnet-reporter.service; do
  src="${UNIT_SRC}/${unit}"
  dst="/etc/systemd/system/${unit}"
  sed "s/REPLACE_USER/${RUN_USER}/g" "$src" >"$dst"
  chmod 644 "$dst"
  echo "installed $dst (User=${RUN_USER})"
done

systemctl daemon-reload

if [[ "$ENABLE" -eq 1 ]]; then
  systemctl enable --now hummingbot-mainnet-watchdog.service
  systemctl enable --now hummingbot-mainnet-reporter.service
  systemctl --no-pager status hummingbot-mainnet-watchdog.service hummingbot-mainnet-reporter.service || true
else
  echo "units installed but not enabled. When Hermes owns the race:"
  echo "  sudo systemctl enable --now hummingbot-mainnet-watchdog hummingbot-mainnet-reporter"
fi
