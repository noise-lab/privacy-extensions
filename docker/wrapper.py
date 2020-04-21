# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging.config
import random
import re
import subprocess
import time
import uuid

from database import Database


def run(log, database, experiment, browser, configurations, domains):
    random.shuffle(domains)
    for domain in domains:
        # We always visit with the website without any extensions first to
        # warm up the upstream DNS cache.
        run_configuration(log, None, experiment, browser, "", domain)

        random.shuffle(configurations)
        for extensions in configurations:
            run_configuration(log, database, experiment, browser, extensions, domain)


def run_configuration(log, database, experiment, browser, extensions, domain):
    log.info(f"Collecting extended HAR via {browser} with '{extensions}' for '{domain}'")
    try:
        extended_har, har_error = get_extended_har(log, browser, extensions, domain)
        har_uuid = uuid.uuid1()

        if database and not database.insert(experiment, browser, extensions, domain,
                                            har_uuid, extended_har, har_error):
            log.info(f"Saved extended HAR via {browser} with '{extensions}' for '{domain}'")
    except Exception as e:
        log.error(f"Unknown error for domain '{domain}': {e}")


def get_extended_har(log, browser, extensions, domain):
    try:
        cmd = ["docker", "run", "--rm",
               "--security-opt", "seccomp=seccomp.json",
               "--cap-add", "SYS_ADMIN",
               f"privacy-extensions-{browser}",
               "--extensions", extensions, f"http://{domain}"]
        run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        log.error(f"Error in container for '{domain}': {e.output}")
        har = None

    try:
        har = run.stdout.decode('utf-8')
        har_error = None
    except Exception as e:
        log.error(f"Error decoding output for domain {domain}: {e}")
        har_error = run.stderr.decode('utf-8')
        har = None

    if not har or har == " ":
        log.error(f"Output is empty for domain '{domain}'")
        har = None
        har_error = run.stderr.decode('utf-8')
        json_har = None
    else:
        try:
            json_har = json.loads(har)
            for entry in json_har['har']['entries']:
                if 'text' in entry['response']['content']:
                   del entry['response']['content']['text']
            # If zero-bytes remain after stripping content, we remove them.
            # We are removing zero bytes from the JSON file even though they are
            # technically correct because we don't care for the places they can
            # occur and PostgreSQL chokes on them.
            har_reassembled = json.dumps(json_har)
            if "\\u0000" in har_reassembled:
                har_stripped = re.sub(r"(\\)+u0000", "", har_reassembled)
                json_har = json.loads(har_stripped)
        except Exception as e:
            log.error(f"Error decoding HAR for domain '{domain}': {e}")
            har_error = str(e)
            json_har = None

    return json_har, har_error


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('log', default="measurement.log")
    parser.add_argument('database_config_file')
    parser.add_argument('domains_list_file')
    parser.add_argument('experiment')
    parser.add_argument('browser')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, level=logging.DEBUG)
    log = logging.getLogger('wrapper')

    database = Database.init_from_config_file(args.database_config_file)

    if args.browser not in ('firefox', 'chrome'):
        raise ValueError(f"Browser must be 'firefox' or 'chrome', not '{args.browser}'")

    with open(args.domains_list_file, 'r') as f:
        domains = [line.strip() for line in f]

    extensions_configurations = [
        # No extensions
        "",
        # Extensions on their own
        "adblock_plus",
        "decentraleyes",
        "disconnect",
        "ghostery_privacy_ad_blocker",
        "https_everywhere",
        "noscript_security_suite",
        "privacy_badger",
        "ublock_origin",
        # Combinations
        "decentraleyes,privacy_badger,ublock_origin"
    ]

    log.info("Starting new run")
    start_time = time.time()
    run(log, database, args.experiment, args.browser, extensions_configurations, domains)
    log.info(f"Elapsed time: {time.time() - start_time} seconds")


if __name__ == '__main__':
    main()
