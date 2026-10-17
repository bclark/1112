#!/usr/bin/env bash
set -u

export DISPLAY=:0

# Link the host /tmp/.X11-unix socket directory dynamically so Xorg restarts survive
rm -rf /tmp/.X11-unix
ln -s /host-tmp/.X11-unix /tmp/.X11-unix

# Start system D-Bus and local nginx auth-injecting proxy on 127.0.0.1:3002
mkdir -p /run/dbus /run/nginx
dbus-daemon --system --fork 2>/dev/null || true
nginx

echo "[kiosk] Waiting for Grafana on 127.0.0.1:3000..."
until curl -sf http://127.0.0.1:3000/api/health >/dev/null 2>&1; do
  sleep 2
done
echo "[kiosk] Grafana is healthy."

while true; do
  if [ ! -S /tmp/.X11-unix/X0 ]; then
    echo "[kiosk] Waiting for X11 socket /tmp/.X11-unix/X0 (HDMI connected)..."
    sleep 3
    continue
  fi

  # Ensure openbox window manager is running on DISPLAY=:0 so --kiosk fullscreen maps properly
  if ! pgrep -x openbox >/dev/null 2>&1; then
    openbox >/dev/null 2>&1 &
    sleep 1
  fi

  # Prevent X11 screen blanking / DPMS sleep on the HDMI screen
  xset s off 2>/dev/null || true
  xset s noblank 2>/dev/null || true
  xset -dpms 2>/dev/null || true

  # Clean up stale Chromium singleton locks if container restarted
  rm -rf /tmp/chromium-kiosk/Singleton* 2>/dev/null || true

  echo "[kiosk] Launching Chromium Kiosk on DISPLAY=:0..."
  /usr/lib/chromium/chromium \
    --no-sandbox \
    --no-first-run \
    --no-default-browser-check \
    --disable-dev-shm-usage \
    --disable-gpu \
    --ozone-platform=x11 \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-features=Translate,OptimizationHints,MediaRouter \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    --window-position=0,0 \
    --window-size=1920,1080 \
    --force-device-scale-factor=0.90 \
    --user-data-dir=/tmp/chromium-kiosk \
    "http://127.0.0.1:3002/kiosk-rotator.html"

  echo "[kiosk] Chromium exited, restarting in 3s..."
  sleep 3
done
