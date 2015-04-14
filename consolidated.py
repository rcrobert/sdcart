import threading
import sys
from Queue import Queue, Empty, Full
import time
from Tkinter import *
import pymysql

from barcode import BarcodeThreaded
from camera import CameraThreaded
from item import Item
from gui import DisplayManager, DisplayEvent
from weight import WeightManager
from database import Database

# PLANNED CHANGES
# * Implement the new DisplayEvent class, expect instances of these to come from the DisplayManager class

# BUGS

# NOTES
# * Tkinter is NOT THREAD-SAFE. Make sure to keep all processing inside the .after callback function or inside of other
#   thread-safe data types.


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
        Database.empty_cart()
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
        """Check periodically for queue management, processing completion, and weight changes.

        :return: None.
        """
        try:
            # Check for items waiting to be added to the cart
            tmp = self.pending_items.get_nowait()

            # Produce items already have SQL data, populate others
            if not tmp.is_produce:
                Database.request_info(tmp)

            # Add item to weight manager
            self.weight_manager.add_item(tmp)

            # Update current list of items
            self.item_list.append(tmp)

            # Update displayed list
            self.display.add_item(tmp)

            # Update SQL database shopping cart
            Database.add_to_cart(tmp)
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

                    # Construct items from the names returned by OpenCV
                    new_items = []
                    for name in new_list:
                        new_items.append(Item(name=name, is_produce=True))

                    # Populate them so we have price per pound values
                    for item in new_items:
                        Database.request_info(item)

                    # Update the produce display's list
                    self.display.update_produce_list(new_items)

                    # Clear the display weight on entry
                    self.display.set_weight(0.0)

                    # Set to produce mode
                    self.weight_manager.start_produce_mode()

                    # Change screens
                    self.display.change_screen(self.display.producescreen)
                else:
                    # Do not change screens, display something
                    self.display.enable_popup_button()
                    self.display.set_popup_text('Item not recognized.\nPlease try again.')
                    self.display.show_popup()

            # Reset flag
            self.threads['camera'].process_complete_event.clear()

        # Check weight values
        self.weight_manager.update()

        # Check for errors
        if self.weight_manager.error:
            # Update the warning label
            if self.weight_manager.error_type == WeightManager.OUT_OF_RANGE:
                # Display popup warning without a button
                self.display.disable_popup_button()
                self.display.show_popup()
                self.display.set_popup_text('Weight out of range')
            elif self.weight_manager.error_type == WeightManager.WRONG_ITEM:
                # Display popup warning without a button
                self.display.disable_popup_button()
                self.display.show_popup()
                self.display.set_popup_text('Incorrect item')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_ADD:
                # Display popup warning without a button
                self.display.disable_popup_button()
                self.display.show_popup()
                self.display.set_popup_text('Please add item to cart')
            elif self.weight_manager.error_type == WeightManager.WAITING_FOR_REMOVE:
                # Display popup warning without a button
                self.display.disable_popup_button()
                self.display.show_popup()
                self.display.set_popup_text('Please remove item from cart')
        else:
            # Clear the warning displayed
            self.display.hide_popup()

        # Keep display weight updated in the produce screen
        if self.display.current_screen == self.display.producescreen:
            self.display.set_weight(self.weight_manager.grams_to_pounds(self.weight_manager.produce_weight))

        # Update SQL every nth iteration
        self.sql_update_count += 1
        if self.sql_update_count == 5:
            Database.update_weight(self.weight_manager.weight)
            self.sql_update_count = 0

        # Schedule another interrupt
        self.root.after(200, self.runtime_interrupt)

    def gui_event_handler(self, event):
        """Callback function for events from the GUI.

        :param event_type: An event from gui.py.
        :param kwargs: Associated data for the event.
        :return: None.
        """

        # Handle home screen events
        if self.display.current_screen == self.display.homescreen:
            if event.type == DisplayEvent.EVENT_BTN_PRODUCE:
                # Do not allow if items are still pending
                if not self.weight_manager.busy:
                    # Move to produce screen
                    self.display.change_screen(self.display.picturescreen)

                    # Expect a picture to be taken
                    self.image_taken = False
            elif event.type == DisplayEvent.EVENT_BTN_HELP:
                # TODO: Implement Help button
                pass
            elif event.type == DisplayEvent.EVENT_BTN_REMOVEITEM:
                # Do not allow if items are still pending
                if not self.weight_manager.busy and not self.weight_manager.error:

                    # Remove the item from our list
                    self.item_list.pop(self.item_list.index(event.selection))

                    # Update the display
                    event.handle_event()

                    # Remove from remote database list
                    Database.remove_from_cart(event.selection)

                    # Notify weight manager
                    self.weight_manager.remove_item(event.selection)
            elif event.type == DisplayEvent.EVENT_BTN_CANCEL:
                # Must be an action pending
                if self.weight_manager.cancel_operation():
                    # TODO: verify this, seems to be assuming that only additions can be canceled
                    # Cancel pending action
                    tmp = self.item_list.pop()

                    # Remove from remote database list
                    Database.remove_from_cart(event.selection)

                    # Update the display
                    event.handle_event()

        # Handle picture screen events
        elif self.display.current_screen == self.display.picturescreen:
            if event.type == DisplayEvent.EVENT_BTN_ACCEPT:
                # Make sure an image has been taken
                if self.image_taken:
                    # Display that it is processing
                    self.display.disable_popup_button()
                    self.display.set_popup_text('Processing...')
                    self.display.show_popup()

                    # Set flag to process the image, completion is checked in runtime_interrupt
                    self.threads['camera'].process_complete_event.clear()
                    self.threads['camera'].process_event.set()
            elif event.type == DisplayEvent.EVENT_BTN_NEWIMAGE:
                # Set flag to take a picture, completion is checked in runtime_interrupt
                self.threads['camera'].image_complete_event.clear()
                self.threads['camera'].image_event.set()
            elif event.type == DisplayEvent.EVENT_BTN_CANCEL:
                # Reset image flag
                self.image_taken = False

                # Clear the display image
                self.display.update_image(None)

                # Return to HomeScreen
                self.display.change_screen(self.display.homescreen)

        # Handle produce screen events
        elif self.display.current_screen == self.display.producescreen:
            if event.type == DisplayEvent.EVENT_BTN_ACCEPT:
                # Produce cannot be weight 0
                if self.weight_manager.produce_weight > 2.0:
                    # Stop produce measurement
                    self.weight_manager.end_produce_mode()

                    # Queue the selected item for processing
                    item = event.selection
                    item.weight = self.weight_manager.produce_weight
                    self.pending_items.put_nowait(item)

                    # Return to HomeScreen
                    self.display.change_screen(self.display.homescreen)
            elif event.type == DisplayEvent.EVENT_BTN_NEWIMAGE:
                # Stop produce measurement
                self.weight_manager.end_produce_mode()

                # Go back to PictureScreen
                self.image_taken = False
                self.display.change_screen(self.display.picturescreen)
            elif event.type == DisplayEvent.EVENT_BTN_CANCEL:
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
