FROM debian:stable-slim

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

ENV CHROMEDRIVER_VERSION=77.0.3865.40

# Google Chrome
# =============
RUN apt-get update && \
    apt-get -y install --no-install-recommends gnupg2 wget ca-certificates unzip

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    apt-key add -

RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/chrome.list
RUN apt-get update && \
    apt-get -y install --no-install-recommends google-chrome-stable \
        xvfb xauth x11-utils

RUN wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    rm /tmp/chromedriver.zip

# HAR Export
# ==========
ENV HAR_VERSION=0.6.3
RUN apt-get install -y --no-install-recommends \
        python3 python3-pip linux-perf procps libcap2-bin

RUN setcap cap_sys_admin+ep /usr/bin/perf_4.19

ADD requirements.txt /tmp/
RUN pip3 install -U -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

ADD har_catcher.json /etc/opt/chrome/native-messaging-hosts/

RUN useradd -ms /bin/bash seluser
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

ADD extensions/ \
    /home/seluser/measure/extensions

ADD harexporttrigger-${HAR_VERSION}.crx \
    run.py \
    perfevents.py \
    har_catcher.py \
    /home/seluser/measure/

RUN chown seluser:seluser -R /home/seluser/measure

USER seluser

WORKDIR /home/seluser/measure

ENTRYPOINT ["python3", "/home/seluser/measure/run.py"]
