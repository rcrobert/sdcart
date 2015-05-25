from Tkinter import *
import tkFont
from PIL import Image, ImageTk
from math import floor, ceil

from item import Item

# PLANS

# BUGS

# NOTES

########################################################################################################################
# MODULE SUPPORT FUNCTIONS
########################################################################################################################

def bind_recursive(widget, event, func):
    """Bind an event to an entire display hierarchy.

    Args:
        widget (Widget): Top widget of the display hierarchy that we want to bind an event to.
        event (String): String specifying which event should be bound to this hierarchy.
        func (function): Callback function that should be bound to this hierarchy for this event.
    Returns:
        None
    """
    children = widget.winfo_children()

    # Recursively bind handlers, depth first
    for each in children:
        bind_recursive(each, event, func)

    # Bind handler
    widget.bind(event, func)


########################################################################################################################
# MODULE CLASSES
########################################################################################################################

class DisplayEvent(object):
    """Class for passing GUI events and parameters.

    Attributes:
        EVENT_BTN_HOME (String): A valid event type for the constructor.
        EVENT_BTN_PRODUCE (String): See above.
        EVENT_BTN_REMOVEITEM (String): See above.
        EVENT_BTN_ACCEPT (String): See above.
        EVENT_BTN_NEWIMAGE (String): See above.
        EVENT_BTN_CANCEL (String): See above.
        EVENT_BTN_HELP (String): See above.

    Args:
        type (String): The type of the event as one of the class members.
        selection (optional, Item): Optional parameter for events that pass Item objects.
        action (optional, function): Optional parameter for events that expect a GUI action to be taken by the caller.
    """

    # Button event identities
    EVENT_BTN_HOME = 'btn_home'
    EVENT_BTN_PRODUCE = 'btn_produce'
    EVENT_BTN_REMOVEITEM = 'btn_removeitem'
    EVENT_BTN_ACCEPT = 'btn_accept'
    EVENT_BTN_NEWIMAGE = 'btn_newimage'
    EVENT_BTN_CANCEL = 'btn_cancel'
    EVENT_BTN_HELP = 'btn_help'

    def __init__(self, event_type, selection=None, action=None):
        self.type = event_type
        self.selection = selection
        self._action = action

    def handle_event(self):
        """Wrapper for calling the event's GUI action."""
        if self._action:
            self._action()


class DisplayManager(object):
    W_WIDTH = 800
    W_HEIGHT = 480

    def __init__(self, root, event_callback):
        self.root = root
        self.event_callback = event_callback

        # Make the window borderless and specify absolute size
        root.overrideredirect(1)
        root.geometry('{}x{}'.format(self.W_WIDTH, self.W_HEIGHT))
        root.focus_set()

        # Bind Escape key to exit the display program
        root.bind('<Escape>', lambda e: root.destroy())

        # Instantiate all screen classes we will use
        self.current_screen = None
        self.homescreen = HomeScreen(self.root, self.event_callback)
        self.picturescreen = PictureScreen(self.root, self.event_callback)
        self.producescreen = ProduceScreen(self.root, self.event_callback)
        self._popupframe = PopupFrame(self.root)

        # Initialize with homescreen displayed
        self.change_screen(self.homescreen)

    def add_item(self, item):
        """Add a new item to the displayed list.

        Args:
            item (Item): Item object to add to the list.

        Returns:
            None.
        """
        self.homescreen.add_item(item)

    def set_popup_text(self, text):
        """Update the text inside the popup window.

        Args:
            text (String): String to display in the popup.

        Returns:
            None.
        """
        self._popupframe.set_label(text)

    def show_popup(self):
        self._popupframe.open()

    def hide_popup(self):
        self._popupframe.close()

    def enable_popup_button(self):
        self._popupframe.show_button()

    def disable_popup_button(self):
        self._popupframe.hide_button()

    def is_button_popup(self):
        return self._popupframe.button_enabled

    def update_image(self, image_name):
        """Update the image displayed by PictureScreen

        Args:
            image_name (String): String giving the image to display. Use None to display nothing.

        Returns:
            None.
        """
        self.picturescreen.update_image(image_name)

    def update_produce_list(self, produce_list):
        """Update the list of options for the produce screen.

        Args:
            produce_list (list): List of Items as possible selections.

        Returns:
            None.
        """
        self.producescreen.update_list(produce_list)

    def set_weight(self, val):
        """Set the displayed weight on the produce screen.

        Args:
            val (float): Weight value to display.

        Returns:
            None.
        """
        self.producescreen.set_weight(val)

    def change_screen(self, screen):
        """Change the current screen displayed.

        Args:
            screen (ListScreen): A screen from one of the member variables.

        Returns:
            None.
        """
        if self.current_screen:
            # Remove the current screen from the display
            self.current_screen.pack_forget()

            # Hide the popup window
            self.hide_popup()

        # Perform set/reset operations on the new screen
        if screen == self.picturescreen:
            # Reset button displays
            self.picturescreen.reset_buttons()

        # Display new screen and save new
        screen.pack()
        self.current_screen = screen


