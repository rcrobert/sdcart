from Tkinter import *
import tkFont
from PIL import Image, ImageTk

from item import Item

# PLANNED MIGRATION:

# BUGS

# NOTES
# * Is the Listbox good enough for our design? Do we need to grid out item properties? Probably should in the future.


########################################################################################################################
# MODULE VARIABLES
########################################################################################################################

# Button event identities
EVENT_BTN_HOME = 'btn_home'
EVENT_BTN_PRODUCE = 'btn_produce'
EVENT_BTN_REMOVEITEM = 'btn_removeitem'
EVENT_BTN_ACCEPT = 'btn_accept'
EVENT_BTN_NEWIMAGE = 'btn_newimage'
EVENT_BTN_CANCEL = 'btn_cancel'
EVENT_BTN_HELP = 'btn_help'


class DisplayManager(object):
    W_WIDTH = 800
    W_HEIGHT = 480

    def __init__(self, root, event_callback):
        self.root = root
        self.event_callback = event_callback

        # Make the window borderless and specify absolute size
        # root.overrideredirect(1)
        root.geometry('{}x{}'.format(self.W_WIDTH, self.W_HEIGHT))
        root.focus_set()

        # Bind Escape key to exit the display program
        root.bind('<Escape>', lambda e: root.destroy())

        # Instantiate all screen classes we will use
        self.current_screen = None
        self.homescreen = HomeScreen(self.root, self.event_callback)
        self.picturescreen = PictureScreen(self.root, self.event_callback)
        self.producescreen = ProduceScreen(self.root, self.event_callback)

        # Initialize with homescreen displayed
        self.change_screen(self.homescreen)

    def add_item(self, item):
        """Add a new item to the displayed list.

        :param item: Item object to add to the list.
        :return: None.
        """
        self.homescreen.add_item(item)

    def remove_item(self, index):
        """Remove an item from the displayed list.

        :param index: Index to remove from
        :return: None.
        """
        self.homescreen.remove_item(index)

    def set_warning_label_home(self, warning):
        """Update the displayed warning.

        :param warning: String to display as a warning.
        :return: None.
        """
        self.homescreen.set_warning_label(warning)

    def set_warning_label_picture(self, warning):
        """Update the displayed warning.

        :param warning: String to display as a warning.
        :return: None.
        """
        self.picturescreen.set_warning_label(warning)

    def get_num_items(self):
        """Check the number of items in the HomeScreen display.

        :return: Number of items in HomeScreen display.
        """
        return len(self.homescreen.item_list)

    def update_image(self, image_name):
        """Update the image displayed by PictureScreen

        :param image_name: String giving the image to display. Use None to display nothing.
        :return: None.
        """
        self.picturescreen.update_image(image_name)

    def update_produce_list(self, produce_list):
        """Update the list of options for ProduceScreen.

        :param produce_list: List of strings containing possible selections.
        :return: None.
        """
        self.producescreen.update_list(produce_list)

    def set_weight(self, val):
        self.producescreen.set_weight(val)

    def change_screen(self, screen):
        """Change the current screen displayed.

        :param screen: A screen type from one of the member variables.
        :return: None.
        """
        if self.current_screen:
            # Remove the current screen from the display
            self.current_screen.pack_forget()

        # TODO: get this out of tis function, wrong location
        # Perform set operations on the screen
        if screen == self.picturescreen:
            # Reset warning displays
            self.picturescreen.set_warning_label('')

            # Reset button displays
            self.picturescreen.reset_buttons()

        # Perform reset operations on the screen
        if self.current_screen == self.picturescreen:
            # Reset warning displays
            self.picturescreen.set_warning_label('')

            # Reset the button displays
            self.picturescreen.reset_buttons()

        # Display new screen and save new
        screen.pack(expand=1, fill=BOTH)
        self.current_screen = screen


