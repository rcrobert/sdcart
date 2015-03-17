import threading
import sys
from Queue import Queue, Empty, Full
import time
from Tkinter import *
import pymysql

from barcode import BarcodeThreaded
from camera import CameraThreaded
from item import Item
from gui import *
from adc_driver import ADCController

# PLANNED CHANGES

# BUGS

# NOTES
# * Tkinter is NOT THREAD-SAFE. Make sure to keep all processing inside the .after callback function or inside of other
#   thread-safe data types.


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
    WRONG_ITEM = 'wrong item'

    def __init__(self):
        self.error = False
        self.error_type = None

        self.adc_controller = ADCController()

        self.busy = False
        self.produce_mode = False
        self.pending_addition = False
        self.pending_removal = False

        self._pending_item = None

        self._snapshot_weight = 0.0
        self.produce_weight = 0.0

        self.weight = 0.0
        self.expected_weight = 0.0

        # Allowed deviation in running total
        self.deviation = 0.05

    def update(self):
        # Check the new total weight
        self.weight = self.get_weight()

        # No negative weights, very small weights should be zero
        if self.weight < 2.00:
            self.weight = 0.00

        if self.expected_weight < 2.00:
            self.expected_weight = 0.00

        # Check if pending additions or removals are resolved
        if self.pending_addition:
            # If the change in weight is what we expect for the item
            if self._check_in_range(self.weight, self._snapshot_weight + self._pending_item.weight,
                                    self._pending_item.d_weight):
                # The item has been added
                self.busy = False
                self.pending_addition = False
                self._pending_item = None

            # Else if the weight has not yet changed
            elif self._check_in_range(self.weight, self._snapshot_weight, self._snapshot_weight * self.deviation):
                # Still waiting for it to be added
                self.error = True
                self.error_type = self.WAITING_FOR_ADD

            # Else there was a change but it was wrong
            else:
                self.error = True
                self.error_type = self.WRONG_ITEM

        elif self.pending_removal:
            # If the change in weight is what we expect for the item
            if self._check_in_range(self.weight, self._snapshot_weight - self._pending_item.weight,
                                    self._pending_item.d_weight):
                # The item has been removed
                self.busy = False
                self.pending_removal = False
                self._pending_item = None

            # Else if the weight has not yet changed
            elif self._check_in_range(self.weight, self._snapshot_weight, self._snapshot_weight * self.deviation):
                # Still waiting for it to be removed
                self.error = True
                self.error_type = self.WAITING_FOR_REMOVE

            # Else there was a change but it was wrong
            else:
                self.error = True
                self.error_type = self.WRONG_ITEM

        # For produce, we want to ignore security weight changes, keep produce_weight updated
        elif self.produce_mode:
            # Update produce weight
            self.produce_weight = self.get_weight() - self._snapshot_weight

            # No errors can exist in produce mode
            self.error = False

        # Check for weight mismatches
        else:
            if self._check_in_range(self.weight, self.expected_weight, self.expected_weight * self.deviation):
                # Valid weight, reset errors
                self.error = False
            else:
                # Invalid weight
                self.error = True
                self.error_type = self.OUT_OF_RANGE

    def add_item(self, item, produce=False):
        # Cannot be called if we are already busy with another operation

        if produce:
            self.expected_weight += item.weight
        else:
            # Update the new expected values
            self.expected_weight += item.weight
            # self.deviation += item.d_weight

            self._snapshot_weight = self.weight

            # Flag as busy with waiting for an addition
            self.busy = True
            self.pending_addition = True

            # Save new item
            self._pending_item = item

    def remove_item(self, item):
        # Cannot be called if we are already busy with another operation

        # Update the new expected values
        self.expected_weight -= item.weight
        # self.deviation -= item.d_weight

        # Save a temporary weight
        self._snapshot_weight = self.weight

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
                # self.deviation -= self._pending_item.d_weight

                # Reset flags
                self.busy = False
                self.pending_addition = False

                # Unsave item
                self._pending_item = None
            elif self.pending_removal:
                # Reset expected weight
                self.expected_weight += self._pending_item.weight
                # self.deviation += self._pending_item.d_weight

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
        """Get the current weight reading from the ADCs.

        Retrieves the current weight reading from the ADCs. Uses thread-safe access of their variable. If it cannot read
        the variable during the call, return the current reading.

        :return: New weight total from the ADCs if lock can be acquired, else return current weight.
        """
        # Initialize to current weight
        weight = self.weight

        # Attempt to acquire the lock
        if self.adc_controller.weight_lock.acquire(False):
            # Save the weight value
            weight = self.adc_controller.weight

            # Release the lock
            self.adc_controller.weight_lock.release()

        return weight

    @staticmethod
    def _check_in_range(actual, expected, deviation):
        if (expected - deviation) <= actual <= (expected + deviation):
            return True
        else:
            return False

        # if (self.expected_weight - self.deviation) <= self.weight <= (self.expected_weight + self.deviation):
        #     return True
        # else:
        #     return False


