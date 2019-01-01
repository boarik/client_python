from prometheus_client.local.reporter import Reporter


class InfluxContextReporter(Reporter):
    def __init__(self, influxdb_client, registry):
        super(InfluxContextReporter, self).__init__(registry)
        self._influxdb_client = influxdb_client

    def report_now(self, prefix=""):
        json_body = []
        for metric in self._registry.collect():
            for sample in metric.samples:
                json_body.append(
                    _transform_prometheus_metric_sample_to_influx_point(prefix, sample)
                )

        self._influxdb_client.write_points(json_body)


def _transform_prometheus_metric_sample_to_influx_point(prefix, prometheus_metric_sample):
    measurement_name = prometheus_metric_sample.name
    if prefix:
        measurement_name = "%s.%s" % (prefix, measurement_name)

    return {
        "measurement": measurement_name,
        "tags": prometheus_metric_sample.labels,
        "time": prometheus_metric_sample.timestamp,
        "fields": {
            "value": prometheus_metric_sample.value
        }
    }
