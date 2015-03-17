import sys
from subprocess import call, Popen, PIPE
import threading
from Queue import Queue

from item import Item


class CameraThreaded(threading.Thread):

    # Compiled executable to run
    detect_exe = 'objectdetect'

    # Directory containing all cascades
    cascade_directory = './cascades'

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

        self.image_name = './images/img_capture.jpg'

    def run(self):
        while True:
            # check termination signal for safely ending thread
            if self.term_event.is_set():
                # perform any necessary cleanup steps
                break

            # Wait for signal to take a picture
            if self.image_event.is_set():

                # Use fswebcam to take picture
                Popen(['fswebcam', '-q', '-r', '500x300', '--no-banner', self.image_name]).communicate()

                # DEBUG
                print 'Picture Taken'

                # Reset flags
                self.image_event.clear()
                self.image_complete_event.set()

            # Wait for signal to process an image
            if self.process_event.is_set():

                # DEBUG
                print 'Processing...'

                # DEBUG
                (out, err) = Popen(['python2.7', 'script_thread.py', self.image_name], stdout=PIPE).communicate()

                # Process which items it could be based on what it receives
                result_list = out.strip().split(';')

                possible_items = []
                for item in result_list:
                    if item == '':
                        continue
                    # Split HSV and Cascade using separating colon
                    result = item.split(':')
                    region = result[0]
                    cascade = result[1]

                    # Determine item based on combination
                    # Region1:Round
                    #   - Orange, Red Apple
                    #
                    # Region2:Round
                    #   - Green Apple
                    #
                    # Region1:Banana or Region2:Banana
                    #   - Banana
                    #
                    # Region2:Asparagus
                    #   - Asparagus
                    #
                    # Region2:Lettuce or Region2:Kale
                    #   - Lettuce, Kale
                    if region == 'Region1':
                        if cascade == 'Round':
                            possible_items.append('Orange')
                            possible_items.append('Red Apple')
                        elif cascade == 'Banana':
                            possible_items.append('Banana')
                    elif region == 'Region2':
                        if cascade == 'Round':
                            possible_items.append('Green Apple')
                        elif cascade == 'Banana':
                            possible_items.append('Banana')
                        elif cascade == 'Asparagus':
                            possible_items.append('Asparagus Spears')
                        elif cascade == 'Lettuce':
                            possible_items.append('Iceberg Lettuce')
                        elif cascade == 'Kale':
                            possible_items.append('Kale')
                    elif region == 'Region3':
                        pass

                # Build an Item and place it in the Queue
                self.completed_item_queue.put(possible_items)

                # Reset flags
                self.process_event.clear()
                self.process_complete_event.set()
            # else:


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
        call(['fswebcam', '-q', '-r', '500x300', '--no-banner', self.image_name])

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
    pass
    sys.exit(0)


if __name__ == '__main__':
    main()