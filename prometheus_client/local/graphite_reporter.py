#!/usr/bin/python
from __future__ import unicode_literals

import re
import socket
import time

from prometheus_client.local.reporter import Reporter

# Roughly, have to keep to what works as a file name.
# We also remove periods, so labels can be distinguished.

_INVALID_GRAPHITE_CHARS = re.compile(r"[^a-zA-Z0-9_-]")


def _sanitize(s):
    return _INVALID_GRAPHITE_CHARS.sub("_", s)


class GraphiteReporter(Reporter):
    def __init__(self, address, registry, timeout_seconds=30, _timer=time.time):
        super(GraphiteReporter, self).__init__(registry)
        self._address = address
        self._registry = registry
        self._timeout = timeout_seconds
        self._timer = _timer

    def report_now(self, prefix=""):
        now = int(self._timer())
        output = []

        prefixstr = ""
        if prefix:
            prefixstr = prefix + "."

        for metric in self._registry.collect():
            for s in metric.samples:
                if s.labels:
                    labelstr = "." + ".".join(
                        ["{0}.{1}".format(
                            _sanitize(k), _sanitize(v))
                            for k, v in sorted(s.labels.items())])
                else:
                    labelstr = ""
                output.append("{0}{1}{2} {3} {4}\n".format(
                    prefixstr, _sanitize(s.name), labelstr, float(s.value), now))

        conn = socket.create_connection(self._address, self._timeout)
        conn.sendall("".join(output).encode("ascii"))
        conn.close()