class PopupFrame(Frame):
    """Frame meant to be used as a floating popup window.


    """

    WIDTH = 460
    HEIGHT = 200

    def __init__(self, root):
        # Frame is an old-style object, cannot use super()
        Frame.__init__(self, root)

        self._displayed = False

        self._label_string = StringVar()
        self._label_string.set('No Warnings')

        # Frame to give structure
        self._prop_frame = Frame(self, height=self.HEIGHT, width=self.WIDTH, bd=5, relief=RIDGE)
        self._prop_frame.grid(row=0, column=0)

        # Text label
        self._label = Label(self, textvariable=self._label_string, wraplength=400, justify=CENTER, font=("Helvetica",
                                                                                                         16, "bold"))
        self._label.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Optional close button, not displayed by default
        self.button_enabled = False
        self._button = Button(self, text='Ok', command=self._button_callback, padx=30, pady=10, font=("Helvetica", 14,
                                                                                                      "bold"))

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def set_label(self, warning):
        """Update the displayed text.

        :param warning: String to display as text.
        :return: None.
        """
        self._label_string.set(warning)

    def open(self):
        """Display the popup.

        :return: None.
        """
        if not self._displayed:
            self.place(relx=0.5, rely=0.4, anchor=CENTER)
            self._displayed = True

    def close(self):
        """Remove the popup.

        :return: None.
        """
        if self._displayed:
            self.place_forget()
            self._displayed = False

    def show_button(self):
        """Show the popup's OK button.

        :return: None.
        """
        if not self.button_enabled:
            # Adjust label placement
            self._label.place(relx=0.5, rely=0.4, anchor=CENTER)

            # Display the button
            self._button.place(relx=0.5, rely=0.9, anchor=S)

            self.button_enabled = True

    def hide_button(self):
        """Hide the popup's OK button.

        :return: None.
        """
        if self.button_enabled:
            # Adjust label placement
            self._label.place(relx=0.5, rely=0.5, anchor=CENTER)

            # Remove the button
            self._button.place_forget()

            self.button_enabled = False

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _button_callback(self):
        self.close()


class ListScreen(Frame):

    LIST_WIDTH = 540
    LIST_HEIGHT = 400

    # Tuples for shared font styles
    monospace_font = ('Courier', 16)
    button_font = (14)
    warning_font = (12)
    info_font = ("Helvetica", 18, "bold")
    price_font = ("Helvetica", 24, "bold")

    def __init__(self, root):
        # Frame is an old-style object, cannot use super()
        Frame.__init__(self, root)

        # Configure the last row and column to be expandable
        self.rowconfigure(4, weight=1)
        self.columnconfigure(4, weight=1)

        # Initialize variables
        self.parent = root

        # Build structural frames
        self.list_frame = Frame(self, height=self.LIST_HEIGHT, width=self.LIST_WIDTH)
        self.list_frame.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

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

        # Create universal warning label
        self._warning_string = StringVar()

        self.warning_label = Label(self, textvariable=self._warning_string, wraplength=260, font=self.warning_font,
                                   anchor=N+W, justify=LEFT)
        self.warning_label.grid(row=4, column=3, columnspan=2, sticky=W)

    def set_warning_label(self, warning):
        """Update the displayed warning.

        :param warning: String to display as a warning.
        :return: None.
        """
        self._warning_string.set(warning)

    @staticmethod
    def _change_fontfamily(widget, family):
        font = tkFont.Font(font=widget['font'])
        font['family'] = family
        widget.configure(font=font)

    @staticmethod
    def _change_fontsize(widget, size):
        font = tkFont.Font(font=widget['font'])
        font['size'] = size
        widget.configure(font=font)


