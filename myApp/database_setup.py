# -*- coding: utf-8 -*-
"""
Created on Mon May  6 21:43:48 2019

@author: demerss1
"""

import sqlite3
import pandas as pd
import os

import datetime as dt

from typing import List


path = os.getcwd()
path = path[path.rindex("\\") + 1:]
if path == "Web Application":
    db = "myApp/water.db"
else:
    db = "water.db"


def create_database() -> None:
    with sqlite3.connect(db) as con:

        # keeps track of which user has which tester
        # also keeps track of tester configuration
        create_user_info = """CREATE TABLE IF NOT EXISTS user_info(
                              ID INTEGER NOT NULL,
                              userName TEXT NOT NULL,
                              password TEXT NOT NULL,
                              frequency INTEGER NOT NULL,
                              pH BOOLEAN NOT NULL,
                              TDS BOOLEAN NOT NULL,
                              Coliform BOOLEAN NOT NULL,
                              PRIMARY KEY(ID));"""

        # keeps track of tester configuration
        create_tester_info = """CREATE TABLE IF NOT EXISTS tester_info(
                                ID INTEGER NOT NULL,
                                pH BOOLEAN NOT NULL,
                                TDS BOOLEAN NOT NULL,
                                Coliform BOOLEAN NOT NULL,
                                PRIMARY KEY(ID));"""

        # keeps track of tests that have been performed
        create_tester_data = """CREATE TABLE IF NOT EXISTS tester_data(
                                ID INTEGER NOT NULL,
                                date TEXT NOT NULL,
                                pH REAL NOT NULL,
                                TDS REAL NOT NULL,
                                Coliform BOOLEAN NOT NULL,
                                PRIMARY KEY(ID, date));"""

        con.cursor().execute(create_tester_data)
        con.cursor().execute(create_user_info)
        con.cursor().execute(create_tester_info)
        con.commit()


def get_tnames() -> List[str]:
    """
    Gets all table names as a List[str]
    """
    query = "SELECT name FROM sqlite_master WHERE type='table'"
    with sqlite3.connect(db) as con:
        df = pd.read_sql(query, con)
    return list(df["name"])


def drop_t(table_name: str = "all") -> None:
    """
    Quick function to drop one table
    If you want all tables input all
    becuase of this do not name a table all
    """
    if table_name == "all":
        names = get_tnames()
        with sqlite3.connect('water.db') as con:
            for name in names:
                query = f"DROP TABLE IF EXISTS '{name}'"
                con.cursor().execute(query)
    else:
        query = f"DROP TABLE IF EXISTS {table_name}"
        with sqlite3.connect(db) as con:
            con.cursor().execute(query)


def qquery(query: str) -> pd.DataFrame:
    """
    Used so you dont have to worry about opening database.
    Just insert sql query and get a dataframe of that query.
    """
    with sqlite3.connect(db) as con:
        df = pd.read_sql(query, con)
    return df. copy()


def fake_tester_info() -> None:
    with sqlite3.connect(db) as con:
        for i in range(1, 11):
            if i % 2 == 0:
                values = f"{i}, TRUE, TRUE, TRUE"
            else:
                values = f"{i}, TRUE, TRUE, TRUE"
            query = f"INSERT INTO tester_info VALUES ({values})"
            con.cursor().execute(query)
        con.commit()


def fake_tester_data() -> None:
    with sqlite3.connect(db) as con:
        for i in range(1, 5):
            if i % 2 == 0:
                for j in range(2):
                    date = dt.datetime(2019 - j, 4, 20)
                    values = f"{i}, '{date}', 7.0, 100, FALSE"
                    query = f"INSERT INTO tester_data VALUES ({values})"
                    con.cursor().execute(query)
            else:
                date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                values = f"{i}, '{date}', 6.0, 100, TRUE"
                query = f"INSERT INTO tester_data VALUES ({values})"
                con.cursor().execute(query)
        con.commit()


def refresh_database() -> None:
    drop_t()
    create_database()
    fake_tester_info()
    fake_tester_data()


if __name__ == "__main__":
    # refresh databaase
    refresh_database()
    df = qquery("select * from tester_data")