class ListScreen(Frame):

    LIST_WIDTH = 540
    LIST_HEIGHT = 400

    def __init__(self, root):
        # Frame is an old-style object, cannot use super()
        Frame.__init__(self, root)

        # Configure the last row and column to be expandable

        # Initialize variables
        self.parent = root

        # DEBUG
        root.bind('<Escape>', lambda e: self.parent.destroy())

        # Build structural frames
        self.list_frame = Frame(self, height=self.LIST_HEIGHT, width=self.LIST_WIDTH)
        self.list_frame.grid(row=0, column=0, rowspan=4, columnspan=3)

        self.up_button_frame = Frame(self, height=200, width=100)
        self.up_button_frame.grid(row=0, column=3, rowspan=2)
        self.down_button_frame = Frame(self, height=200, width=100)
        self.down_button_frame.grid(row=2, column=3, rowspan=2)

        self.button1_frame = Frame(self, height=100, width=160)
        self.button1_frame.grid(row=0, column=4)
        self.button2_frame = Frame(self, height=100, width=160)
        self.button2_frame.grid(row=1, column=4)
        self.button3_frame = Frame(self, height=100, width=160)
        self.button3_frame.grid(row=2, column=4)
        self.button4_frame = Frame(self, height=100, width=160)
        self.button4_frame.grid(row=3, column=4)

    @staticmethod
    def _change_fontsize(widget, size):
        font = tkFont.Font(font=widget['font'])
        font['size'] = size
        widget.configure(font=font)


class HomeScreen(ListScreen):
    def __init__(self, root, event_callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        # initialize variables
        self._price_total = 0.0
        self.item_list = []
        self.event_callback = event_callback
        self._price_string = StringVar()
        self._price_string.set('Total: ${: .2f}'.format(self.get_price_total()))
        self._warning_string = StringVar()
        self._warning_string.set('')

        # build our buttons and place them into the grid
        self.produce_button = Button(self, text='Scan Produce', command=self._produce_button_callback)
        self.produce_button.grid(row=0, column=4, sticky=N+E+S+W)
        self._change_fontsize(self.produce_button, 14)

        self.remove_button = Button(self, text='Remove Item', command=self._remove_button_callback)
        self.remove_button.grid(row=1, column=4, sticky=N+E+S+W)
        self._change_fontsize(self.remove_button, 14)

        # TODO: put Help back in when its implemented
        self.help_button = Button(self, text='Help', command=lambda: self._help_button_callback())
        # self.help_button.grid(row=2, column=4, sticky=N+E+S+W)
        self._change_fontsize(self.help_button, 14)

        self.cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback)
        self.cancel_button.grid(row=3, column=4, sticky=N+E+S+W)
        self._change_fontsize(self.cancel_button, 14)

        # build our price label it is associated with a variable to dynamically update
        self.price_label = Label(self, textvariable=self._price_string)
        self.price_label.grid(row=4, column=1, sticky=W)
        self._change_fontsize(self.price_label, 16)

        # build our warning label it is associated with a variable to dynamically update
        self.warning_label = Label(self, textvariable=self._warning_string)
        self.warning_label.grid(row=4, column=2, columnspan=3, sticky=W)
        self._change_fontsize(self.warning_label, 14)

        # build our item list as a Listbox and associated controls
        self.item_listbox = Listbox(self)
        self._change_fontsize(self.item_listbox, 16)
        self.item_listbox.grid(row=0, column=0, columnspan=3, rowspan=4, sticky=N+E+S+W)

        self.up_button = Button(self, text='Up', command=lambda: self.item_listbox.yview_scroll(-1, UNITS))
        self._change_fontsize(self.up_button, 16)
        self.up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)
        self.down_button = Button(self, text='Down', command=lambda: self.item_listbox.yview_scroll(1, UNITS))
        self._change_fontsize(self.down_button, 16)
        self.down_button.grid(row=2, column=3, rowspan=2, sticky=N+E+S+W)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def get_price_total(self):
        """Get the current price total.

        :return: Returns the total cost of all items displayed.
        """
        return self._price_total

    def set_price_total(self, val):
        """Update the current price total and the displayed price.

        :param val: New price total to set.
        :return: None.
        """
        self._price_total = val

        self._price_string.set('Total: ${:.2f}'.format(self.get_price_total()))

    def set_warning_label(self, warning):
        """Update the displayed warning.

        :param warning: String to display as a warning.
        :return: None.
        """
        self._warning_string.set(warning)

    def add_item(self, item):
        """Add a new item to the displayed list.

        :param item: Item object to add to the list.
        :return: None.
        """
        # pull data from the item
        name = item.name
        price = item.price

        # append element
        self.item_listbox.insert(END, '{:_<40}${:>.2f}'.format(name, price))
        self.item_list.append(item)

        # update price total
        self.set_price_total(self.get_price_total() + price)

        # scroll to the bottom
        self.item_listbox.yview_scroll(len(self.item_list), UNITS)

    def remove_item(self, index):
        """Remove the currently selected item from the list and call defined callback function.

        :return: None:
        """
        # Do not attempt to remove from an empty list
        if self.item_listbox.size() != 0:
            # Get index of selection

            # remove from the display
            self.item_listbox.delete(index)

            # remove from internal list
            tmp = self.item_list.pop(index)

            # update price total
            if self.get_price_total() - tmp.price < 0.00:
                self.set_price_total(0.0)
            else:
                self.set_price_total(self.get_price_total() - tmp.price)

    def _produce_button_callback(self):
        """Pass an event through the callback function.

        :return: None.
        """
        self.event_callback(EVENT_BTN_PRODUCE)

    def _remove_button_callback(self):
        if self.item_listbox.size() != 0:
            index = self.item_listbox.index(ACTIVE)
            self.event_callback(EVENT_BTN_REMOVEITEM, index=index)

    def _help_button_callback(self):
        self.event_callback(EVENT_BTN_HELP)

    def _cancel_button_callback(self):
        self.event_callback(EVENT_BTN_CANCEL)

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    # DEBUG
    # use to build up a baseline list to work with
    def _populate_items(self):
        for i in range(20):
            tmp = Item(name='Temp Item', price=float(i))
            self.add_item(tmp)


