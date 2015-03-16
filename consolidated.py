import threading
import sys
from Queue import Queue, Empty, Full
import time
from Tkinter import *

from barcode import BarcodeThreaded
from camera import CameraThreaded
from item import Item
from gui import *

# PLANNED CHANGES
# * Need to add weight sensing into the mix for certain produce items. They are already put into the pending item Queue
#   but they should not be placed in the pending item Queue until their weight is measured fully. Do we need another
#   screen? Or do we display the delta weight on the produce confirmation screen? Either way weight needs to be
#   populated before it is placed into pending items.
#
# * Need to add some sort of halt flag to the barcode thread. When it is expecting an item to be added, it should not be
#   allowed to scan a new item.
#
# * See above. We also need to have a cancel button in HomeScreen to cancel a pending barcode item being added to the
#   cart if they change their mind.

# BUGS

# NOTES
# * Tkinter is NOT THREAD-SAFE. Make sure to keep all processing inside the .after callback function or inside of other
#   thread-safe data types.

# Maybe have something like pending_addition and pending_removal. We only allow one at a time and one of each.

# pending_addition means we are watching new weight and either updating the display on ProduceScreen or comparing it to
# the weight we are expecting. Once ProduceScreen is accepted or the weight matches, we cancel pending_addition.

# pending_removal means we are watching new weight and a reduction equal to the removed item. In the case of removing
# produce, we do need to add some tolerance values as the floating point weights will never be identical. Produce should
# probably just include some expected % error.

# the weight sensing should probably be its own module
# ISSUE: do we require that an item be scanned before being added to the cart? Yes
# ISSUE: do we require that an item be removed in the GUI before being removed from the cart? for simplicity Yes
# for above issues, working in both directions is very complicated

# Members
# busy - binary flag that is set while in produce_mode, or while waiting for add_item or remove_item
#
# Methods
# add_item(Item item) this will tell it that an item of a specific weight has been scanned into the cart
# start_produce_mode() maybe just a binary flag
# end_produce_mode()
# remove_item(Item item) this will tell it that an item of a specific weight hsa been requested to be removed


class WeightManager(object):
    WAITING_FOR_ADD = 'waiting for add'
    WAITING_FOR_REMOVE = 'waiting for remove'
    OUT_OF_RANGE = 'out of range'

    def __init__(self):
        self.error = False
        self.error_type = None

        self.busy = False
        self.produce_mode = False
        self.pending_addition = False
        self.pending_removal = False

        self._pending_item = None

        self._snapshot_weight = 0.0
        self.produce_weight = 0.0

        self.weight = 0.0
        self.expected_weight = 0.0
        self.deviation = 0.0

    def update(self):
        # Check the new total weight
        self.weight = self.get_weight()

        # Check if pending additions or removals are resolved
        if self.pending_addition:
            if self._check_in_range():
                # The item has been added
                self.busy = False
                self.pending_addition = False
                self._pending_item = None
            else:
                # Still waiting for it to be added
                self.error = True
                self.error_type = self.WAITING_FOR_ADD
        elif self.pending_removal:
            if self._check_in_range():
                # The item has been removed
                self.busy = False
                self.pending_removal = False
                self._pending_item = None
            else:
                # Still waiting for it to be removed
                self.error = True
                self.error_type = self.WAITING_FOR_REMOVE

        # For produce, we want to ignore security weight changes, keep produce_weight updated
        elif self.produce_mode:
            print 'Produce mode'
            # Update produce weight
            self.produce_weight = self.get_weight() - self._snapshot_weight

            # DEBUG
            self.produce_weight = 1.0

            # No errors can exist in produce mode
            self.error = False

        # Check for weight mismatches
        else:
            if self._check_in_range():
                # Valid weight, reset errors
                self.error = False
            else:
                # Invalid weight
                self.error = True
                self.error_type = self.OUT_OF_RANGE

    def add_item(self, item):
        # Cannot be called if we are already busy with another operation

        # Update the new expected values
        self.expected_weight += item.weight
        self.deviation += item.d_weight

        # Flag as busy with waiting for an addition
        self.busy = True
        self.pending_addition = True

        # Save new item
        self._pending_item = item

    def add_produce(self):
        # Increase our expected weight to match
        self.expected_weight += self.produce_weight

    def remove_item(self, item):
        # Cannot be called if we are already busy with another operation

        # Update the new expected values
        self.expected_weight -= item.weight
        self.deviation -= item.d_weight

        # Flag as busy with waiting for a removal
        self.busy = True
        self.pending_removal = True

        # Save new item
        self._pending_item = item

    def cancel_operation(self):
        # Can only be called if we are busy with another operation
        # Intended to be called with add or remove only
        if self.busy:
            if self.pending_addition:
                # Reset expected weight
                self.expected_weight -= self._pending_item.weight
                self.deviation -= self._pending_item.d_weight

                # Reset flags
                self.busy = False
                self.pending_addition = False

                # Unsave item
                self._pending_item = None
            elif self.pending_removal:
                # Reset expected weight
                self.expected_weight += self._pending_item.weight
                self.deviation += self._pending_item.d_weight

                # Reset flags
                self.busy = False
                self.pending_removal = False

                # Unsave item
                self._pending_item = None

            return True
        else:
            return False

    def start_produce_mode(self):
        # Flag as busy with produce
        self.busy = True
        self.produce_mode = True

        # Reset tracked weight
        self.produce_weight = 0.0

        # Take a snapshot of current weight
        self._snapshot_weight = self.weight

    def end_produce_mode(self):
        # Reset flags
        self.busy = False
        self.produce_mode = False

    def get_weight(self):
        return self.weight

    def _check_in_range(self):
        if (self.expected_weight - self.deviation) <= self.weight <= (self.expected_weight + self.deviation):
            return True
        else:
            return False