class PictureScreen(ListScreen):
    def __init__(self, root, event_callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        self.event_callback = event_callback
        self.image = None

        # self._warning_string = StringVar()
        # self._warning_string.set('')

        self._take_picture_string = StringVar()
        self._take_picture_string.set('Take Picture')

        self.picture_taken = False

        # Do not display up and down buttons
        # self.up_button_frame.configure(width=50)
        # self.down_button_frame.configure(width=50)

        # Build and display buttons
        self.accept_button = Button(self, text='Accept', command=self._accept_button_callback, font=self.button_font)

        self.take_picture_button = Button(self, textvariable=self._take_picture_string, font=self.button_font,
                                          command=self._take_picture_button_callback)
        self.take_picture_button.grid(row=1, column=4, sticky=N+E+S+W)

        self.back_button = Button(self, text='Back', command=self._back_button_callback, font=self.button_font)
        self.back_button.grid(row=2, column=4, sticky=N+E+S+W)

        # Build and display label with the image taken
        self.list_frame.pack_propagate(False)
        self.image_label = Label(self.list_frame)
        self.image_label.pack()
        # self.image_label.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        # Build and display label with advice
        self.advice_label = Label(self, text='Ensure produce item is completely visible.', font=self.info_font)
        self.advice_label.grid(row=4, column=0, columnspan=3, sticky=N+E+S+W)

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
            # Convert the new image, use .rotate(180) to flip if needed
            self.image = ImageTk.PhotoImage(Image.open(image_name).rotate(180))

            # Update and display again
            self.image_label.configure(image=self.image)
            self.image_label.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

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
        event = DisplayEvent(DisplayEvent.EVENT_BTN_ACCEPT)
        self.event_callback(event)

    def _take_picture_button_callback(self):
        if not self.picture_taken:
            self.set_buttons()
        event = DisplayEvent(DisplayEvent.EVENT_BTN_NEWIMAGE)
        self.event_callback(event)

    def _back_button_callback(self):
        event = DisplayEvent(DisplayEvent.EVENT_BTN_CANCEL)
        self.event_callback(event)


class ProduceScreen(ListScreen):
    """A Tkinter frame for the display of produce options.

    Args:
        parent (Widget): This frame's parent in the display hierarchy.
        callback (function): The function to pass DisplayEvent objects to.
    """
    def __init__(self, parent, callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, parent)

        self._callback = callback

        # Remove the bottom right warning label
        self.warning_label.grid_forget()

        # Fill up button section
        self._select_button = Button(self, text='Accept Weight', command=self._select_button_callback,
                                    font=self.button_font)
        self._select_button.grid(row=0, column=4, sticky=N+E+S+W)
        self._new_picture_button = Button(self, text='New Picture', command=self._new_picture_button_callback,
                                         font=self.button_font)
        self._new_picture_button.grid(row=1, column=4, sticky=N+E+S+W)
        self._cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback, font=self.button_font)
        self._cancel_button.grid(row=2, column=4, sticky=N+E+S+W)


        self._weight_total = 0.0
        self._info_string = StringVar()
        self._info_string.set('Please add produce item to cart\n{:>.2f}lbs'.format(self._weight_total))
        self._info_label = Label(self, textvariable=self._info_string, font=self.info_font)
        self._info_label.grid(row=4, column=1, sticky=W)

        # Build a canvas to display a grid of ProduceItem widgets
        self._produce_list = []
        self._rows = 0
        self._columns = 3
        self._selected_item = None

        self._item_canvas = Canvas(self)
        self._item_canvas.config(scrollregion=self._item_canvas.bbox(ALL))

        self._canvas_frame = Frame(self._item_canvas)
        self._canvas_frame.bind('<Configure>', self._on_frame_configure)

        self._item_canvas.create_window((0, 0), window=self._canvas_frame, anchor=N+W)
        self._item_canvas.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        # Create scroll buttons to control the canvas
        self._current_scroll_row = 0
        self._up_button = Button(self, text='Up', command=self._up_button_callback, font=self.button_font)
        self._up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)

        self._down_button = Button(self, text='Down', command=self._down_button_callback, font=self.button_font)
        self._down_button.grid(row=2, column=3, rowspan=2, sticky=N+E+S+W)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def update_list(self, produce_list):
        """Update the displayed selection of produce.

        Args:
            produce_list (list): List of Items that will be displayed.

        Returns:
            None.
        """
        self._produce_list = produce_list

        # Remove all items in the display
        for child in self._canvas_frame.winfo_children():
            child.grid_forget()

        # Repopulate the frame
        for i, item in enumerate(produce_list):
            filename = self._lookup_filename(item.name)
            ProduceItem(self._canvas_frame, item, filename, self._child_callback).grid(row=int(floor(i / self._columns)),
                                                                                      column=(i % self._columns))

        # Update the number of rows displayed
        self._rows = int(ceil(len(produce_list) / float(self._columns)))

        # Reset to the top
        self._current_scroll_row = 0
        self._item_canvas.yview_moveto(0.0)

        # Default to first item selected
        self._selected_item = None


    def set_weight(self, val):
        """Change the displayed weight."""
        self._weight_total = val

        self._info_string.set('Please add produce item to cart\n{:>.2f}lbs'.format(self._weight_total))

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    @staticmethod
    def _lookup_filename(name):
        """Determine the file name from an item's name."""
        return './resources/images/' + '_'.join(name.lower().split(' ')) + '.jpeg'

    def _up_button_callback(self):
        if self._current_scroll_row > 0:
            self._current_scroll_row -= 1
            self._item_canvas.yview_moveto(self._current_scroll_row / float(self._rows))

    def _down_button_callback(self):
        if self._current_scroll_row < (self._rows - 1):
            self._current_scroll_row += 1
            self._item_canvas.yview_moveto(self._current_scroll_row / float(self._rows))

    def _on_frame_configure(self, event):
        self._item_canvas.config(scrollregion=self._item_canvas.bbox(ALL))

    def _child_callback(self, clicked_item):
        """Callback function passed to all child widgets."""
        if self._selected_item != clicked_item:
            if self._selected_item:
                self._selected_item.deselect()

            clicked_item.select()

            self._selected_item = clicked_item

    def _select_button_callback(self):
        if self._selected_item:
            event = DisplayEvent(DisplayEvent.EVENT_BTN_ACCEPT, selection=self._selected_item.item)
            self._callback(event)

    def _new_picture_button_callback(self):
        # Needs to move back a screen
        event = DisplayEvent(DisplayEvent.EVENT_BTN_NEWIMAGE)
        self._callback(event)

    def _cancel_button_callback(self):
        event = DisplayEvent(DisplayEvent.EVENT_BTN_CANCEL)
        self._callback(event)


