import time
from fastapi import FastAPI, Request, Response, status
from dotenv import dotenv_values
import pymysql
import json
from typing import List

config_env = dotenv_values(".env")

app = FastAPI()

connection = pymysql.connect(host=config_env["HOST"],
                             user=config_env["USER_DB"],
                             password=config_env["PASS_DB"],
                             db=config_env["DB_NAME"],
                             charset=config_env["DB_CHARSET"],
                             )

api_url = config_env["API_URL"]


@app.get("/")
async def root():
    return {"message": "Hello API"}


@app.post("/{api_name}/", status_code=200, tags=["Create"])
async def student(request: List, api_name: str, method: str | None = None, hcode: str | None = None):
    i = 0
    table_name = "hosxp_school"
    print(api_name)
    print(method)
    print(hcode)

    # sql_delete = "DELETE FROM " + table_name + " WHERE HOSPCODE = " + hcode + ";"
    # print(sql_delete)

    # json_data = await request.json()
    # covert request to list

    data = request[0]

    # print data where key = data
    for key, value in data.items():
        if key == "data":
            data = value
            # print(data)

    # data = json_data["data"]

    for item in data:
        dictionary = item
        print(dictionary)

        headers = []
        values = []
        for key in dictionary:
            value = dictionary[key]
            headers.append(key)
            values.append(value)

        # convert list to string with double quote
        headers_str = ','.join(headers)
        values_str = '"' + '","'.join(map(str, values)) + '"'  # map(str, values) convert int to str
        # replace "None" to NULL
        values_str = values_str.replace('\"None\"', 'NULL')

        sql = "INSERT IGNORE INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"
        # print(sql)

        i += 1

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()  # commit the changes
        except Exception as e:
            print(f'This is error: {e}')
            error = str(e)
            connection.rollback()  # rollback if any exception occurred (optional)
            # write log to file
            with open('log.txt', 'a') as f:
                current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                f.write(f'{current_date} {error} \n')
            return {"message": error}

    with open('log.txt', 'a') as f:
        current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f'{current_date} inserted {i} rows \n')

    return {"message": "Insert " + str(i) + " rows"}
    # return {"message": "Look good"}
