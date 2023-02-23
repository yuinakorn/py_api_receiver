from dotenv import dotenv_values
from sqlalchemy.orm import Session
from database import get_connection, Base, SessionLocal
import requests
from datetime import datetime
import pytz

config_env = dotenv_values(".env")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_bed(table: str, api_id: int, db: Session):
    print("get_bed")
    if api_id == 1:
        return insert_bed1(table, api_id, db)
    elif api_id == 2:
        return insert_bed2(table, api_id, db)


def insert_bed1(table: str, api_id: int, db: Session):
    global value, columns, table_name, rows, my_list, i
    url = f"{config_env['URL_NKP']}?bed={api_id}"
    print(url)

    tz = pytz.timezone('Asia/Bangkok')
    rounds = datetime.now(tz).strftime("%H")

    response = requests.request("GET", url)
    datas = response.json()
    connection = get_connection("bed_monitor")
    i = 0

    # insert data into database
    for data in datas:

        rows = []
        for key in data:
            value = data[key]

            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in data.keys())
            rows = ', '.join("'" + str(x).replace('/', '_') + "'" for x in data.values())

        column_string = columns
        column_list = [x.strip("'") for x in column_string.split(", ")]
        column_list[-1] = "rounds"
        column_list = str(column_list)
        column_list_str = column_list.replace("[", "")
        column_list_str = column_list_str.replace("]", "")
        column_list_str = column_list_str.replace("'", "")

        data_string = rows
        data_list = [x.strip("'") for x in data_string.split(", ")]
        data_list[-1] = rounds
        data_list = str(data_list)
        data_list_str = data_list.replace("[", "")
        data_list_str = data_list_str.replace("]", "")

        i = i + 1

        try:
            with connection.cursor() as cursor:
                sql = "REPLACE INTO " + table + " (" + column_list_str + ") VALUES (" + data_list_str + ");"
                cursor.execute(sql)
                connection.commit()

        except:
            print("Error: unable to fetch data")

    connection.close()

    return {"detail": f"inserted {i} records"}


def insert_bed2(table: str, api_id: int, db: Session):
    global value, columns, table_name, rows, my_list, i
    url = f"{config_env['URL_NKP']}?bed={api_id}"
    print(url)

    tz = pytz.timezone('Asia/Bangkok')
    datetime_now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    rounds = datetime.now(tz).strftime("%H")

    response = requests.request("GET", url)
    datas = response.json()
    connection = get_connection("bed_monitor")
    i = 0

    # insert data into database
    for data in datas:

        rows = []
        for key in data:
            value = data[key]

            # columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in data.keys())
            rows = ', '.join("'" + str(x).replace('/', '_') + "'" for x in data.values())

        # column_string = columns
        # column_list = [x.strip("'") for x in column_string.split(", ")]

        column_list_new = "hcode, ward, ward_name, bedcount, admitnow, free, bed_type, d_update, rounds"
        # print(column_list_new)

        # column_list = str(column_list)
        # column_list_str = column_list.replace("[", "")
        # column_list_str = column_list_str.replace("]", "")
        # column_list_str = column_list_str.replace("'", "")

        data_string = rows
        data_list = [x.strip("'") for x in data_string.split(", ")]
        data_list.append(rounds)
        data_list.append("10713")
        data_list.append(datetime_now)
        data_list_new = [
            data_list[-2],
            data_list[1],
            data_list[2],
            data_list[3],
            data_list[4],
            data_list[5],
            data_list[0],
            data_list[-1],
            data_list[-3]
        ]
        # print(data_list_new)
        data_list_new = str(data_list_new)
        data_list_str = data_list_new.replace("[", "")
        data_list_str = data_list_str.replace("]", "")
        # print(data_list_str)

        i = i + 1

        try:
            with connection.cursor() as cursor:
                sql = "REPLACE INTO " + table + " (" + column_list_new + ") VALUES (" + data_list_str + ");"
                print(sql)
                cursor.execute(sql)
                connection.commit()

        except:
            print("Error: unable to fetch data")

    connection.close()

    return {"detail": f"inserted {i} records"}
