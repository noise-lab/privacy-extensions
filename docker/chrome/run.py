#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

from datetime import datetime

import perfevents

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('website')
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--extensions')
    parser.add_argument('--extensions-wait', type=int, default=15)
    args = parser.parse_args()

    # Start X
    vdisplay = Display(visible=False, size=(1920, 1080))
    vdisplay.start()

    # Prepare Chrome
    options = Options()
    options.headless = False
    options.add_argument("no-sandbox")
    options.add_argument("auto-open-devtools-for-tabs")
    options.add_extension("/home/seluser/measure/harexporttrigger-0.6.3.crx")
    options.binary_location = "/usr/bin/google-chrome-stable"

    # Install other addons
    extensions_path = pathlib.Path("/home/seluser/measure/extensions")
    if args.extensions:
        for extension in args.extensions.split(","):
            matches = list(extensions_path.glob("{}*.crx".format(extension)))
            if matches and len(matches) == 1:
                options.add_extension(str(matches[0]))

    # Launch Chrome and install our extension for getting HARs
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(args.timeout)

    # Start perf timer
    perf = perfevents.PerfEvents(args.timeout)

    # We need to wait for everything to open up properly
    time.sleep(args.extensions_wait)

    # Make a page load
    perf.start()
    started = datetime.now()
    driver.get(args.website)

    # Once the HAR is on disk in the container, write it to stdout so the host machine can get it
    har_file = "/home/seluser/measure/har.json"

    def har_file_ready():
        return pathlib.Path(har_file + ".ready").exists()

    while (datetime.now() - started).total_seconds() < args.timeout and not har_file_ready():
        time.sleep(1)

    # Stop collecting performance data
    perf_data = perf.stop()

    # Read HAR file
    har = {}
    if har_file_ready():
        with open(har_file, 'r') as f:
            har = json.load(f)

    driver.quit()
    vdisplay.stop()

    json.dump({'har': har, 'perf': perf_data}, sys.stdout)


if __name__ == '__main__':
    main()
