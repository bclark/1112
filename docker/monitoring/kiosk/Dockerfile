FROM alpine:latest

RUN apk add --no-cache \
    chromium \
    nginx \
    openbox \
    dbus \
    font-noto \
    font-noto-emoji \
    xset \
    xrandr \
    xdpyinfo \
    curl \
    bash

COPY nginx.conf /etc/nginx/http.d/default.conf
COPY kiosk-rotator.html /usr/share/nginx/html/kiosk-rotator.html
COPY start-kiosk.sh /usr/local/bin/start-kiosk.sh
RUN chmod +x /usr/local/bin/start-kiosk.sh

CMD ["/usr/local/bin/start-kiosk.sh"]
