from fastapi import FastAPI, Request, status, HTTPException
from dotenv import dotenv_values
from database import get_connection
import time

config_env = dotenv_values(".env")

app = FastAPI()

api_url = config_env["API_URL"]


@app.get("/")
async def root():
    return {"message": "Hello API"}


@app.post("/{api_name}", status_code=status.HTTP_200_OK, tags=["Create"])
async def api(request: Request, api_name: str):
    json_data = await request.json()
    i = 0
    hoscode = str(json_data["hcode"])
    table_name = json_data["table"]
    method = json_data["method"]

    connection = get_connection(api_name)

    if connection is None:
        raise HTTPException(status_code=404, detail="API Not Found")

    if method == "deleteinsert":
        sql_delete = "DELETE FROM " + table_name + " WHERE HOSPCODE = " + hoscode + ";"
        print(sql_delete)
        with connection.cursor() as cursor:
            cursor.execute(sql_delete)
            connection.commit()
        print({"detail": "Delete Success"})

    data = json_data["data"]

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

        if method == "replace":
            sql = "REPLACE INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"
            print(sql)
        else:
            sql = "INSERT INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"

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
            return {"detail": error}

    with open('log.txt', 'a') as f:
        current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f'{current_date} Insert {i} rows into {hoscode} success \n')

    connection.close()

    return {"detail": "Insert " + str(i) + " rows into " + hoscode + " success"}
