import os
import json

import aiosqlite
from typing import Dict, Any, Tuple, Deque
from enum import Enum
import logging

WAL_MODE = "PRAGMA journal_mode=WAL"
DB_NAME = "comfy.db"
DB_PATH = None


def get_db_path():
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_NAME)
    return DB_PATH


class Table(Enum):
    NODE_LOCATIONS = "node_locations"
    NODE_ATTRIBUTES = "node_attributes"
    MODULES = "modules"


async def create_table(
    conn: aiosqlite.Connection, table_name: str, columns: Dict[str, str]
):
    columns_str = ", ".join([f"{k} {v}" for k, v in columns.items()])
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
    try:
        async with conn.execute(create_table_query) as cursor:
            await cursor.close()
    except aiosqlite.Error as e:
        print(
            f"Error creating table: {e}. Details\nTable Name: {table_name}\nColumns: {columns}"
        )


async def init_db():
    async with aiosqlite.connect(get_db_path()) as conn:
        await create_table(
            conn,
            Table.MODULES.value,
            {
                "module_path": "TEXT",
                "mtime": "REAL",
                "web_directory": "TEXT",
                "class_mappings": "JSON",
                "display_name_mappings": "JSON",
            },
        )
        await create_table(
            conn,
            Table.NODE_LOCATIONS.value,
            {"class_name": "TEXT", "class_path": "TEXT", "mtime": "REAL"},
        )
        await create_table(
            conn,
            Table.NODE_ATTRIBUTES.value,
            {
                "name": "TEXT",
                "input": "JSON",
                "output": "JSON",
                "output_is_list": "JSON",
                "output_name": "JSON",
                "display_name": "TEXT",
                "description": "TEXT",
                "python_module": "TEXT",
                "category": "TEXT",
                "output_node": "INTEGER",
            },
        )


def delete_db():
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info(f"Deleted {DB_NAME}")
    else:
        logging.warn(f"{DB_NAME} not found at {db_path}")


async def execute_query(
    conn: aiosqlite.Connection, query: str, values: Tuple[Any, ...] = ()
):
    try:
        async with conn.execute(query, values) as cursor:
            await cursor.close()
    except aiosqlite.Error as e:
        print(f"Error executing query:\n\t{e}\n\tQuery: {query}\n\tValues: {values}")


async def set_wal_mode(conn: aiosqlite.Connection, wal_mode: bool):
    if wal_mode:
        await execute_query(conn, WAL_MODE)


async def insert_queue(
    conn: aiosqlite.Connection,
    table_name: Table,
    updates: Deque[Dict[str, Any]],
    wal_mode: bool = True,
):
    await set_wal_mode(conn, wal_mode)
    while updates:
        record = updates.popleft()
        for key, value in record.items():
            if isinstance(value, (dict, list, tuple)):
                record[key] = json.dumps(value)

        columns = ", ".join(record.keys())
        placeholders = ", ".join(["?"] * len(record))
        values = tuple(record.values())
        insert_query = f"INSERT OR REPLACE INTO {table_name.value} ({columns}) VALUES ({placeholders})"
        await execute_query(conn, insert_query, values)
    await conn.commit()


async def insert_node_locations(updates: Deque[Dict[str, str]]):
    async with aiosqlite.connect(DB_NAME) as conn:
        await insert_queue(conn, Table.NODE_LOCATIONS, updates)


async def insert_node_attributes(updates: Deque[Dict[str, Any]]):
    async with aiosqlite.connect(DB_NAME) as conn:
        await insert_queue(conn, Table.NODE_ATTRIBUTES, updates)


async def insert_modules(updates: Deque[Dict[str, Any]]):
    async with aiosqlite.connect(DB_NAME) as conn:
        await insert_queue(conn, Table.MODULES, updates)


async def select_one(
    conn: aiosqlite.Connection,
    table_name: Table,
    select_fields: str,
    where: Dict[str, Any],
):
    where_str = " AND ".join([f"{k} = ?" for k in where.keys()])
    select_query = f"SELECT {select_fields} FROM {table_name.value} WHERE {where_str}"
    try:
        async with conn.execute(select_query, tuple(where.values())) as cursor:
            return await cursor.fetchone()

    except aiosqlite.Error as e:
        print(
            f"Error selecting from table:\n\t{e}\nTable Name: {table_name.value}\nSelect Fields: {select_fields}\nWhere: {where}"
        )


async def get_node_location_by_name(
    conn: aiosqlite.Connection, name: str, select_fields: str = "*"
):
    return await select_one(
        conn, Table.NODE_LOCATIONS, select_fields, {"class_name": name}
    )


async def get_node_attributes_by_name(
    conn: aiosqlite.Connection, name: str, select_fields: str = "*"
):
    return await select_one(conn, Table.NODE_ATTRIBUTES, select_fields, {"name": name})


async def get_module_by_path(
    conn: aiosqlite.Connection, path: str, select_fields: str = "*"
):
    return await select_one(conn, Table.MODULES, select_fields, {"module_path": path})
