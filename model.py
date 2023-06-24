import os
import psycopg2
from dotenv import load_dotenv
from enum import Enum
from flask import abort
from flask_login import UserMixin
from typing import Optional

load_dotenv()


def execute_query(query, values=tuple(), fetchall=False, fetchone=False):
    def get_db_connection():
        conn = psycopg2.connect(host=os.environ['FLASK_DB_HOSTNAME'],
                                database='wedding_seating_chart',
                                user=os.environ['FLASK_DB_USERNAME'],
                                password=os.environ['FLASK_DB_PASSWORD'])
        return conn

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            if fetchone:
                return cur.fetchone()
            elif fetchall:
                return cur.fetchall()


class Sex(Enum):
    MALE = "Чоловік"
    FEMALE = "Жінка"
    UNKNOWN = "Невідомо"


class Side(Enum):
    BRIDE = "Наречена"
    GROOM = "Наречений"
    BOTH = "Наречені"


class Guest:
    id: int
    guest_name: str
    profile_image: Optional[str] = None
    guest_sex: Sex
    guest_age: Optional[int] = None
    guest_description: Optional[str] = ""
    guest_phone_number: Optional[str] = ""
    guest_contact: Optional[str] = None
    table_number: Optional[int] = None
    seat_number: Optional[int] = None
    guest_side: Side

    def __init__(self, args, escape_none=True):
        self.id = args[0]
        self.name = args[1]
        self.profile_image = args[2]
        self.sex = args[3]
        self.age = args[4]
        self.description = args[5]
        self.phone_number = args[6]
        self.contact = args[7]
        if escape_none:
            self.table_number = args[8] or "--"
            self.seat_number = args[9] or "--"
        else:
            self.table_number = args[8]
            self.seat_number = args[9]
        self.side = args[10]


def pop_unused_keys(kwargs):
    unused_keys = ('csrf_token', 'delete', 'cancel')
    for unused_key in unused_keys:
        if unused_key in kwargs:
            kwargs.pop(unused_key)
    return kwargs


def validate_table_seat_numbers(kwargs):
    if kwargs['table_number'] == "--":
        kwargs['table_number'] = None
    if kwargs['seat_number'] == "--":
        kwargs['seat_number'] = None
    return kwargs


def insert_guest(**kwargs):
    kwargs = pop_unused_keys(kwargs)
    kwargs = validate_table_seat_numbers(kwargs)

    query = f'INSERT INTO guests (guest_name, profile_image, guest_sex, guest_age, ' \
            f'guest_description, guest_phone_number, guest_contact, table_number, ' \
            f'seat_number, guest_side) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ) RETURNING id;'
    execute_query(query, (tuple(kwargs.values())))


def update_guest(**kwargs):
    kwargs = pop_unused_keys(kwargs)
    kwargs = validate_table_seat_numbers(kwargs)

    query = f'UPDATE guests SET guest_name = %s, profile_image = %s, guest_sex = %s, guest_age = %s, ' \
            f'guest_description = %s, guest_phone_number = %s, guest_contact = %s, table_number = %s, ' \
            f'seat_number = %s, guest_side = %s, update_date = now() WHERE id = %s;'

    execute_query(query, (tuple(kwargs.values())))


def get_all_guests():
    query = 'SELECT * FROM guests order by create_date;'
    guests = execute_query(query, fetchall=True)
    res = [Guest(guest) for guest in guests]
    return res


def get_guest_by_id(guest_id, escape_none=False):
    query = f'SELECT * FROM guests WHERE ID = %s;'
    guest_info = execute_query(query, ((guest_id,),), fetchone=True)
    if guest_info:
        return Guest(guest_info, escape_none=escape_none)
    else:
        return abort(404)


def get_guests_by_table(table_id):
    query = f"SELECT * FROM guests WHERE TABLE_NUMBER = %s;"
    table_guests = execute_query(query, ((table_id,),), fetchall=True)
    return [Guest(guest_info) for guest_info in table_guests]


def delete_guest_by_id(guest_id):
    query = f"DELETE FROM guests WHERE ID = %s;"
    execute_query(query, ((guest_id,),))
