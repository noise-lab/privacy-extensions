#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import csv
import io
import os
import signal
import subprocess
import threading


class PerfEventsCSVDialect(csv.Dialect):
    delimiter = ' '
    lineterminator = '\n'
    quoting = csv.QUOTE_NONE
    skipinitialspace = True


class PerfEvents(threading.Thread):
    def __init__(self, timeout):
        self._timeout = timeout
        threading.Thread.__init__(self)

    def run(self):
        try:
            cmd = ["perf_4.19", "stat", "record",
                   "-e", "cpu-clock",
                   "-e", "cpu-migrations",
                   "-e", "context-switches",
                   "-e", "page-faults",
                   "-e", "task-clock",
                   "-a", "--", "sleep", f"{self._timeout + 1}"]
            self.process = subprocess.Popen(cmd,
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
            self.process.wait()
        except subprocess.CalledProcessError as e:
            log.error(f"Error collecting performance events: {e}")

    def stop(self):
        try:
            # Grep process id of sleep
            cmd = ["pgrep", "-P", f"{self.process.pid}"]
            run = subprocess.run(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
            pid = int(run.stdout.strip().decode('utf-8'))
            if pid:
                os.kill(pid, signal.SIGTERM)
                os.kill(pid, signal.SIGKILL)
        except subprocess.CalledProcessError as e:
            log.error(f"Error stopping performance event sleep: {e}")

        self.process.wait()
        return self.parse()

    def parse(self):
        # Parse performance data
        cmd = ["perf_4.19", "script"]
        run = subprocess.run(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
        csv_dict = csv.DictReader(io.StringIO(run.stdout.decode('utf-8')),
                                dialect=PerfEventsCSVDialect)

        # Transpose and merge results
        perf = collections.defaultdict(int)
        for row in csv_dict:
            perf[row['EVENT']] += int(row['VAL'])

        return perf
