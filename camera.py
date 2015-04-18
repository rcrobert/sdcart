import sys
from subprocess import call, Popen, PIPE
import threading
from Queue import Queue


class CameraThreaded(threading.Thread):

    # Compiled executable to run
    detect_exe = 'objectdetect'

    # Directory containing all cascades
    cascade_directory = '/home/pi/izot-sdk/izot/testing/cart_project/cascades'

    # Name of text file containing all cascade names
    cascade_list = 'cascade_list.txt'

    def __init__(self):
        super(CameraThreaded, self).__init__()
        self.completed_item_queue = Queue(maxsize=20)

        # Create threading Events for control
        self.image_event = threading.Event()
        self.process_event = threading.Event()
        self.term_event = threading.Event()
        self.image_complete_event = threading.Event()
        self.process_complete_event = threading.Event()

        self.image_name = '/home/pi/izot-sdk/izot/testing/cart_project/images/img_capture.jpg'

    def run(self):
        while True:
            # check termination signal for safely ending thread
            if self.term_event.is_set():
                # perform any necessary cleanup steps
                break

            # Wait for signal to take a picture
            if self.image_event.is_set():
                # Use fswebcam to take picture
                Popen(['fswebcam', '-q', '-r', '500x350', '--no-banner', self.image_name]).communicate()

                # Reset flags
                self.image_event.clear()
                self.image_complete_event.set()

            # Wait for signal to process an image
            if self.process_event.is_set():
                (out, err) = Popen(['python2.7', 'script_thread.py', self.image_name], stdout=PIPE).communicate()

                # Process which items it could be based on what it receives
                result_list = out.strip().split(';')

                possible_items = []
                for each in result_list:
                    # Clear out empty list items
                    if each == '':
                        continue

                    possible_items.append(each.split(':'))

                # Place the list of region/classifier pairs in the Queue
                self.completed_item_queue.put(possible_items)

                # Reset flags
                self.process_event.clear()
                self.process_complete_event.set()
            # else:

    def take_picture(self):
        self.image_complete_event.clear()
        self.image_event.set()

    def process_image(self):
        self.process_complete_event.clear()
        self.process_event.set()

    @property
    def image_complete(self):
        if self.image_complete_event.is_set():
            self.image_complete_event.clear()
            return True
        else:
            return False

    @property
    def processing_complete(self):
        if self.process_complete_event.is_set():
            self.process_complete_event.clear()
            return True
        else:
            return False

    def get_results(self):
        # Return results after completion, unhandled Empty exception to indicate an error
        return self.completed_item_queue.get_nowait()



class CameraProcess(threading.Thread):

    # directory containing all cascades and cascade lists
    cascade_directory = ''

    # directory containing all executable tests
    executable_directory = ''

    def __init__(self):
        super(CameraProcess, self).__init__()

        # items processed are placed inside this queue
        self.completed_item_queue = Queue(maxsize=20)

        self.image_name = 'img_capture.jpg'
        self.hsv_run = ''
        self.cascade_run = ''

    def run(self):
        # Take a picture
        call(['fswebcam', '-r', '500x300', '--no-banner', self.image_name])

        # Run HSV and capture
        (out, err) = Popen([self.executable_directory + self.hsv_run, self.image_name], stdout=PIPE).communicate()

        # Parse results

        # Determine which cascade list to run
        # Run cascades and capture
        cascade_list = []
        # Build cascade list from the text file
        (out, err) = Popen([self.executable_directory + self.cascade_run])

        # Parse results

        # Return results
        # Build an Item class and place it on the queue
        # End
        pass


def main():
    import time

    t = CameraThreaded()
    t.daemon = True
    t.start()

    try:
        t.image_event.set()

        # Wait until image is taken
        while not t.image_complete_event.is_set():
            pass

        t.process_event.set()

        # Wait until OpenCV finishes
        while not t.process_complete_event.is_set():
            pass

        print t.completed_item_queue.get_nowait()
    finally:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()