class PictureScreen(ListScreen):
    def __init__(self, root, event_callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        self.event_callback = event_callback
        self.image = None

        self._warning_string = StringVar()
        self._warning_string.set('')

        self._take_picture_string = StringVar()
        self._take_picture_string.set('Take Picture')

        self.picture_taken = False

        # Do not display up and down buttons
        # self.up_button_frame.configure(width=50)
        # self.down_button_frame.configure(width=50)

        # Build and display buttons
        self.accept_button = Button(self, text='Accept', command=self._accept_button_callback)
        self._change_fontsize(self.accept_button, 14)

        self.take_picture_button = Button(self, textvariable=self._take_picture_string, command=self._take_picture_button_callback)
        self._change_fontsize(self.take_picture_button, 14)
        self.take_picture_button.grid(row=1, column=4, sticky=N+E+S+W)

        self.back_button = Button(self, text='Back', command=self._back_button_callback)
        self._change_fontsize(self.back_button, 14)
        self.back_button.grid(row=2, column=4, sticky=N+E+S+W)

        # Build and display label with the image taken
        self.image_label = Label(self)
        self.image_label.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        # Build and display label with advice
        self.advice_label = Label(self, text='Ensure produce item is completely visible.')
        self._change_fontsize(self.advice_label, 14)
        self.advice_label.grid(row=4, column=0, columnspan=3, sticky=N+E+S+W)

        # Build a warning label for later use
        self.warning_label = Label(self, textvariable=self._warning_string)
        self._change_fontsize(self.warning_label, 14)
        self.warning_label.grid(row=4, column=3, columnspan=2, sticky=N+E+S+W)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def update_image(self, image_name):
        """Update the image displayed on this screen.

        :param image_name: String giving the image to display. Use None to display nothing.
        :return: None.
        """
        # Remove from display
        self.image_label.grid_forget()

        if image_name:
            # Convert the new image
            self.image = ImageTk.PhotoImage(Image.open(image_name).rotate(180))

            # Update and display again
            self.image_label.configure(image=self.image)
            self.image_label.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

    def set_warning_label(self, warning):
        """Update the displayed warning.

        :param warning: String to display as a warning.
        :return: None.
        """
        self._warning_string.set(warning)

    def reset_buttons(self):
        self.picture_taken = False
        self._take_picture_string.set('Take Picture')
        self.accept_button.grid_forget()

    def set_buttons(self):
        self.picture_taken = True
        self._take_picture_string.set('New Picture')
        self.accept_button.grid(row=0, column=4, sticky=N+E+S+W)

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _accept_button_callback(self):
        self.event_callback(EVENT_BTN_ACCEPT)

    def _take_picture_button_callback(self):
        if not self.picture_taken:
            self.set_buttons()
        self.event_callback(EVENT_BTN_NEWIMAGE)

    def _back_button_callback(self):
        self.event_callback(EVENT_BTN_CANCEL)


class ProduceScreen(ListScreen):
    def __init__(self, root, event_callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        self.event_callback = event_callback
        self.produce_list = None
        self.weight_total = 0.0
        self.weight_string = StringVar()
        self.weight_string.set('{:>.2f}lbs'.format(self.weight_total))

        self.select_button = Button(self, text='Accept Weight', command=self._select_button_callback)
        self._change_fontsize(self.select_button, 14)
        self.select_button.grid(row=0, column=4, sticky=N+E+S+W)

        self.new_picture_button = Button(self, text='New Picture', command=self._new_picture_button_callback)
        self._change_fontsize(self.new_picture_button, 14)
        self.new_picture_button.grid(row=1, column=4, sticky=N+E+S+W)

        self.cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback)
        self._change_fontsize(self.cancel_button, 14)
        self.cancel_button.grid(row=2, column=4, sticky=N+E+S+W)

        self.produce_listbox = Listbox(self)
        self._change_fontsize(self.produce_listbox, 16)
        self.produce_listbox.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        self.weight_label = Label(self, textvariable=self.weight_string)
        self._change_fontsize(self.weight_label, 14)
        self.weight_label.grid(row=4, column=1, sticky=W)

        self.up_button = Button(self, text='Up', command=lambda: self.produce_listbox.yview_scroll(-1, UNITS))
        self._change_fontsize(self.up_button, 16)
        self.up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)

        self.down_button = Button(self, text='Down', command=lambda: self.produce_listbox.yview_scroll(1, UNITS))
        self._change_fontsize(self.down_button, 16)
        self.down_button.grid(row=2, column=3, rowspan=2, sticky=N+E+S+W)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def update_list(self, produce_list):
        self.produce_list = produce_list

        # Remove all items in the display
        self.produce_listbox.delete(0, END)

        # Repopulate
        for item in produce_list:
            self.produce_listbox.insert(END, item)

    def set_weight(self, val):
        # No negatives
        if val < 0.00:
            val = 0.00

        self.weight_total = val

        self.weight_string.set('{:>.2f}lbs'.format(self.weight_total))

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _select_button_callback(self):
        # Notify manager, gets passed back to top level and item is added to display list
        self.event_callback(EVENT_BTN_ACCEPT, selection=self.produce_listbox.get(ACTIVE))

    def _new_picture_button_callback(self):
        # Needs to move back a screen
        self.event_callback(EVENT_BTN_NEWIMAGE)

    def _cancel_button_callback(self):
        self.event_callback(EVENT_BTN_CANCEL)


def main():
    def other_task():
        root.after(1, other_task)

    def event_handler(event_type, **kwargs):
        print event_type
        if event_type == EVENT_BTN_ACCEPT:
            print kwargs.get('selection', 'N/A')
        elif event_type == EVENT_BTN_REMOVEITEM:
            print kwargs.get('index', 'N/A')

    root = Tk()
    myapp = DisplayManager(root, event_handler)
    # myapp.update_list(['Lettuce', 'Kale', 'Asparagus'])
    # myapp.pack(fill=BOTH, expand=True)

    # populate for debugging
    # myapp.homescreen._populate_items()

    # schedule tasks
    # root.after(1, other_task)

    # start the main loop
    root.mainloop()
    print 'exiting...'

if __name__ == '__main__':
    main()