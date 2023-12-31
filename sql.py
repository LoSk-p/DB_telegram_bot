from dataclasses import dataclass
import sqlite3
import os
import logging
import typing as tp
from dataclasses import dataclass

from config.config import BD_NAME

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@dataclass
class Material:
    caption: tp.Optional[str] = None
    text: tp.Optional[str] = None
    file: tp.Optional[bytes] = None
    filename: tp.Optional[str] = None
    picture: tp.Optional[bytes] = None
    sent: str = "False"

    def get_list(self, number: int):
        return [number, self.caption, self.text, self.file, self.filename, self.picture, self.sent]

class DataDB:
    def __init__(self, name: str = BD_NAME):
        self.con = None
        self.cur = None
        self.name = name
        self.material_data = None
        if not os.path.isfile(name):
            self.create_new_bd(name)
        else:
            self.con = sqlite3.connect(name)
            self.cur = self.con.cursor()

    def connect_bd(func):
        def wrapper(self, *args, **kwargs):
            self.con = sqlite3.connect(self.name)
            self.cur = self.con.cursor()
            logging.info(f"Connected to BD")
            res = func(self, *args, **kwargs)
            self.con.close()
            self.con = None
            self.cur = None
            logging.info(f"Connection to BD {self.name} was closed")
            return res
        return wrapper

    def create_material(self, caption: tp.Optional[str] = None,
                        text: tp.Optional[str] = None,
                        file: tp.Optional[bytes] = None,
                        filename: tp.Optional[str] = None,
                        picture: tp.Optional[bytes] = None):
        self.material_data = Material(caption, text, file, filename, picture)

    def update_material(self, caption: tp.Optional[str] = None,
                        text: tp.Optional[str] = None,
                        file: tp.Optional[bytes] = None,
                        filename: tp.Optional[str] = None,
                        picture: tp.Optional[bytes] = None):
        if self.material_data is not None:
            if caption is not None:
                self.material_data.caption = caption
            if text is not None:
                self.material_data.text = text
            if file is not None:
                self.material_data.file = file
            if filename is not None:
                self.material_data.filename = filename
            if picture is not None:
                self.material_data.picture = picture
        else:
            self.create_material(caption, text, file, filename, picture)

    @connect_bd
    def add_material(self):
        next_number = self._get_rows_number_materials()
        fields = self.material_data.get_list(next_number)
        self.cur.execute("INSERT INTO materials VALUES(?,?,?,?,?,?,?)", fields)
        self.con.commit()
        self.material_data = None

    @connect_bd
    def delete_material(self, number: int):
        materials_number = self._get_rows_number_materials()
        self.cur.execute("DELETE FROM materials WHERE number LIKE ?", [number])
        i = number + 1
        while i < materials_number:
            self.cur.execute("UPDATE materials SET number = ? WHERE number LIKE ?", [str(i - 1), str(i)])
            i += 1
        self.con.commit()

    @connect_bd
    def create_new_bd(self, name: str):
        self.con = sqlite3.connect(name)
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE materials(number, caption, text, file, filename, picture, sent)")
        self.cur.execute("CREATE TABLE users(user_id)")
        logging.info(f"New DB {name} was created")

    @connect_bd
    def get_not_sent(self) -> list:
        res = self.cur.execute("SELECT number, caption, text, file, filename, picture FROM materials WHERE sent LIKE 'False'")
        return self._format_rows(res.fetchall())

    @connect_bd
    def set_sent(self, number: int):
        self.cur.execute("UPDATE materials SET sent = 'True' WHERE number LIKE ?", str(number))
        self.con.commit()
        logging.info(f"Set sent True for {number} material")

    @connect_bd
    def add_user(self, user_id: str):
        if user_id not in self._get_users():
            self.cur.execute("INSERT INTO users VALUES(?)", [user_id])
            self.con.commit()
            logging.info(f"Added new user {user_id}")
        else:
            logging.info(f"User {user_id} already exists")

    @connect_bd
    def get_users(self) -> list:
        return self._get_users()

    @connect_bd
    def get_last_materials(self, number_of_rows: int = None) -> list:
        result = []
        max_number = self._get_rows_number_materials()
        if (number_of_rows is None) or (number_of_rows == max_number):
            number_of_rows = max_number
        for i in range(number_of_rows):
            res = self.cur.execute("SELECT number, caption, text, file, filename, picture FROM materials WHERE number LIKE ?", str(max_number - 1 - i))
            result.append(res.fetchall()[0])
        return self._format_rows(result)

    @connect_bd
    def delete_user(self, user_id: str):
        self.cur.execute("DELETE FROM users WHERE user_id LIKE ?", [user_id])
        self.con.commit()
        logging.info(f"User {user_id} was deleted")
    
    def _get_users(self) -> list:
        res = self.cur.execute("SELECT user_id FROM users")
        res_list = res.fetchall()
        new_res = [i[0] for i in res_list]
        return new_res

    def _get_rows_number_materials(self) -> int:
        res = self.cur.execute("SELECT COUNT(number) FROM materials")
        return res.fetchall()[0][0]

    def _format_rows(self, rows: list) -> list:
        result = []
        for row in rows:
            result.append({
                "number": row[0], 
                "caption": row[1], 
                "text": row[2],
                "file": row[3],
                "filename": row[4],
                "picture": row[5]
            })
        return result