# TODO: figure out how to fit in price per pound, may need to resize images
class ProduceItem(Frame):
    """A Tkinter frame for displaying Item objects.

    Args:
        parent (Widget): Parent widget for this frame for determining placement hierarchy.
        item (Item): Item whose data will be displayed in this frame.
        image_name (String): Directory to find the image to display in this frame.
        callback(function): A function that will be called for events with one of the module level constants and an
                            optional keyword argument.

    Attributes:
        item (Item): Item that was passed to the constructor.
    """

    _WIDTH = 180
    _HEIGHT = 200

    def __init__(self, parent, item, image_name, callback):
        # Frame is an old-style object, cannot use super()
        Frame.__init__(self, parent)

        # Public member variables
        self.item = item

        # Private member variables
        self._image_name = image_name
        self._callback = callback
        self._hovering = False
        self._clicked = False
        self._clicked_widget = None

        # Configure the base frame with a 5px border and fix the size at WIDTH x HEIGHT regardless of contents
        self.config(width=self._WIDTH, height=self._HEIGHT)
        self.config(bd=5, relief=RAISED)
        self.pack_propagate(False)

        # Set up a main frame to ensure background color
        self._frame = Frame(self, bg='white')
        self._frame.pack(fill=BOTH, expand=True)

        # Set up a label to hold the produce image
        self._image = ImageTk.PhotoImage(Image.open(image_name))
        self._image_label = Label(self._frame, image=self._image, bg='white')
        self._image_label.pack(side=TOP)

        # Set up a label to hold the item name
        self._text = Label(self._frame, text=item.name, font=('Helvetica', 11), bg='white')
        self._text.pack(side=TOP, fill=X, expand=True)

        # Set up a label to hold the item price per pound
        self._price = Label(self._frame, text='${:.2f} per lb'.format(item.price_per_pound), anchor=E,
                            font=('Helvetica', 8), padx=10, bg='white')
        self._price.pack(side=TOP, fill=X, expand=True)

        # Bind click event handlers to self and all children
        bind_recursive(self, '<Button-1>', self._on_press)
        bind_recursive(self, '<ButtonRelease-1>', self._on_release)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def select(self):
        """Change the border style to the selected style."""
        self.config(relief=SUNKEN)

    def deselect(self):
        """Change the border style to the unselected style."""
        self.config(relief=RAISED)

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _on_press(self, event):
        """Callback function for mouse button presses."""
        self._clicked = True

    def _on_release(self, event):
        """Callback function for mouse button releases."""
        if self._clicked and self._is_inside(event.x_root, event.y_root):
            self._callback(self)

    def _is_inside(self, x, y):
        """Check if the coordinates given are inside of this widget.

        Structured such that the event parameters from mouse clicks can be passed to this function for a simple boolean
        return value.

        Args:
            x: X-coordinate value.
            y: Y-coordinate value.

        Returns:
            bool: True if the coordinates are within the widget, else False.
        """
        w_x = self.winfo_rootx()
        w_y = self.winfo_rooty()
        if w_x <= x <= (w_x + self.winfo_reqwidth()) and w_y <= y <= (w_y + self.winfo_reqheight()):
            return True
        else:
            return False


