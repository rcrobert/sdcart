import pymysql
from item import Item


class DatabaseError(Exception):
    def __init__(self, args):
        self.args = args

class NoItem(Exception):
    def __init__(self, args):
        self.args = args

class Database(object):
    CONN = pymysql.connect(
        host="db-01.soe.ucsc.edu",
        user="sdp2015_echelon",
        passwd="Jlbihf2015!",
        database="sdp2015_echelon"
    )

    CURSOR = CONN.cursor()

    def __init__(self):
        pass

    @classmethod
    def add_to_cart(cls, item):
        assert isinstance(item, Item)
        cls.CURSOR.execute("INSERT INTO shopping_cart (item_name, item_weight, item_price)"
                           "VALUES (%s,%s,%s)", (item.name, item.weight, item.price))
        cls.CONN.commit()
        cls.CURSOR.execute("INSERT INTO history (item_name) VALUES (%s)", item.name)
        cls.CONN.commit()

    @classmethod
    def remove_from_cart(cls, item):
        assert isinstance(item, Item)
        cls.CURSOR.execute("DELETE FROM shopping_cart WHERE item_name='{}' ORDER BY scan_time LIMIT 1".format(item.name))
        cls.CONN.commit()

    @classmethod
    def empty_cart(cls):
        cls.CURSOR.execute("DELETE FROM shopping_cart WHERE 1")
        cls.CONN.commit()

    @classmethod
    def request_info(cls, item):
        """Retrieve info for an Item object.

        :param item: Item object to populate.
        :return: None
        """

        # Ensure type
        assert isinstance(item, Item)

        if not item.is_produce:
            barcode = item.barcode
            cls.CURSOR.execute("SELECT name,weight,price,deviation FROM item_db WHERE barcode_id='{}'".format(barcode))
            rows = cls.CURSOR.fetchall()

            if len(rows) > 1:
                # Error non-unique barcode in database
                raise DatabaseError('non-unique barcode in database')
            elif len(rows) < 1:
                # Error non-existent barcode in database
                print 'No results'
                raise NoItem('no results for barcode in database')

            # Populate item
            item.name = rows[0][0]
            item.weight = float(rows[0][1])
            item.price = float(rows[0][2])
            item.d_weight = float(rows[0][3])
        else:
            # Do not populate produce items this way
            raise DatabaseError('use get_produce_list method for produce items')

    @classmethod
    def get_produce_list(cls, opencv_results):
        item_list = []

        for each in opencv_results:
            region = each[0]
            classifier = each[1]

            if classifier != 'None':
                cls.CURSOR.execute("SELECT result,price_per_pound FROM produce_db_2 WHERE color='{}' AND "
                                   "shape='{}' ORDER BY result".format(region, classifier))
                rows = cls.CURSOR.fetchall()
            else:
                cls.CURSOR.execute("SELECT result,price_per_pound FROM produce_db_2 WHERE color='{}' ORDER BY "
                                   "result".format(region, classifier))
                rows = cls.CURSOR.fetchall()

            for row in rows:
                tmp = Item(name=row[0], is_produce=True)
                tmp.price_per_pound = round(row[1], 2)

                item_list.append(tmp)

        return item_list

    @classmethod
    def update_weight(cls, weight):
        """Updates the database with a new shopping cart weight."""
        cls.CURSOR.execute("UPDATE shopping_cart SET current_load='{}' ORDER BY scan_time LIMIT 1".format(int(weight)))
        cls.CONN.commit()

    @classmethod
    def add_barcode_item(cls, barcode_id, name, weight, price, deviation):
        """Adds an item to the barcode item database."""
        cls.CURSOR.execute("INSERT INTO item_db (barcode_id, name, weight, price, deviation)"
                           "VALUES (%s,%s,%s,%s,%s)", (barcode_id, name, weight, price, deviation))
        cls.CONN.commit()

    @classmethod
    def add_produce_item(cls, color, shape, name, price):
        """Adds an item to the produce item database."""
        cls.CURSOR.execute("INSERT INTO produce_db_2 (color, shape, result, price_per_pound)"
                           "VALUES (%s,%s,%s,%s)", (color, shape, name, price))
        cls.CONN.commit()

    @classmethod
    def check_in_inventory(cls, name, is_produce):
        """Check if an item of given name exists in the SQL database.

        Args:
            name (String): The name of the item to search for.
            is_produce (boolean): True if the item searched for is produce, False for barcode.

        Returns:
            boolean: True if the item is a duplicate in the database.

        """
        # Select from either produce or item database
        if is_produce:
            cls.CURSOR.execute("SELECT * FROM produce_db_2 WHERE result=%s", (name))
        else:
            cls.CURSOR.execute("SELECT * FROM item_db WHERE name=%s", (name))

        # Fetch the results
        rows = cls.CURSOR.fetchall()

        # If any results exist for this name, item is a duplicate return TRUE
        if len(rows) > 0:
            return True
        else:
            return False

def main():
    tmp = Item(barcode='0910293')

    # Note that you use the Database class to call the functions, not instances of the class
    # Also note that to do this, you need to have the '@classmethod' decorator above each of the function definitions
    #   that you write
    Database.add_to_cart(tmp)


if __name__ == '__main__':
    main()