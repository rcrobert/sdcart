from adc_driver import ADCController
from item import Item

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
            if self._check_in_range(self.weight, self.expected_weight, self.expected_weight * self.deviation):
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