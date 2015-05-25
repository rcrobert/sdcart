from Queue import Queue, Empty
from Tkinter import *
import pymysql

from subprocess import call, Popen, PIPE

from barcode import BarcodeThreaded
from camera import CameraThreaded
from item import Item
from gui import DisplayManager, DisplayEvent
from weight import IncrementalWeightManager
from database import Database, NoItem
# from PWM import LED

# PLANNED CHANGES

# BUGS
# * Crashes when camera.py calls Popen in response to a GUI event. Could be issues with memory limitations or it could
#   be that the new scripts were not loaded on the Pi yet and caused a crash. Unlikely since a call to fswebcam was
#   able to crash it. If memory is an issue, do not keep the producescreen or picturescreen loaded, load them
#   dynamically as needed.

#   UPDATE: Not memory, able to remove DisplayManager.producescreen or add 4 more instances and no effect on runtime
#   behavior.

#   Calling Popen also crashes it when called inside of main. It is not a permissions issue, running as sudo still
#   crashes. Using call() instead of Popen() does not fix it. Popen() is not raising any exceptions. Popen() crashes on
#   any process opened including 'date'.

#   Maybe this Popen call is not thread-safe?

#   SOLVED: Including the PWM/LED library causes subprocess.Popen() and subprocess.call() to fail.

# NOTES
# * Tkinter is NOT THREAD-SAFE. Make sure to keep all processing inside the .after callback function or inside of other
#   thread-safe data types.


