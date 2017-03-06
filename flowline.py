#!/usr/bin/env python3

import traceback
import threading
import queue
import logging
import time


log = logging.getLogger(__name__)


class Error(Exception):
    pass

class NotReady(Error):
    pass


class FlowLine:
    SLEEPING = 1

    def __init__(self, **kwargs):
        self.sleeping = kwargs.get("sleeping", self.SLEEPING)
        self.lines = {}
        self.lock = threading.Lock()
        self.workers = []

    def resgist(self, do_work, upstream=None, downstream=None):
        """resgist a worker with upstream and downstream,
        if no upstream, it's a pure producer, and should be a generator,
        else take args from upstream,
        then put output into downstreams."""
        upstream = self._make_list(upstream)
        downstream = self._make_list(downstream)
        def worker():
            log.info("worker %s start to work", do_work.__name__)
            if not upstream:
                for output in do_work():
                    output = self._make_list(output)
                    self.put_args(output, downstream)
            else:
                while True:
                    try:
                        args = self.get_args(upstream)
                        output = do_work(*args)
                        output = self._make_list(output)
                        self.put_args(output, downstream)
                    except NotReady:
                        time.sleep(self.sleeping)
                    except Exception as e:  # noqa
                        err = traceback.format_exception(Exception, e, e.__traceback__)
                        log.error("%s error with args:%s", do_work.__name__, args)
                        log.error("%s", "".join(err))
                    if self.finished(upstream):
                        break
            self.fire_worker(downstream)
            log.info("job of worker %s is done", do_work.__name__)

        w = threading.Thread(target=worker)
        self.recruit_worker(w, upstream, downstream)


    def start(self):
        for w in self.workers:
            w.start()
        for w in self.workers:
            w.join()


    @staticmethod
    def _make_list(data):
        if not data:
            data = []
        elif isinstance(data, tuple):
            data = list(data)
        elif not isinstance(data, list):
            data = [data]
        return data

    @staticmethod
    def new_line():
        return {
            "producer": 0,
            "consumer": 0,
            "queue": queue.Queue()
        }

    def recruit_worker(self, worker, upstream, downstream):
        self.workers.append(worker)
        if upstream:
            for u in upstream:
                if u not in self.lines:
                    self.lines[u] = self.new_line()
                self.lines[u]["consumer"] += 1
        if downstream:
            for d in downstream:
                if d not in self.lines:
                    self.lines[d] = self.new_line()
                self.lines[d]["producer"] += 1

    def fire_worker(self, downstream):
        if downstream:
            for d in downstream:
                if d not in self.lines:
                    self.lines[d] = self.new_line()
                self.lines[d]["producer"] -= 1

    def finished(self, upstream):
        if not upstream:
            return True
        finish = True
        for u in upstream:
            line = self.lines[u]
            if line["producer"] > 0 or not line["queue"].empty():
                finish = False
                break
        return finish

    def get_args(self, upstream):
        if not upstream:
            return []
        args = []
        not_ready = False
        self.lock.acquire()
        for u in upstream:
            q = self.lines[u]["queue"]
            if q.empty():
                not_ready = True
                break
            else:
                args.append(q.get())
        if not_ready:
            for i, a in enumerate(args):
                u = upstream[i]
                q = self.lines[u]["queue"]
                q.put(a)
        self.lock.release()
        if not_ready:
            raise NotReady
        else:
            return args

    def put_args(self, output, downstream):
        if not output or not downstream:
            return
        if len(output) != len(downstream):
            log.error("output %s and downstream %s mismatched!", output, downstream)
            return
        for i, d in enumerate(downstream):
            if not output[i]:
                continue
            q = self.lines[d]["queue"]
            q.put(output[i])



def example_3xplus1():
    "a simple example: 3x+1 problem"
    import random

    def producer():
        for _ in range(20):
            time.sleep(1)
            yield random.randint(1, 100)

    def dispatch(x):
        if x == 1:
            return None, None, x
        if x % 2 == 1:
            return x, None, None
        else:
            return None, x, None

    def handle_even(x):
        return x // 2

    def handle_odd(x):
        return x * 3 + 1

    def just_print(x):
        print("result:", x)

    fl = FlowLine()
    fl.resgist(producer, downstream="data")
    fl.resgist(producer, downstream="data")
    fl.resgist(producer, downstream="data")
    fl.resgist(dispatch, upstream="data", downstream=["odd", "even", "print"])
    fl.resgist(handle_odd, upstream="odd", downstream="print")
    fl.resgist(handle_even, upstream="even", downstream="print")
    fl.resgist(just_print, upstream="print")
    fl.start()


if __name__ == '__main__':
    import cclog
    cclog.init()
    example_3xplus1()
