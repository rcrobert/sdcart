class ItemError(Exception):
    def __init__(self, args):
        self.args = args


class Item(object):
    """Class that holds shopping cart item data. Used for packing and passing item data.

    Args:
        barcode (optional String): String value for the item's barcode. Default is None.
        name (optional String): String value for the item's name. Default is None.
        weight (optional float): Float value for the item's weight on creation. Default is None.
        is_produce (optional bool): Boolean value indicating if this is a produce item. Default is False.

    Attributes:
        name (String): The item's name.
        barcode (String): The item's barcode string.
        weight (float): The item's total weight.
        is_produce (bool): Whether the item is a produce item or not.
        price (float): The price of the item.
        price_per_pound (float): The price per pound of the item. Used only for produce items.
        d_weight (float): The amount of deviation from the item's listed weight.
    """
    def __init__(self, barcode=None, name=None, weight=None, is_produce=False):
        self.barcode = barcode
        self.weight = weight
        self.name = name
        self.is_produce = is_produce

        self.price_per_pound = None
        self.d_weight = None

        self._price = None

    def __repr__(self):
        s = ''

        s += 'Name: ' + str(self.name) + '\n'
        s += 'Price: ' + str(self.price) + '\n'
        s += 'Weight: ' + str(self.weight) + '\n'
        s += 'Barcode: ' + str(self.barcode) + '\n'
        s += 'Deviation: ' + str(self.d_weight) + '\n'

        return s

    @property
    def price(self):
        if self.is_produce:
            # Do not attempt to round if either member is None type
            if self.price_per_pound and self.weight:
                return round(self.price_per_pound * self.weight, 2)
        else:
            if self._price:
                return round(self._price, 2)

        # Return None type if required members are still undefined
        return None

    @price.setter
    def price(self, val):
        if self.is_produce:
            raise ItemError('cannot set produce price')
        else:
            self._price = val

    @property
    def weight_lbs(self):
        return self.grams_to_pounds(self.weight)

    @weight_lbs.setter
    def weight_lbs(self, val):
        raise ItemError('cannot set weight in pounds')

    @staticmethod
    def grams_to_pounds(val):
        """Convert value from grams to pounds"""
        return round(val * 0.00220462, 2)

def main():
    N = Item(barcode='602652170652')
    N.price = 1.523
    print N

    M = Item(name='Kale', is_produce=True)
    M.price_per_pound = 1.062
    M.weight = 1.00
    print M

if __name__ == '__main__':
    main()