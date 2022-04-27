import os
import sqlite3

from crawlers.settings import DATA_PATH
from crawlers.items import BookItem


class DB:

    DB_PATH = os.path.join(DATA_PATH, "data.db")
    __con = sqlite3.connect(DB_PATH)
    __cur = __con.cursor()

    @classmethod
    def init(cls):
        cls.__cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            name text,
            author text,
            type text,
            url text,
            lastupdate text,
            total_chapters INT,
            download_chapters INT
        )
        ''')
        cls.__con.commit()

    @classmethod
    def insert(item: BookItem):
        sql = '''
        INSERT OR REPLACE INTO books 
        (id,name,author,type,url,lastupdate,total_chapters,download_chapters)
        values (?,?,?,?,?,?,?,?);
        '''
        cls.__cur.execute(sql, (
            item['bid'],
            item['bname'],
            item['author'],
            item['btype'],
            item['url'],
            item['lastupdate'],
            item['total_chapters'],
            item['download_chapters']
        ))

    @classmethod
    def needUpdateBook(cls, item: BookItem):
        sql = '''
        SELECT 
        total_chapters,download_chapters
        FROM books WHERE id = ?;
        '''
        cls.__cur.execute(sql, (item['bid'],))
        result = cls.__cur.fetchone()
        if not result:
            return True
        return result[0] != item['total_chapters'] or result[0] > result[1] or item['total_chapters'] > result[1]

    @classmethod
    def close(cls):
        cls.__con.commit()
        cls.__con.close()
