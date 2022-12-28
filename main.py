from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values
from sqlalchemy.orm import Session
# from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, Integer
from database import get_connection, Base, SessionLocal
# from pydantic import BaseModel
import time
import json
import requests
import jwt
from datetime import datetime

config_env = dotenv_values(".env")

app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

api_url = config_env["API_URL"]


class Params(Base):
    __tablename__ = "json_params"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    params = Column(String)


class Hcode(Base):
    __tablename__ = "json_hoscode"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    hoscode = Column(String)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Hello API"}


# api receiver # ตัวนำเข้าข้อมูล
@app.post("/{api_name}", status_code=status.HTTP_200_OK,
          tags=["receiver and caller API"])  # api_name is parameter select database
async def receiver(api_name: str, request: Request = Body(..., max_size=100000000)):  # default max_size is 100MB.
    # test api r1
    print("api_name" + api_name)
    if api_name == "send_smog_r1":
        url = config_env["SMOG_R1_URL"]

        json_data = await request.json()
        print(url)
        print(json_data)

        payload = json.dumps(json_data)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

        return {"message": response}
    # end test api r1

    else:
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
            # values_str = values_str.replace('\"None\"', 'NULL')

            if method == "replace":
                # sql = "REPLACE INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"
                columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in dictionary.keys())
                values_str = ', '.join("'" + str(x).replace('/', '_') + "'" for x in dictionary.values())
                values = values_str.replace('\"None\"', 'NULL')
                sql = "REPLACE INTO %s (%s) VALUES (%s);" % (table_name, columns, values)
                print(sql)
            else:
                sql = "INSERT INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"

            i += 1

            try:
                with connection.cursor() as cursor:
                    # cursor.execute(sql)
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

        # url = "https://notify-api.line.me/api/notify"
        #
        # message = "API " + api_name + " end process"

        # payload = f'message={message}'
        # headers = {
        #     'Authorization': 'Bearer ' + config_env["LINE_TOKEN"],
        #     'Content-Type': 'application/x-www-form-urlencoded'
        # }
        #
        # requests.request("POST", url, headers=headers, data=payload)

        return {"detail": "Insert " + str(i) + " rows into " + hoscode + " success"}


# api caller # ตัวเรียกข้อมูล
@app.post("/callapi/{params}/{hosgroup}", status_code=status.HTTP_200_OK, tags=["receiver and caller API"])
async def caller(request: Request, params: str, hosgroup: str, db: Session = Depends(get_db)):
    global hoscode_list, table_name, params_list
    wait_result = request.query_params.get("wait_result")
    method = request.query_params.get("method")

    # if not visit date, set default to current date
    # if request.query_params.get("vstdate") is None:
    #     vstdate = time.strftime("%Y-%m-%d", time.localtime())

    # vstdate = request.query_params.get("vstdate")

    config_api = {
        "api_name": params,
        "wait_result": wait_result,
        "method": method
    }

    params_data = json.loads(db.query(Params).filter(Params.name == params).first().params)
    hoscode_data = json.loads(db.query(Hcode).filter(Hcode.name == hosgroup).first().hoscode)

    for i in params_data:
        params_list = i['params']
        print(params_list)

    for i in hoscode_data:
        hoscode_list = i['hos_code']
        print(hoscode_list)

    for i in params_list:  # loop table
        table_name = i
        for j in hoscode_list:  # loop hospital
            hoscode = j

            print(table_name)

            url = api_url + "/" + table_name + "/" + hoscode + "?wait_result=" + wait_result + "&api=" + \
                  config_api["api_name"] + "&method=" + config_api["method"]

            print(url)

            payload = {}
            headers = {}

            response = requests.request("GET", url, headers=headers, data=payload)

            # status_code = response.status_code

            # json_arr = response.json()
            # print(json_arr)

        time.sleep(3)  # delay 3 seconds

    return {"detail": f"Call API {config_api['api_name']} Success"}


@app.post("/telelog/", status_code=status.HTTP_200_OK, tags=["tele-medicine log"])
async def telelog(request: Request, jwt_str: str, ip: str):
    jwt_decode = jwt.decode(jwt_str, config_env["JWT_SECRET"], algorithms=["HS256"])
    hoscode = "'" + str(jwt_decode["hosCode"]) + "'"
    username = "'" + jwt_decode["username"] + "'"
    doctor_cid = "'" + str(jwt_decode["cid"]) + "'"
    patient_cid = "'" + str(jwt_decode["patientCid"]) + "'"
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    date_time = "'" + str(date_time) + "'"
    ip_client = "'" + str(ip) + "'"
    connection = get_connection('telelog')

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO tele_log (hoscode, username, doctor_cid, patient_cid, start_tele, client_ip) VALUES " \
                  "(%s, %s, %s, %s, CONCAT(CURRENT_DATE,' ',CURRENT_TIME), %s)" % (
                hoscode, username, doctor_cid, patient_cid, ip_client)
            print(sql)
            cursor.execute(sql)
            connection.commit()  # commit the changes
        return {
            "status": "ok",
            "detail": f"Insert tele-log success {now}",
            "client ip": ip
        }

    except Exception as e:
        print(f'This is error: {e}')
        return {
            "status": "fail",
            "detail": str(e),
            "client ip": ip
        }


@app.post("/client/status/", status_code=status.HTTP_200_OK, tags=["client status"])
async def client_status(request: Request):
    connection = get_connection('telelog')
    data = await request.json()

    data_header = request.headers
    if config_env["CHECK_API_TOKEN"] == data_header['api_key']:
        return {
            "status": "ok",
            "detail": data["message"],
            "token": data_header['api_key']
        }
    else:
        return {
            "status": "fail",
            "detail": "invalid api_key",
            "token": data_header['api_key']
        }