class CartManager(object):
    def __init__(self):
        self.pending_items = Queue(maxsize=20)
        self.item_list = []

        # Instantiate weight manager
        self.weight_manager = WeightManager()

        # Instantiate threads
        self.threads = {
            'barcode': BarcodeThreaded(scan_dir='/dev/hidraw1'),
            'camera': CameraThreaded(),
            'adc': self.weight_manager.adc_controller
        }

        # Configure threads
        self.threads['barcode'].daemon = False
        self.threads['camera'].daemon = False
        self.threads['adc'].daemon = False

        # Reset SQL cart data
        Item.CURSOR.execute("DELETE FROM shopping_cart WHERE 1")
        Item.CONN.commit()
        self.sql_update_count = 0

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

    def runtime_interrupt(self):
        """Check periodically for queue management and weight changes.

        :return: None.
        """
        try:
            # Check for items pending SQL data
            tmp = self.pending_items.get_nowait()

            tmp.request_info()

            # Add item to weight manager
            if tmp.barcode:
                self.weight_manager.add_item(tmp)
            else:
                self.weight_manager.add_item(tmp, produce=True)

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
            if self.display.current_screen == self.display.picturescreen:
                # Update produce list, unhandled Empty exception to indicate an error
                new_list = self.threads['camera'].completed_item_queue.get_nowait()

                if new_list:
                    # Clear the image
                    self.display.update_image(None)

                    # Update the list
                    self.display.update_produce_list(new_list)

                    # Clear the display weight on entry
                    self.display.set_weight(0.0)

                    # Set to produce mode
                    self.weight_manager.start_produce_mode()

                    # Change screens
                    self.display.change_screen(self.display.producescreen)
                else:
                    # Do not change screens, display something
                    self.display.set_warning_label_picture('Item not recognized')

            # Reset flag
            self.threads['camera'].process_complete_event.clear()

        # Check weight values
        self.weight_manager.update()

        # Check for errors
        if self.weight_manager.error:
            # Update the warning label
            if self.weight_manager.error_type == WeightManager.OUT_OF_RANGE:
                self.display.set_warning_label_home('Weight out of range')
            elif self.weight_manager.error_type == WeightManager.WRONG_ITEM:
                self.display.set_warning_label_home('Incorrect item')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_ADD:
                self.display.set_warning_label_home('Please add item to cart')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_REMOVE:
                self.display.set_warning_label_home('Please remove item from cart')
        else:
            # Clear the warning displayed
            self.display.set_warning_label_home('')

        # Keep display weight updated in the produce screen
        if self.display.current_screen == self.display.producescreen:
            self.display.set_weight(Item.grams_to_pounds(self.weight_manager.produce_weight))

        # Update SQL every 4th iteration
        self.sql_update_count += 1
        if self.sql_update_count == 4:
            Item.CURSOR.execute("UPDATE shopping_cart SET current_load='{}' ORDER BY scan_time LIMIT 1".format(int(self.weight_manager.weight)))
            Item.CONN.commit()
            self.sql_update_count = 0

        # Schedule another interrupt
        self.root.after(200, self.runtime_interrupt)

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
                if not self.weight_manager.busy and not self.weight_manager.error:
                    # Remove the item from our list
                    selection = kwargs.get('index')
                    tmp = self.item_list.pop(selection)

                    # Remove from display
                    self.display.remove_item(selection)

                    # Remove from remote database list
                    Item.CURSOR.execute("DELETE FROM shopping_cart WHERE item_name='{}' ORDER BY scan_time LIMIT 1".format(tmp.name))
                    Item.CONN.commit()

                    # Notify weight manager
                    self.weight_manager.remove_item(tmp)
            elif event_type == EVENT_BTN_CANCEL:
                # Must be an action pending
                if self.weight_manager.cancel_operation():
                    # Cancel pending action
                    tmp = self.item_list.pop()

                    Item.CURSOR.execute("DELETE FROM shopping_cart WHERE item_name='{}' ORDER BY scan_time LIMIT 1".format(tmp.name))
                    Item.CONN.commit()

                    # Remove from display
                    self.display.remove_item(self.display.get_num_items() - 1)

        # Handle picture screen events
        elif self.display.current_screen == self.display.picturescreen:
            if event_type == EVENT_BTN_ACCEPT:
                # Make sure an image has been taken
                if self.image_taken:
                    # Display that it is processing
                    self.display.set_warning_label_picture('Processing...')

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
                # Produce cannot be weight 0
                if self.weight_manager.produce_weight > 2.0:
                    # Stop produce measurement
                    self.weight_manager.end_produce_mode()

                    # Queue the selected item for processing
                    item = Item(name=kwargs.get('selection'), weight=self.weight_manager.produce_weight)
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