class HomeScreen(ListScreen):
    """A Tkinter frame for the main screen display of the shopping list.

    Args:
        parent (Widget): This frame's parent in the display hierarchy.
        callback (function): The function to pass DisplayEvent objects to.

    Attributes:
        price_total (float): The total price of all items currently in the list.
    """
    _DISPLAY_ROWS = 8
    _ACT_ADD = 'homescreen_act_add'
    _ACT_REMOVE = 'homescreen_act_remove'

    def __init__(self, parent, callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, parent)

        # Public member variables
        self.price_total = property(self._get_price_total, self._set_price_total)

        # Private member variables
        self._callback = callback
        self._price_total = 0.0
        self._selected_item = None
        self._rows = 0
        self._displayed_row = 0
        self._last_action = None
        self._last_added = None
        self._last_removed = None

        # Remove parent class's label
        # self.warning_label.grid_forget()

        # Fill up button section
        # TODO: put Help back in when its implemented
        self._produce_button = Button(self, text='Scan Produce', command=self._produce_button_callback,
                                      font=self.button_font)
        self._produce_button.grid(row=0, column=4, sticky=N+E+S+W)
        self._remove_button = Button(self, text='Remove Item', command=self._remove_button_callback,
                                     font=self.button_font)
        self._remove_button.grid(row=1, column=4, sticky=N+E+S+W)
        self._help_button = Button(self, text='Quit', command=self._help_button_callback, font=self.button_font)
        self._help_button.grid(row=2, column=4, sticky=N+E+S+W)
        self._cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback, font=self.button_font)
        self._cancel_button.grid(row=3, column=4, sticky=N+E+S+W)

        # Build a label to display the price total
        self._price_string = StringVar()
        self._price_string.set('Total: ${: .2f}'.format(self._price_total))
        self._price_label = Label(self, textvariable=self._price_string, padx=60, pady=20, font=self.price_font)
        self._price_label.grid(row=4, column=0, sticky=W)

        # Canvas to display our ListItem frames
        self._item_canvas = Canvas(self)
        self._item_canvas.config(scrollregion=self._item_canvas.bbox(ALL))

        self._canvas_frame = Frame(self._item_canvas)
        self._canvas_frame.bind('<Configure>', self._on_frame_configure)

        self._item_canvas.create_window((0, 0), window=self._canvas_frame, anchor=N+W)
        self._item_canvas.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        # Create scroll buttons to control the canvas
        self._current_scroll_row = 0
        self._up_button = Button(self, text='Up', command=self._up_button_callback, font=self.button_font)
        self._up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)

        self._down_button = Button(self, text='Down', command=self._down_button_callback, font=self.button_font)
        self._down_button.grid(row=2, column=3, rowspan=2, sticky=N+E+S+W)

        # DEBUG
        # self._empty = True
        # self._debug_label = Label(self._canvas_frame, text='Welcome', font=(20))
        # self._debug_label.pack(side=TOP)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def add_item(self, item):
        """Add a new item to the displayed list.

        Args:
            item (Item): Item object to add to the list.

        Returns:
            None.
        """
        # DEBUG
        # if self._empty:
        #     self._debug_label.pack_forget()

        # Add item to the display
        new_frame = ListItem(self._canvas_frame, item, self._child_callback)
        new_frame.pack(side=TOP)

        # Update the price total
        self._set_price_total(self._price_total + item.price)

        # Increment row count
        self._rows += 1

        # Update last action
        self._last_action = self._ACT_ADD
        self._last_added = new_frame

    def remove_selected(self):
        """Remove the currently selected item from the display.

        Args:
            None.

        Returns:
            bool: True if an item was selected and removed, False if no item was selected.
        """
        if self._selected_item:
            removed_item = self._selected_item.item
            self._selected_item.pack_forget()
            self._selected_item.deselect()

            # Update the price total
            self._set_price_total(self._price_total - removed_item.price)

            # Decrement row count
            self._rows -= 1

            # Update last action
            self._last_action = self._ACT_REMOVE
            self._last_removed = self._selected_item

            # Update scroll position
            # if self._displayed_row > self._rows - self._DISPLAY_ROWS:
            #     self._displayed_row -= 1

            if self._rows > 0:
                self._item_canvas.yview_moveto(self._displayed_row / float(self._rows))

            # Clear selection
            self._selected_item = None
            return True
        else:
            return False

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _get_price_total(self):
        """Getter for the price_total member."""
        return self._price_total

    def _set_price_total(self, val):
        """Setter for the price_total member."""
        self._price_total = val

        # Update StringVar
        self._price_string.set('Total: ${: .2f}'.format(val))

    def _undo_add(self):
        """Remove the last item added to the display."""
        self._last_added.pack_forget()
        self._last_action = None

        # Update the price total
        self._set_price_total(self._price_total - self._last_added.item.price)

        # Decrement row count
        self._rows -= 1

        # Update scroll position
        # if self._displayed_row > self._rows - self._DISPLAY_ROWS:
        #     self._displayed_row -= 1

        if self._rows > 0:
            self._item_canvas.yview_moveto(self._displayed_row / float(self._rows))

    def _undo_remove(self):
        """Add the last item removed back to the display."""
        self._last_removed.pack(side=TOP)
        self._last_action = None

        # Update the price total
        self._set_price_total(self._price_total + self._last_removed.item.price)

        # Increment row count
        self._rows += 1

    def _clear_display(self):
        """Remove all widgets from the canvas display."""
        for child in self._canvas_frame.winfo_children():
            child.place_forget()

    def _child_callback(self, clicked_item):
        """Callback function passed to all child widgets."""
        if clicked_item != self._selected_item:
            if self._selected_item:
                self._selected_item.deselect()

            clicked_item.select()

            self._selected_item = clicked_item
        else:
            self._selected_item.deselect()
            self._selected_item = None

    def _up_button_callback(self):
        if self._displayed_row > 0:
            self._displayed_row -= 1
            self._item_canvas.yview_moveto(self._displayed_row / float(self._rows))

    def _down_button_callback(self):
        if self._displayed_row < self._rows - self._DISPLAY_ROWS:
            self._displayed_row += 1
            self._item_canvas.yview_moveto(self._displayed_row / float(self._rows))

    def _on_frame_configure(self, event):
        self._item_canvas.config(scrollregion=self._item_canvas.bbox(ALL))

    def _produce_button_callback(self):
        event = DisplayEvent(DisplayEvent.EVENT_BTN_PRODUCE)
        self._callback(event)

    def _remove_button_callback(self):
        if self._selected_item:
            event = DisplayEvent(DisplayEvent.EVENT_BTN_REMOVEITEM, selection=self._selected_item.item,
                                 action=self.remove_selected)
            self._callback(event)

    def _help_button_callback(self):
        event = DisplayEvent(DisplayEvent.EVENT_BTN_HELP)
        self._callback(event)

    def _cancel_button_callback(self):
        if self._last_action == self._ACT_ADD:
            handler = self._undo_add
            event = DisplayEvent(DisplayEvent.EVENT_BTN_CANCEL, action=handler)
            self._callback(event)
        elif self._last_action == self._ACT_REMOVE:
            handler = self._undo_remove
            event = DisplayEvent(DisplayEvent.EVENT_BTN_CANCEL, action=handler)
            self._callback(event)


