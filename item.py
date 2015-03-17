import time
import pymysql


class ItemError(Exception):
    def __init__(self, args):
        self.args = args


class Item(object):
    """Class holds shopping cart item data. Used for packing and passing item data. This class is also responsible for
    requesting complete item data from the server database."""

    CONN = pymysql.connect(
        host="db-01.soe.ucsc.edu",
        user="sdp2015_echelon",
        passwd="Jlbihf2015!",
        database="sdp2015_echelon"
    )

    CURSOR = CONN.cursor()

    def __init__(self, barcode=None, cascades=None, name=None, price=None, weight=None):
        self.barcode = barcode
        self.cascades = cascades
        self.weight = weight
        self.name = name
        self.price = price

        self._is_populated = False
        self.d_weight = 100.0

    def __repr__(self):
        s = ''

        s += 'Name: ' + str(self.name) + '\n'
        s += 'Price: ' + str(self.price) + '\n'
        s += 'Weight: ' + str(self.weight) + '\n'
        s += 'Barcode: ' + str(self.barcode) + '\n'
        s += 'Cascades: ' + str(self.cascades) + '\n'

        return s

    def request_info(self, callback=None):
        """Populates the item's information with database information.

        :param callback: User-specified function to be called when a request finishes.
        :return:
        """

        self.price = 10.20
        self.weight = 1.00

        # populate item data based on how it was scanned in
        if self.barcode:
            # Add to database, update cart list on the database
            self.CURSOR.execute("INSERT INTO shopping_cart (item_name, item_weight, item_price)"
                                "SELECT name,weight,price FROM item_db WHERE barcode_id='{}'".format(self.barcode))
            self.CONN.commit()

            # Fetch the item data
            self.CURSOR.execute("SELECT name,weight,price,deviation FROM item_db WHERE barcode_id='{}'".format(self.barcode))
            rows = self.CURSOR.fetchall()

            if len(rows) > 1:
                # Error more than one result from barcode
                raise ItemError('Multiple results for barcode')

            # Populate item
            self.name = rows[0][0]
            self.weight = float(rows[0][1])
            self.price = float(rows[0][2])
            self.d_weight = float(rows[0][3])
        elif self.name:
            # Get total price
            self.CURSOR.execute("SELECT price_per_pound FROM produce_db WHERE name='{}'".format(self.name))
            rows = self.CURSOR.fetchall()

            if len(rows) > 1:
                # Error if more than one result for produce name
                raise ItemError('Multiple results for produce name')

            # TODO: convert to pounds from grams
            self.price = float(rows[0][0]) * self.grams_to_pounds(self.weight)

            # Add to database, update cart list on the database
            self.CURSOR.execute("INSERT INTO shopping_cart (item_name, item_weight, item_price)"
                                "VALUES (%s,%s,%s)", (self.name, self.weight, self.price))
        else:
            self.name = 'OtherItem'

    @staticmethod
    def grams_to_pounds(val):
        """Convert value from grams to pounds"""
        return val * 0.00220462

def main():
    N = Item(barcode='602652170652')
    N.request_info()

if __name__ == '__main__':
    main()