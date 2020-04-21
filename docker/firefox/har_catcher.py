#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pathlib
import struct
import sys

try:
    def get_message():
        raw_length = sys.stdin.buffer.read(4)

        if len(raw_length) == 0:
            sys.exit(0)

        length = struct.unpack('@I', raw_length)[0]
        message = sys.stdin.buffer.read(length)
        return message

    while True:
        message = get_message()
        with open("har.json", 'wb') as f:
            f.write(message)
        pathlib.Path("har.json.ready").touch()

except Exception as e:
    print("Couldn't save HAR:", e)
