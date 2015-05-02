import pymysql
from subprocess import Popen, PIPE
import re


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
    def add_to_inventory(cls, pro_color, pro_shape, pro_name, pro_price):
        cls.CURSOR.execute("INSERT INTO produce_db_2 (color, shape, result, price_per_pound)"
                           "VALUES (%s,%s,%s,%s)", (pro_color, pro_shape, pro_name, pro_price))
        cls.CONN.commit()

    @classmethod
    def check_in_inventory(cls, pro_color, pro_shape):
        cls.CURSOR.execute("SELECT * FROM produce_db_2 WHERE color=%s AND shape=%s", (pro_color, pro_shape))
        rows = cls.CURSOR.fetchall()
        return rows

def main():
	image_name = './images/thisImage.jpg'
	(out, err) = Popen(['python', 'script_thread.py'], stdout=PIPE).communicate()
	out = out.strip()

	result = out.strip(';')
	result2 = result.split(':')

	# DEBUG
	# print 'Result:', result

	# result2[1] = ';'.strip(result2[1])

	name = raw_input('Enter Produce Name: ')
	price = raw_input('Enter Produce Price Per Pound: ')

	return_results = Database.check_in_inventory(result2[0], result2[1])
	same_boolean = 0
	for n in return_results:
			if n[2] == name:
				print "Item already in inventory",
				same_boolean = 1
			
	if same_boolean == 0:
		Database.add_to_inventory(result2[0], result2[1], name, price)

if __name__ == '__main__':
    main()