class ListItem(Frame):
    """A Tkinter frame for displaying Item objects.

    Args:
        parent (Widget): Parent widget for this frame for determining placement hierarchy.
        item (Item): Item whose data will be displayed in this frame.
        callback(function): A function that will be called for events with one of the module level constants and an
                            optional keyword argument.

    Attributes:
        base_font (String, int, String): Tuple used to define the font style and size of the item's name and price
                                         labels.
        info_font (String, int, String): Tuple used to define the font style and size of a produce item's extra unit
                                         price information.
        item (Item): Item that was passed to the constructor.
    """
    _WIDTH = 540
    _HEIGHT = 50

    base_font = ('Helvetica', 13, 'bold')
    info_font = ('Helvetica', 8)

    def __init__(self, parent, item, callback):
        # Frame is an old-style object, cannot use super()
        Frame.__init__(self, parent)

        # Public member variables
        self.item = item

        # Private member variables
        self._callback = callback
        self._clicked = False

        # Configure the base frame with a 5px border and fix the size at WIDTH x HEIGHT regardless of contents
        self.config(bd=5, relief=RAISED)
        self.config(width=self._WIDTH, height=self._HEIGHT)
        self.pack_propagate(False)

        # Label containing the item name
        self._name_string = StringVar()
        self._name_string.set(item.name)
        self._name_label = Label(self, textvariable=self._name_string, font=self.base_font, padx=10)
        self._name_label.pack(side=LEFT)

        # Pack the price into a frame that will also contain more info for produce items
        self._price_frame = Frame(self)
        self._price_frame.pack(side=RIGHT)

        # Label containing the item price
        self._price_string = StringVar()
        self._price_string.set('${: .2f}'.format(item.price))
        self._price_label = Label(self._price_frame, textvariable=self._price_string, font=self.base_font, anchor=E)
        self._price_label.pack(side=TOP, fill=X)

        # Produce needs another label to display price per unit weight and weight
        if item.is_produce:
            self._info_string = StringVar()
            self._info_string.set('{: .2f} lb @ ${: .2f} per lb'.format(item.grams_to_pounds(item.weight),
                                                                        item.price_per_pound))
            self._info_label = Label(self._price_frame, textvariable=self._info_string, anchor=E, font=self.info_font)
            self._info_label.pack(side=TOP)

        # Bind click event handlers to self and all children recursively
        bind_recursive(self, '<Button-1>', self._on_press)
        bind_recursive(self, '<ButtonRelease-1>', self._on_release)

    ####################################################################################################################
    # PUBLIC METHODS
    ####################################################################################################################

    def select(self):
        """Change the border style to the selected style."""
        self.config(relief=SUNKEN)

    def deselect(self):
        """Change the border style to the unselected style."""
        self.config(relief=RAISED)

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _on_press(self, event):
        """Callback function for mouse button presses."""
        self._clicked = True

    def _on_release(self, event):
        """Callback function for mouse button releases."""
        if self._clicked and self._is_inside(event.x_root, event.y_root):
            self._callback(self)

    def _is_inside(self, x, y):
        """Check if the coordinates given are inside of this widget.

        Structured such that the event parameters from mouse clicks can be passed to this function for a simple boolean
        return value.

        Args:
            x: X-coordinate value.
            y: Y-coordinate value.

        Returns:
            bool: True if the coordinates are within the widget, else False.
        """
        w_x = self.winfo_rootx()
        w_y = self.winfo_rooty()
        if w_x <= x <= (w_x + self.winfo_reqwidth()) and w_y <= y <= (w_y + self.winfo_reqheight()):
            return True
        else:
            return False


