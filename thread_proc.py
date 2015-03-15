import threading


class ThreadedProcess(threading.Thread):
    def __init__(self):
        super(ThreadedProcess, self).__init__()
        self.term_event = threading.Event()

    def run(self):
        # call user defined initialization function
        self.initialize()

        while True:
            if self.term_event.is_set():
                self.cleanup()
                break

            self.loop()

    def initialize(self):
        pass

    def loop(self):
        pass

    def cleanup(self):
        pass