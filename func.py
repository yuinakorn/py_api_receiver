import pymysql
import pytz
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, DateTime, Float
from database import get_connection, SessionLocal, Base


class DbLog(Base):
    __tablename__ = "api_receiver_log"
    id = Column(Integer, primary_key=True, index=True)
    hcode = Column(String, nullable=True)
    api_name = Column(String, nullable=True)
    method = Column(String, nullable=True)
    table_name = Column(String, nullable=True)
    rows = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    process_time = Column(Float, nullable=True)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


tz = pytz.timezone('Asia/Bangkok')


async def insert_data(api_name: str, json_data):
    print("inside func insert_data")
    start_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    start_times = datetime.now()

    table_name = json_data["table"]
    items = json_data["data"]
    print("json_data = ", json_data)

    columns = ', '.join(items[0].keys())
    print(columns)

    values_list = []
    i = 0
    for item in items:
        values = tuple(item.values())
        values_list.append(values)
        i += 1

    placeholders = ', '.join(['%s'] * len(items[0]))

    if json_data["method"] == "insert":
        query = f"INSERT INTO {table_name} ({', '.join(items[0].keys())}) VALUES ({placeholders})"
    else:
        query = f"REPLACE INTO {table_name} ({', '.join(items[0].keys())}) VALUES ({placeholders})"

    print("rows = ", i)

    try:
        connection = get_connection(api_name)
        if connection is None:
            raise ValueError("Database connection not established")

        with connection.cursor() as cursor:
            try:
                cursor.executemany(query, values_list)
                connection.commit()
                print("Data inserted successfully.")
            except pymysql.Error as e:
                print("Error occurred during data insertion:", e)

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Database Error or API Connection Not Found")

    end_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    end_times = datetime.now()
    time_difference = round((end_times - start_times).total_seconds(), 2)

    logs = {
        "hcode": json_data["hcode"],
        "api_name": api_name,
        "table_name": table_name,
        "method": json_data["method"],
        "rows": i,
        "start": start_time,
        "end": end_time,
        "process_time": time_difference
    }
    print("end_time = ", end_time)
    write_log(logs)


def write_log(logs):
    try:
        new_log = DbLog(
            hcode=logs["hcode"],
            api_name=logs["api_name"],
            method=logs["method"],
            table_name=logs["table_name"],
            rows=logs["rows"],
            start_time=logs["start"],
            end_time=logs["end"],
            process_time=logs["process_time"]
        )
        db = SessionLocal()
        db.add(new_log)
        db.commit()
        db.close()

    except Exception as e:
        print("Error: ", e)