class CartManager(object):
    def __init__(self):
        self.pending_items = Queue(maxsize=20)
        self.completed_items = Queue(maxsize=20)
        self.item_list = []

        # Instantiate weight manager
        self.weight_manager = WeightManager()

        # Instantiate threads
        self.threads = {
            'barcode': BarcodeThreaded(scan_dir='/dev/hidraw2'),
            'camera': CameraThreaded(),
            'server': threading.Thread(target=self.server_thread_target)
        }

        # Configure threads
        self.threads['barcode'].daemon = False
        self.threads['camera'].daemon = False
        self.threads['server'].daemon = True

        # Instantiate GUI
        self.root = Tk()
        self.display = None
        self.image_taken = False
        self.produce_list = None

    def start(self):
        # Start threads
        for t in self.threads.itervalues():
            t.start()

        # Start GUI
        self.display = DisplayManager(self.root, self.gui_event_handler)
        self.root.after(250, self.runtime_interrupt)
        self.root.mainloop()

        # If we exit mainloop, we are done
        # Close all threads
        print 'Preparing to exit...'

        # Set all termination events
        for t in self.threads.itervalues():
            if not t.daemon:
                t.term_event.set()

        # Wait for all threads
        print 'Waiting for threads...'
        for t in self.threads.itervalues():
            if not t.daemon:
                t.join()
        print 'All threads shut down.'

        print 'main shutting down...'

    def server_thread_target(self):
        """Process Items from the pending item queue.

        :return: None.
        """
        while True:
            # Blocking call to check for incomplete items
            item = self.pending_items.get()

            # Simulate turnaround time
            item.request_info()
            time.sleep(0.5)

            # Place it in the complete item queue
            self.completed_items.put(item)

    def runtime_interrupt(self):
        """Check periodically for queue management and weight changes.

        :return: None.
        """
        try:
            # Check for items completed by the server
            tmp = self.completed_items.get_nowait()

            # Barcode items need to be added to the scale
            if tmp.barcode:
                self.weight_manager.add_item(tmp)

            # Update current list of items
            self.item_list.append(tmp)
            self.display.add_item(tmp)
        except Empty:
            pass

        try:
            # Check for items completed by BarcodeThreaded
            tmp = self.threads['barcode'].completed_item_queue.get_nowait()

            # If we are processing an item already, do not scan in a new one
            if not self.weight_manager.busy:
                self.pending_items.put_nowait(tmp)
        except Empty:
            pass

        # Check for picture completion
        if self.threads['camera'].image_complete_event.is_set():
            # Update the image and set flag
            self.image_taken = True
            self.display.update_image(self.threads['camera'].image_name)

            # Reset flag
            self.threads['camera'].image_complete_event.clear()

        # Check for OpenCV processing completion
        if self.threads['camera'].process_complete_event.is_set():
            # Clear the display image
            self.display.update_image(None)

            if self.display.current_screen == self.display.picturescreen:
                # Update produce list, unhandled Empty exception to indicate an error
                self.display.update_produce_list(self.threads['camera'].completed_item_queue.get_nowait())

                # Clear the display weight on entry
                self.display.set_weight(0.0)

                # Set to produce mode
                self.weight_manager.start_produce_mode()

                # Change screens
                self.display.change_screen(self.display.producescreen)

            # Reset flag
            self.threads['camera'].process_complete_event.clear()

        # Check weight values
        self.weight_manager.update()

        if self.weight_manager.error:
            # Update the warning label
            if self.weight_manager.error_type == WeightManager.OUT_OF_RANGE:
                print 'Weight out of range'
                print 'Act: ', self.weight_manager.weight
                print 'Exp: ', self.weight_manager.expected_weight
                self.display.set_warning_label('Weight out of range')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_ADD:
                print 'Please add item to cart'
                self.display.set_warning_label('Please add item to cart')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_REMOVE:
                print 'Please remove item from cart'
                self.display.set_warning_label('Please remove item from cart')
        else:
            # Clear the warning displayed
            self.display.set_warning_label('')

        # Keep display weight updated in the produce screen
        if self.display.current_screen == self.display.producescreen:
            self.display.set_weight(self.weight_manager.produce_weight)

        # Schedule another interrupt
        self.root.after(1000, self.runtime_interrupt)

    def gui_event_handler(self, event_type, **kwargs):
        """Callback function for events from the GUI.

        :param event_type: An event from gui.py.
        :param kwargs: Associated data for the event.
        :return: None.
        """

        # Handle home screen events
        if self.display.current_screen == self.display.homescreen:
            if event_type == EVENT_BTN_PRODUCE:
                # Do not allow if items are still pending
                if not self.weight_manager.busy:
                    # Move to produce screen
                    self.display.change_screen(self.display.picturescreen)

                    # Expect a picture to be taken
                    self.image_taken = False
            elif event_type == EVENT_BTN_HELP:
                # TODO: Implement Help button
                pass
            elif event_type == EVENT_BTN_REMOVEITEM:
                # Do not allow if items are still pending
                if not self.weight_manager.busy:
                    # Remove the item from our list
                    selection = kwargs.get('index')
                    tmp = self.item_list.pop(selection)

                    # Remove from display
                    self.display.remove_item(selection)

                    # Notify weight manager
                    self.weight_manager.remove_item(tmp)
            elif event_type == EVENT_BTN_CANCEL:
                # Must be an action pending
                if self.weight_manager.cancel_operation():
                    # Cancel pending action
                    self.item_list.pop()

                    # Remove from display
                    self.display.remove_item(self.display.get_num_items() - 1)

        # Handle picture screen events
        elif self.display.current_screen == self.display.picturescreen:
            if event_type == EVENT_BTN_ACCEPT:
                # Make sure an image has been taken
                if self.image_taken:
                    # Set flag to process the image, completion is checked in runtime_interrupt
                    self.threads['camera'].process_complete_event.clear()
                    self.threads['camera'].process_event.set()
            elif event_type == EVENT_BTN_NEWIMAGE:
                # Set flag to take a picture, completion is checked in runtime_interrupt
                self.threads['camera'].image_complete_event.clear()
                self.threads['camera'].image_event.set()
            elif event_type == EVENT_BTN_CANCEL:
                # Reset image flag
                self.image_taken = False

                # Clear the display image
                self.display.update_image(None)

                # Return to HomeScreen
                self.display.change_screen(self.display.homescreen)

        # Handle produce screen events
        elif self.display.current_screen == self.display.producescreen:
            if event_type == EVENT_BTN_ACCEPT:
                # Stop produce measurement
                self.weight_manager.end_produce_mode()
                self.weight_manager.add_produce()

                # Queue the selected item for processing
                # TODO: need to create produce items with a weight, use self.weight_manager.produce_weight
                item = Item(name=kwargs.get('selection'))
                self.pending_items.put_nowait(item)

                # Return to HomeScreen
                self.display.change_screen(self.display.homescreen)
            elif event_type == EVENT_BTN_NEWIMAGE:
                # Stop produce measurement
                self.weight_manager.end_produce_mode()

                # Go back to PictureScreen
                self.image_taken = False
                self.display.change_screen(self.display.picturescreen)
            elif event_type == EVENT_BTN_CANCEL:
                # Stop produce measurement
                self.weight_manager.end_produce_mode()

                # Cancel and go back to HomeScreen
                self.display.change_screen(self.display.homescreen)


def main():
    master = CartManager()
    master.start()

    sys.exit(0)


if __name__ == '__main__':
    main()
