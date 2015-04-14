import pymysql
from item import Item


class DatabaseError(Exception):
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
                           "VALUES (%s,%s,%s)", (item.name, item.price, item.weight))
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
                raise DatabaseError('no results for barcode in database')

            # Populate item
            item.name = rows[0][0]
            item.weight = float(rows[0][1])
            item.price = float(rows[0][2])
            item.d_weight = float(rows[0][3])
        else:
            name = item.name
            cls.CURSOR.execute("SELECT price_per_pound FROM produce_db WHERE name='{}'".format(name))
            rows = cls.CURSOR.fetchall()

            if len(rows) > 1:
                # Error non-unique barcode in database
                raise DatabaseError('non-unique name in database')
            elif len(rows) < 1:
                # Error non-existent barcode in database
                raise DatabaseError('no results for name in database')

            # Populate item
            item.price_per_pound = round(float(rows[0][0]), 2)
            # TODO: this is an arbitrary deviation for produce, should be refined
            item.d_weight = 10.0

            # TODO: database will not be updated until produce item is committed with a weight

    @classmethod
    def update_weight(cls, weight):
        cls.CURSOR.execute("UPDATE shopping_cart SET current_load='{}' ORDER BY scan_time LIMIT 1".format(int(weight)))
        cls.CONN.commit()

def main():
    tmp = Item(barcode='0910293')

    # Note that you use the Database class to call the functions, not instances of the class
    # Also note that to do this, you need to have the '@classmethod' decorator above each of the function definitions
    #   that you write
    Database.add_to_cart(tmp)

if __name__ == '__main__':
    main()