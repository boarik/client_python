from abc import abstractmethod, ABCMeta
from contextlib import contextmanager, AbstractContextManager
from functools import wraps
from threading import Thread, Event
import logging
import time


class _ReportThread(Thread):
    def __init__(self, reporter, interval, prefix):
        super(_ReportThread, self).__init__()
        self._reporter = reporter
        self._reporting_interval = interval
        self._prefix = prefix
        self._stop_event = Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._reporter.report_now(prefix=self._prefix)
            except Exception:
                logging.exception("Report via threaded push failed")

            self._wait_loop()

    def _wait_loop(self):
        now = time.time()
        wait_until = now + self._reporting_interval
        time.sleep(max(0., wait_until - now))

    def reset(self):
        self._stop_event.clear()

    def stop(self):
        self._stop_event.set()


class _ReportContext(AbstractContextManager):
    def __init__(self, reporter, report_on_failure=True):
        super(_ReportContext, self).__init__()
        self._reporter = reporter
        self._report_on_failure = report_on_failure

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and not self._report_on_failure:
            return

        self._reporter.report_now()


class Reporter(object, metaclass=ABCMeta):
    def __init__(self, registry=None):
        self._registry = registry

    def context(self, report_on_failure=True):
        return _ReportContext(reporter=self, report_on_failure=report_on_failure)

    def decorate(self, report_on_failure=True):
        def decorator(func):
            @wraps(func)
            def inner(*args, **kwargs):
                with _ReportContext(reporter=self, report_on_failure=report_on_failure):
                    return func(*args, **kwargs)

            return inner

        return decorator

    def start(self, interval=30.0, prefix=""):
        thread = _ReportThread(reporter=self, interval=interval, prefix=prefix)
        thread.daemon = True
        thread.start()
        return thread

    @abstractmethod
    def report_now(self, prefix=""):
        pass


@contextmanager
def silence_errors(log_errors=True):
    try:
        yield
    except Exception:
        if log_errors:
            logging.exception("Silenced raised exception")

        pass


def example():
    class MyReporter(Reporter):
        def report_now(self, prefix="Hello"):
            print("%s World!" % prefix)

    reporter = MyReporter()

    # No report is done: decorating a failing function where the decorator doesn't report on error.
    with silence_errors(log_errors=False):
        @reporter.decorate(report_on_failure=False)
        def fail():
            print("Failing")
            raise ValueError("fail")

        fail()

    # A report is done: failing inside a reporter context in which reporting on error is allowed.
    with silence_errors(log_errors=False):
        with reporter.context(report_on_failure=True):
            print("Failing 2")
            raise ValueError("fail2")

    # Report once every second: using a threaded reporter with an interval of 1 second.
    thread = reporter.start(prefix="Hi", interval=1)
    time.sleep(2)
    thread.stop()


if __name__ == "__main__":
    example()
