import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        db='hfv',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_stock_codes_from_db():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        db='hfv',
        charset='utf8'
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT code, name FROM stocks")
    result = cursor.fetchall()
    conn.close()
    return result