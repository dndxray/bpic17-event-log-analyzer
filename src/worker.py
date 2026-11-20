import queue
import threading


class Worker:
    def __init__(self, func, args=()):
        self._results = queue.Queue()
        self._thread = threading.Thread(target=self._run, args=(func, args), daemon=True)

    def start(self):
        self._thread.start()

    def _run(self, func, args):
        try:
            self._results.put(("ok", func(*args)))
        except Exception as exc:
            self._results.put(("error", exc))

    def poll(self):
        try:
            return self._results.get_nowait()
        except queue.Empty:
            return None


def run_async(widget, func, args, on_done, on_error, interval=200):
    worker = Worker(func, args)
    worker.start()

    def check():
        outcome = worker.poll()
        if outcome is None:
            widget.after(interval, check)
            return
        kind, value = outcome
        (on_done if kind == "ok" else on_error)(value)

    widget.after(interval, check)