class CartManager(object):
    def __init__(self):
        self.pending_items = Queue(maxsize=20)
        self.item_list = []
        self.last_item = None

        # Initialize LEDs
        # LED.initLeds()
        # LED.statusLedsOFF()

        # Instantiate weight manager
        self.weight_manager = IncrementalWeightManager()

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
        self.second_count = 0
        self.weight_tare_count = 0

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

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass

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

        # For items scanned or completed via produce selection, add them to the internal cart list and the SQL database
        try:
            # Check for items waiting to be added to the cart
            tmp = self.pending_items.get_nowait()

            # Produce items already have SQL data, populate others
            if not tmp.is_produce:
                try:
                    Database.request_info(tmp)

                    # Add item to weight manager
                    self.weight_manager.add_item(tmp)

                    # Update current list of items
                    self.item_list.append(tmp)

                    # Update displayed list
                    self.display.add_item(tmp)

                    # Update SQL database shopping cart
                    Database.add_to_cart(tmp)
                except NoItem:
                    # Item does not exist in database
                    self.display.enable_popup_button()
                    self.display.show_popup()
                    self.display.set_popup_text('Unrecognized barcode.')
                    self.weight_manager.set_red_lights()
            else:
                # Give it a deviation
                tmp.d_weight = 15.0

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
        if self.threads['camera'].image_complete:
            # Update the image and set flag
            self.image_taken = True
            self.display.update_image(self.threads['camera'].image_name)

        # Check for OpenCV processing completion
        if self.threads['camera'].processing_complete:
            if self.display.current_screen == self.display.picturescreen:
                # Update produce list
                classifier_list = self.threads['camera'].get_results()
                print classifier_list

                if classifier_list:
                    # Clear the image
                    self.display.update_image(None)

                    # Construct items from the names returned by OpenCV
                    new_items = Database.get_produce_list(classifier_list)

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

        # Check weight values
        self.weight_manager.update()

        # Check for errors
        if self.weight_manager.error:
            # Set LEDs red
            # LED.statusLedsRED()

            # Update weight manager warnings on Homescreen
            if self.display.current_screen == self.display.homescreen:
                if self.weight_manager.error_type == IncrementalWeightManager.OUT_OF_RANGE_HIGH:
                    # Display popup warning without a button
                    self.display.disable_popup_button()
                    self.display.show_popup()
                    # self.display.set_popup_text('Foreign item in cart\nActual: {}g'.format(self.weight_manager._get_weight()))
                    self.display.set_popup_text('Foreign item in cart.')

                elif self.weight_manager.error_type == IncrementalWeightManager.OUT_OF_RANGE_LOW:
                    # Display popup warning without a button
                    self.display.disable_popup_button()
                    self.display.show_popup()
                    # self.display.set_popup_text('Missing item from cart\nActual: {}g'.format(self.weight_manager._get_weight()))
                    self.display.set_popup_text('Missing item from cart.')

                elif self.weight_manager.error_type == IncrementalWeightManager.WRONG_ITEM:
                    # Display popup warning without a button
                    self.display.disable_popup_button()
                    self.display.show_popup()
                    if self.weight_manager._pending_item:
                        # self.display.set_popup_text('Incorrect item.\nActual: {}g\nExpected: {}g'.format(self.weight_manager.weight_reading, self.weight_manager._pending_item.weight))
                        self.display.set_popup_text('Incorrect item.')
                    else:
                        self.display.set_popup_text('Incorrect item.')

                elif self.weight_manager.error_type == IncrementalWeightManager.WAITING_FOR_ADD:
                    # Display popup warning without a button
                    self.display.disable_popup_button()
                    self.display.show_popup()
                    self.display.set_popup_text('Please add item to cart')

                elif self.weight_manager.error_type == IncrementalWeightManager.WAITING_FOR_REMOVE:
                    # Display popup warning without a button
                    self.display.disable_popup_button()
                    self.display.show_popup()
                    self.display.set_popup_text('Please remove item from cart')
        else:
            # Clear weight manager warnings on Homescreen
            if self.display.current_screen == self.display.homescreen and not self.display.is_button_popup():
                self.display.hide_popup()

        # Keep display weight updated in the produce screen
        if self.display.current_screen == self.display.producescreen:
            self.display.set_weight(self.weight_manager.grams_to_pounds(self.weight_manager.produce_weight))

        # Update SQL every nth iteration
        self.second_count += 1

        # if self.weight_manager.busy:
        #     self.weight_tare_count = 0

        if self.second_count == 5:
            # Update the weight every second
            Database.update_weight(self.weight_manager.total_weight)

            # Increment our weight tare timer
            if not self.weight_manager.busy:
                # Clear the scale if we have any small accumulated errors
                if not self.weight_manager.busy and abs(self.weight_manager.weight_reading) <= 10.0:
                    self.weight_manager.tare()

            # TODO Remove this shit
            # self.display.homescreen._warning_string.set('Actual: {}g'.format(self.weight_manager.weight_reading))

            # Reset counter
            self.second_count = 0

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
                self.root.destroy()
            elif event.type == DisplayEvent.EVENT_BTN_REMOVEITEM:
                # Do not allow if items are still pending
                if not self.weight_manager.busy and not self.weight_manager.error:

                    # Remove the item from our list
                    self.last_item = self.item_list.pop(self.item_list.index(event.selection))

                    # Update the display
                    event.handle_event()

                    # Remove from remote database list
                    Database.remove_from_cart(event.selection)

                    # Notify weight manager
                    self.weight_manager.remove_item(event.selection)
            elif event.type == DisplayEvent.EVENT_BTN_CANCEL:
                # Must be an action pending
                if self.weight_manager.busy:
                    if self.weight_manager.pending_addition:
                        tmp = self.item_list.pop()
                        Database.remove_from_cart(tmp)
                    elif self.weight_manager.pending_removal:
                        self.item_list.append(self.last_item)
                        Database.add_to_cart(self.last_item)

                    # Cancel the expected weight action
                    self.weight_manager.cancel_operation()

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
                    self.threads['camera'].process_image()
            elif event.type == DisplayEvent.EVENT_BTN_NEWIMAGE:
                # Set flag to take a picture, completion is checked in runtime_interrupt
                self.threads['camera'].take_picture()
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