########################################################################################################################
# DEPRECATED CLASSES
########################################################################################################################

class OldHomeScreen(ListScreen):
    def __init__(self, root, callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        # initialize variables
        self._price_total = 0.0
        self.item_list = []
        self._callback = callback
        self._price_string = StringVar()
        self._price_string.set('Total: ${: .2f}'.format(self.get_price_total()))

        # build our buttons and place them into the grid
        self.produce_button = Button(self, text='Scan Produce', command=self._produce_button_callback, font=self.button_font)
        self.produce_button.grid(row=0, column=4, sticky=N+E+S+W)

        self.remove_button = Button(self, text='Remove Item', command=self._remove_button_callback, font=self.button_font)
        self.remove_button.grid(row=1, column=4, sticky=N+E+S+W)

        # TODO: put Help back in when its implemented
        self.help_button = Button(self, text='Help', command=self._help_button_callback, font=self.button_font)
        # self.help_button.grid(row=2, column=4, sticky=N+E+S+W)

        self.cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback, font=self.button_font)
        self.cancel_button.grid(row=3, column=4, sticky=N+E+S+W)

        # build our price label it is associated with a variable to dynamically update
        self.price_label = Label(self, textvariable=self._price_string, font=self.price_font)
        self.price_label.grid(row=4, column=0, sticky=W)

        # build our item list as a Listbox and associated controls
        self.item_listbox = Listbox(self, font=self.monospace_font)
        self.item_listbox.grid(row=0, column=0, columnspan=3, rowspan=4, sticky=N+E+S+W)

        self.up_button = Button(self, text='Up', command=lambda: self.item_listbox.yview_scroll(-1, UNITS), font=self.button_font)
        self.up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)
        self.down_button = Button(self, text='Down', command=lambda: self.item_listbox.yview_scroll(1, UNITS), font=self.button_font)
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

    def add_item(self, item):
        """Add a new item to the displayed list.

        :param item: Item object to add to the list.
        :return: None.
        """
        # pull data from the item
        name = item.name
        price = item.price

        # append element
        self.item_listbox.insert(END, '{:_<34}${:>.2f}'.format(name, price))
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

    ####################################################################################################################
    # PRIVATE METHODS
    ####################################################################################################################

    def _produce_button_callback(self):
        """Pass an event through the callback function.

        :return: None.
        """
        event = DisplayEvent(DisplayEvent.EVENT_BTN_PRODUCE)
        self._callback(event)

    def _remove_button_callback(self):
        if self.item_listbox.size() != 0:
            index = self.item_listbox.index(ACTIVE)
            self.event_callback(EVENT_BTN_REMOVEITEM, index=index)

    def _help_button_callback(self):
        self.event_callback(EVENT_BTN_HELP)

    def _cancel_button_callback(self):
        self.event_callback(EVENT_BTN_CANCEL)


