from adc_driver import ADCController
from PWM import LEDController

# Members
# busy - binary flag that is set while in produce_mode, or while waiting for add_item or remove_item
#
# Methods
# add_item(Item item) this will tell it that an item of a specific weight has been scanned into the cart
# start_produce_mode() maybe just a binary flag
# end_produce_mode()
# remove_item(Item item) this will tell it that an item of a specific weight hsa been requested to be removed

class WeightManagerError(Exception):
    def __init__(self, args):
        self.args = args

class IncrementalWeightManager(object):
    WAITING_FOR_ADD = 'waiting for add'
    WAITING_FOR_REMOVE = 'waiting for remove'
    OUT_OF_RANGE_HIGH = 'out of range high'
    OUT_OF_RANGE_LOW = 'out of range low'
    WRONG_ITEM = 'wrong item'

    def __init__(self):
        # Instantiate ADC Controller class
        self.adc_controller= ADCController()

        # Initialize LED Controller
        LEDController.init()

        # Error tracking
        self.error = False
        self.error_type = None

        # State flags
        self.busy = False
        self._produce_mode = False
        self.pending_addition = False
        self.pending_removal = False

        # State memory
        self._pending_item = None
        self.produce_weight = 0.0
        self.weight_reading = 0.0
        self._increment_counter = 0
        self._seconds_count = 0
        self._lights_on = False

        # Metrics for database usage
        self.total_weight = 0.0
        self.expected_weight = 0.0

        # Configurable
        self.max_deviation = 20.0 # maximum deviation in grams
        self.leds_green_time = 1

    def update(self):
        self.weight_reading = self._get_weight()

        # Handle timer for green lights
        if self._lights_on:
            self._increment_counter += 1

            if self._increment_counter == 5:
                self._seconds_count += 1
                self._increment_counter = 0

            if self._seconds_count == self.leds_green_time:
                # Turn off the green lights
                self._lights_on = False
                LEDController.toggle(LEDController.GREEN, 0)

                # Reset counter
                self._seconds_count = 0
        else:
            self._increment_counter = 0
            self._seconds_count = 0

        # Check if pending addition is resolved
        if self.pending_addition:
            if self._check_in_range(self.weight_reading, self._pending_item.weight, self._pending_item.d_weight):
                # Item has been added, clear flags
                self.busy = False
                self.pending_addition = False

                # No more item pending
                self._pending_item = None

                # Update total weight
                self.total_weight += self.weight_reading

                # Zero the total weight
                self.adc_controller.zero()

                # TODO: LEDs go green for 2 sec
                self._lights_on = True
                LEDController.toggle(LEDController.RED, 0)
                LEDController.toggle(LEDController.GREEN, 1)
            else:
                # Either waiting still or incorrect item
                self.error = True

                if abs(self.weight_reading) > self.max_deviation:
                    # Incorrect item
                    self.error_type = self.WRONG_ITEM

                    # TODO: LEDs go red
                    LEDController.toggle(LEDController.GREEN, 0)
                    LEDController.toggle(LEDController.RED, 1)
                else:
                    # Nothing has been added, still waiting
                    self.error_type = self.WAITING_FOR_ADD

                    # TODO: LEDs go yellow

        # Check if pending removal is resolved
        elif self.pending_removal:
            if self._check_in_range(self.weight_reading, -self._pending_item.weight, self._pending_item.d_weight):
                # Item has been removed, clear flags
                self.busy = False
                self.pending_removal = False

                # No more item pending
                self._pending_item = None

                # Update total weight
                self.total_weight -= self.weight_reading

                # Zero the total weight
                self.adc_controller.zero()

                # TODO: LEDs go green for 2 sec
                self._lights_on = True
                LEDController.toggle(LEDController.RED, 0)
                LEDController.toggle(LEDController.GREEN, 1)
            else:
                # Either waiting still or incorrect item
                self.error = True

                if abs(self.weight_reading) > self.max_deviation:
                    # Incorrect item
                    self.error_type = self.WRONG_ITEM

                    # TODO: LEDs go red
                    LEDController.toggle(LEDController.GREEN, 0)
                    LEDController.toggle(LEDController.RED, 1)
                else:
                    # Nothing has been removed, still waiting
                    self.error_type = self.WAITING_FOR_REMOVE

                    # TODO: LEDs go yellow

        # Handle produce mode differently
        elif self._produce_mode:
            # Update produce weight
            self.produce_weight = self.weight_reading

            # No errors can exist in this mode
            self.error = False
            self.error_type = None

            # TODO: LEDs go off
            LEDController.toggle(LEDController.RED, 0)
            LEDController.toggle(LEDController.GREEN, 0)

        # Handle standard operation security
        else:
            if abs(self.weight_reading) > self.max_deviation:
                # Weight is incorrect, set error flags
                self.error = True

                if self.weight_reading > 0.0:
                    self.error_type = self.OUT_OF_RANGE_HIGH
                else:
                    self.error_type = self.OUT_OF_RANGE_LOW

                # TODO: LEDs go red
                LEDController.toggle(LEDController.GREEN, 0)
                LEDController.toggle(LEDController.RED, 1)
            else:
                # Weight is correct, clear error flags
                self.error = False
                self.error_type = None

                # TODO: LEDs go off
                if not self._lights_on:
                    LEDController.toggle(LEDController.RED, 0)
                    LEDController.toggle(LEDController.GREEN, 0)

    def add_item(self, item):
        # Cannot be called while busy with another operation
        if self.busy:
            raise WeightManagerError('cannot add item while busy')

        # Non-produce
        if not item.is_produce:
            # Set flags
            self.busy = True
            self.pending_addition = True

            # Save item to be added
            self._pending_item = item

            # Update expected weight
            self.expected_weight += item.weight

        # For produce items, just re-zero the weight there is no checking process
        else:
            self.total_weight += item.weight
            self.expected_weight += item.weight
            self.adc_controller.zero()

    def remove_item(self, item):
        # Cannot be called while busy with another operation
        if self.busy:
            raise WeightManagerError('cannot remove item while busy')

        # Set flags
        self.busy = True
        self.pending_removal = True

        # Save item to be removed
        self._pending_item = item

        # Update the expected weight
        self.expected_weight -= item.weight

    def cancel_operation(self):
        # Can only be called if we are busy
        if not self.busy:
            raise WeightManagerError('no pending operation to cancel')

        if self.pending_addition:
            # Clear flags
            self.busy = False
            self.pending_addition = False

            # Update expected weight
            self.expected_weight -= self._pending_item.weight

            # Clear pending item
            self._pending_item = None
        elif self.pending_removal:
            # Clear flags
            self.busy = False
            self.pending_removal = False

            # Update expected weight
            self.expected_weight += self._pending_item.weight

            # Clear pending item
            self._pending_item = None

    def start_produce_mode(self):
        # Set flags
        self.busy = True
        self._produce_mode = True

    def end_produce_mode(self):
        # Clear flags
        self.busy = False
        self._produce_mode = False

    def tare(self):
        self.adc_controller.zero()

    @staticmethod
    def grams_to_pounds(val):
        """Convert value from grams to pounds"""
        return round(val * 0.00220462, 2)

    def _get_weight(self):
        """Get the current weight reading from the ADCs."""
        return self.adc_controller.weight

    @staticmethod
    def _check_in_range(actual, expected, deviation):
        """Check if a value falls within a range with deviation.

        Args:
            actual (float): The value to check.
            expected (float): The expected value to check against.
            deviation (float): The allowed deviation from the expected value.

        Returns:
            boolean: True if actual falls within the range given by expected and deviation.
        """
        if not deviation:
            deviation = 0.0

        if (expected - deviation) <= actual <= (expected + deviation):
            return True
        else:
            return False


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

        self.weight = self.get_weight()
        self.expected_weight = self.get_weight()

        # Allowed deviation in running total
        self.deviation = 0.005
        self.total_deviation = 8.0

    def update(self):
        # Check the new total weight
        self.weight = self.get_weight()

        # Negative weights, very small weights should be zero
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
            # if self._check_in_range(self.weight, self.expected_weight, self.expected_weight * self.deviation):
            if self._check_in_range(self.weight, self.expected_weight, self.total_deviation):
                # Valid weight, reset errors
                self.error = False
            else:
                # Invalid weight
                self.error = True
                self.error_type = self.OUT_OF_RANGE

    def add_item(self, item):
        # Cannot be called if we are already busy with another operation

        if item.is_produce:
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
    def grams_to_pounds(val):
        """Convert value from grams to pounds"""
        return round(val * 0.00220462, 2)

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