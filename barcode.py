import threading
import select
from Queue import Queue

from item import Item


class BarcodeThreaded(threading.Thread):
    _letter_codes = {4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K',
                    15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V',
                    26: 'W', 27: 'X', 28: 'Y', 29: 'Z'}

    def __init__(self, scan_dir):
        super(BarcodeThreaded, self).__init__()
        self.scan_dir = scan_dir

        # items processed are placed inside this queue
        self.completed_item_queue = Queue(maxsize=20)

        # Create threading Events for control
        self.term_event = threading.Event()

    def run(self):
        scanner = open(self.scan_dir, mode='rb')
        code = ''
        done = False

        while True:
            # check termination signal for safely ending thread
            if self.term_event.is_set():
                scanner.close()
                break

            # non-blocking read call
            readable = select.select([scanner], [], [], 1)
            if readable[0]:
                buf = scanner.read(8)
            else:
                buf = []

            for c in buf:
                val = ord(c)

                # if we read a letter
                if 4 <= val <= 29:
                    code += self._letter_codes[val]
                # if we read a number
                elif val > 29:
                    val -= 29

                    # newline is end-of-code
                    if val == 11:
                        done = True
                    else:
                        # 0's are 10's
                        if val == 10:
                            val = 0

                        code += str(val)

                if done:
                    # queue the item, blocks until a space is available
                    self.completed_item_queue.put(Item(barcode=code))

                    # clear code
                    code = ''

                    done = False

        return

    # TODO: handle character decoding in a function possibly
    def _process_char(self, val):
        pass


class Barcode(object):
    letter_codes = {4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K',
                    15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V',
                    26: 'W', 27: 'X', 28: 'Y', 29: 'Z'}

    def __init__(self, scan_dir, log_dir=None):
        # class is deprecated
        raise DeprecationWarning('Use the BarcodeThreaded for most applications')

        self.scan_dir = scan_dir
        self.log_dir = log_dir

        self._val = 0
        self._done = False
        self._code = ''

    # need a start_scan func that is non-blocking
    def scan_wait(self):
        """Blocks until a barcode is read.

        :return: The barcode read as ASCII
        """
        self._done = False
        self._code = ''

        scanner = open(self.scan_dir, mode='rb')

        while True:
            buf = scanner.read(8)

            for c in buf:
                self._val = ord(c)

                if 4 <= self._val <= 29:
                    self._code += self.letter_codes[self._val]
                elif self._val > 29:
                    self._val -= 29

                    if self._val == 11:
                        self._done = True
                    else:
                        if self._val == 10:
                            self._val = 0

                        self._code += str(self._val)

                if self._done:
                    if self.log_dir:
                        with open(self.log_dir, mode='ab') as log:
                            log.write('$' + self._code + '~\n')

                    scanner.close()
                    return self._code

# ## TEST HARNESS ## #
if __name__ == '__main__':
    pass