class OldProduceScreen(ListScreen):
    def __init__(self, root, event_callback):
        # Frame is an old-style object, cannot use super()
        ListScreen.__init__(self, root)

        self.event_callback = event_callback
        self.produce_list = None
        self.weight_total = 0.0
        self.weight_string = StringVar()
        self.weight_string.set('{:>.2f}lbs'.format(self.weight_total))

        self._warning_string.set('Please add produce item to cart')

        self.select_button = Button(self, text='Accept Weight', command=self._select_button_callback,
                                    font=self.button_font)
        self.select_button.grid(row=0, column=4, sticky=N+E+S+W)

        self.new_picture_button = Button(self, text='New Picture', command=self._new_picture_button_callback,
                                         font=self.button_font)
        self.new_picture_button.grid(row=1, column=4, sticky=N+E+S+W)

        self.cancel_button = Button(self, text='Cancel', command=self._cancel_button_callback, font=self.button_font)
        self.cancel_button.grid(row=2, column=4, sticky=N+E+S+W)

        self.produce_listbox = Listbox(self, font=self.monospace_font)
        self.produce_listbox.grid(row=0, column=0, rowspan=4, columnspan=3, sticky=N+E+S+W)

        self.weight_label = Label(self, textvariable=self.weight_string, font=self.price_font)
        self.weight_label.grid(row=4, column=1, sticky=W)

        self.up_button = Button(self, text='Up', command=lambda: self.produce_listbox.yview_scroll(-1, UNITS),
                                font=self.button_font)
        self.up_button.grid(row=0, column=3, rowspan=2, sticky=N+E+S+W)

        self.down_button = Button(self, text='Down', command=lambda: self.produce_listbox.yview_scroll(1, UNITS),
                                  font=self.button_font)
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
    def event_handler(event):
        if myapp.current_screen == myapp.homescreen:
            if event.type == event.EVENT_BTN_PRODUCE:
                myapp.change_screen(myapp.picturescreen)

        elif myapp.current_screen == myapp.picturescreen:
            if event.type == event.EVENT_BTN_ACCEPT:
                myapp.update_produce_list(produce)
                myapp.change_screen(myapp.producescreen)
            elif event.type == event.EVENT_BTN_NEWIMAGE:
                print 'Picture taken'
            elif event.type == event.EVENT_BTN_CANCEL:
                myapp.change_screen(myapp.homescreen)

        elif myapp.current_screen == myapp.producescreen:
            if event.type == event.EVENT_BTN_ACCEPT:
                new_item = event.selection
                new_item.weight = 0.50
                myapp.add_item(new_item)
                myapp.change_screen(myapp.homescreen)
            elif event.type == event.EVENT_BTN_NEWIMAGE:
                myapp.change_screen(myapp.picturescreen)
            elif event.type == event.EVENT_BTN_CANCEL:
                myapp.change_screen(myapp.homescreen)

        if event.selection:
            print event.selection
        event.handle_event()

    items = [Item(name='Granola'),
             Item(name='Kale', is_produce=True),
             Item(name='Mac and Cheese'),
             Item(name='Gum'),
             Item(name='Tomato', is_produce=True),
             Item(name='Doritos'),
             Item(name='Tofu'),
             Item(name='Cheese'),
             Item(name='Salami'),
             Item(name='Bread'),
             Item(name='Chili')]

    produce = [Item(name='Kale', is_produce=True),
               Item(name='Iceberg Lettuce', is_produce=True),
               Item(name='Green Apple', is_produce=True)]

    for each in items:
        if each.is_produce:
            each.weight = 1.05
            each.price_per_pound = 0.60
        else:
            each.price = 5.20

    for each in produce:
        each.price_per_pound = 0.60

    root = Tk()

    # Demo the popup warnings
    # myapp = DisplayManager(root, event_handler)
    # myapp.change_screen(myapp.producescreen)
    # myapp.set_popup_text('Announcement text!\n\nNext line.\nAnd another line.\nAnd some more.')
    # myapp.set_popup_text('Announcement text!')
    # myapp._popupframe.show_button()
    # myapp.show_popup()


    # Demo the new produce screen
    # Frame(root, width=800, height=480, bg='blue').grid(row=0, column=0)
    # myapp = ProduceScreen(root, event_handler)
    # myapp.grid(row=0, column=0)
    # myapp.update_list(produce)


    # Demo the new home screen
    root.overrideredirect(1)
    root.geometry('800x480')
    root.focus_set()

    myapp = HomeScreen(root, event_handler)
    myapp.pack()
    for each in items:
        myapp.add_item(each)


    # Test PictureScreen
    # myapp = PictureScreen(root, event_handler)
    # myapp.pack()
    # myapp.update_image('./images/img_capture.jpg')


    # Test the whole deal
    # myapp = DisplayManager(root, event_handler)
    # for each in items:
    #     myapp.add_item(each)

    # start the main loop
    root.mainloop()
    print 'exiting...'

if __name__ == '__main__':
    main()