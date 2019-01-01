import json
import logging

from prometheus_client.local.reporter import Reporter


class LogStreamReporter(Reporter):
    def __init__(self, registry, stream=None, tag="METRIC"):
        super(LogStreamReporter, self).__init__(registry)

        handler = logging.StreamHandler(stream)

        log_format = "%(message)s"
        if tag:
            log_format = "{}: %(message)s".format(tag)

        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger = logging.getLogger("METRIC")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        self.logger = logger

    def report_now(self, prefix=""):
        for measurement in self._collect_measurement(prefix):
            self.logger.info(json.dumps(measurement, sort_keys=True))

    def _collect_measurement(self, prefix):
        for metric in self._registry.collect():
            for sample in metric.samples:
                yield _transform_prometheus_metric_sample_to_measurment_json(prefix, sample)


def _transform_prometheus_metric_sample_to_measurment_json(prefix, prometheus_metric_sample):
    measurement_name = prometheus_metric_sample.name
    if prefix:
        measurement_name = "%s.%s" % (prefix, measurement_name)

    return {
        "measurement": measurement_name,
        "tags": prometheus_metric_sample.labels,
        "time": prometheus_metric_sample.timestamp,
        "value": prometheus_metric_sample.value,
    }


def example():
    from collections import namedtuple
    import time

    Metric = namedtuple("Metric", ["samples"])
    Sample = namedtuple("Sample", ["name", "labels", "timestamp", "value"])

    class MyRegistry(object):
        def collect(self):
            for i in range(10):
                name = "metric_%d" % i
                group = i % 2
                yield Metric(
                    samples=[
                        Sample(name, {"group": group, "owner": "A"}, time.time(), i / 3.),
                        Sample(name, {"group": group, "owner": "B"}, time.time(), str(i)),
                    ]
                )

    reporter = LogStreamReporter(registry=MyRegistry())
    reporter.report_now(prefix="example")


if __name__ == "__main__":
    example()
