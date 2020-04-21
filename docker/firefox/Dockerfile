FROM debian:stable-slim

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

ENV FIREFOX_VERSION=68.0.2
ENV GECKODRIVER_VERSION=0.24.0
ENV HAR_VERSION=0.6.2

# Mozilla Firefox
# ===============
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget ca-certificates bzip2 gzip \
        libgtk-3-0 libx11-xcb1 libdbus-glib-1-2 libxt6

RUN wget -q https://ftp.mozilla.org/pub/firefox/releases/${FIREFOX_VERSION}/linux-x86_64/en-US/firefox-${FIREFOX_VERSION}.tar.bz2 -O /tmp/firefox.tar.bz2  && \
    tar -xf /tmp/firefox.tar.bz2 -C /opt/ && \
    rm /tmp/firefox.tar.bz2

RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz -O /tmp/geckodriver.tar.gz && \
    tar -xf /tmp/geckodriver.tar.gz -C /usr/local/bin/ && \
    rm /tmp/geckodriver.tar.gz

# HAR Export
# ==========
RUN apt-get install -y --no-install-recommends \
        python3 python3-pip linux-perf procps libcap2-bin

RUN setcap cap_sys_admin+ep /usr/bin/perf_4.19

ADD requirements.txt /tmp/
RUN pip3 install -U -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

ADD har_catcher.json /usr/lib/mozilla/native-messaging-hosts/

RUN useradd -ms /bin/bash seluser
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

ADD extensions/ \
    /home/seluser/measure/extensions

ADD harexporttrigger-${HAR_VERSION}-fx.xpi \
    run.py \
    perfevents.py \
    har_catcher.py \
    /home/seluser/measure/

RUN chown seluser:seluser -R /home/seluser/measure

USER seluser

WORKDIR /home/seluser/measure

ENTRYPOINT ["python3", "/home/seluser/measure/run.py"]
