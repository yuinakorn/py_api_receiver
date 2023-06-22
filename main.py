import asyncio

from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values
from sqlalchemy.orm import Session
# from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, Integer
from starlette.middleware.cors import CORSMiddleware

from database import get_connection, Base, SessionLocal
# from pydantic import BaseModel
import time
import json
import requests
import jwt
from datetime import datetime
import pytz
import threading
from controllers import receiver_controller
from controllers.sent_outer_controller import select_api, sent_to_cmu
from func import insert_data

tz = pytz.timezone('Asia/Bangkok')

config_env = dotenv_values(".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"detail": "Hello"}


outer_api_list = ["send_smog_r1", "send_cleft_cmu"]


# on test ตัวรับข้อมูล
@app.post("/{api_name}", status_code=status.HTTP_200_OK,
          tags=["receiver and caller API"])  # api_name is parameter select database
async def receiver(api_name: str, request: Request = Body(..., max_size=200000000)):  # default max_size is 200MB.
    print(
        "start import api_name: " + api_name + "\n" + "start_time = " + datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"))

    if api_name in outer_api_list:
        select_api(api_name, request)
    else:
        json_data = await request.json()

        # insert_data(api_name, json_data)
        asyncio.create_task(insert_data(api_name, json_data))

        return {
            "message": "import data in progress at " + datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
            "detail": "please check in database"
        }


# api receiver # ตัวนำเข้าข้อมูล
@app.post("/org/{api_name}", status_code=status.HTTP_200_OK,
          tags=["receiver and caller API"])  # api_name is parameter select database
async def receiver(api_name: str, request: Request = Body(..., max_size=100000000)):  # default max_size is 100MB.
    # test api r1
    print("api_name: " + api_name)
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

    elif api_name.startswith("cmu_dent_"):
        try:
            json_data = await request.json()
        except:
            raise HTTPException(status_code=404, detail="Error: json_data")

        return sent_to_cmu(api_name, json_data)
        # print(api_name)
        # return {"detail": "Success: cmu_dent_person"}

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
        print(data)

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

                values = values_str.replace('\"None\"', "''")  # replace "None" to NULL
                values = values.replace("\'None\'", "''")  # replace "None" to NULL

                print(values)
                sql = "REPLACE INTO %s (%s) VALUES (%s);" % (table_name, columns, values)
                print(sql)
            else:
                sql = "INSERT INTO " + table_name + " (" + headers_str + ") VALUES (" + values_str + ");"
                print(sql)

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

        return {"detail": "Insert " + str(i) + " rows into " + hoscode + " success"}


# api caller # ตัวเรียกข้อมูล
@app.post("/callapi/{params}/{hosgroup}", status_code=status.HTTP_200_OK, tags=["receiver and caller API"])
async def caller(request: Request, params: str, hosgroup: str, db: Session = Depends(get_db)):
    global hoscode_list, table_name, params_list
    wait_result = request.query_params.get("wait_result")
    method = request.query_params.get("method")
    # shorten if else
    d1 = request.query_params.get("d1", "")
    d2 = request.query_params.get("d2", "")

    print("d1 = " + str(d1))
    print("d2 = " + str(d2))
    # provider_id = request.query_params.get("provider_id")
    # provider_id = request.query_params.get("provider_id")

    tz = pytz.timezone('Asia/Bangkok')
    rounds = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    print("rounds = " + str(rounds))

    config_api = {
        "api_name": params,
        "wait_result": wait_result,
        "method": method
    }

    # where script_provider = provider
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

            # url = api_url + "/" + table_name + "/" + hoscode + "?wait_result=" + wait_result + "&api=" + \
            url = api_url + "/" + table_name + "/" + hoscode + "?wait_result=" + (wait_result or "") + "&api=" + \
                  config_api["api_name"] + "&method=" + config_api["method"] + "&rounds=" + str(rounds) + \
                  "&d1=" + d1 + "&d2=" + d2

            print(url)

            payload = {}
            headers = {}
            requests.request("GET", url, headers=headers, data=payload)

            # status_code = response.status_code
            # json_arr = response.json()
            # print(json_arr)

        # time.sleep(3)  # delay 3 seconds

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


def make_request(url):
    response = requests.post(url)
    print(response.text)


@app.post("/onecall/{params}/{hosgroup}", status_code=status.HTTP_200_OK, tags=["Custom API"])
async def one_call(request: Request, params: str, hosgroup: str, db: Session = Depends(get_db)):
    global hoscode_list, table_name, params_list, urls
    wait_result = request.query_params.get("wait_result")
    method = request.query_params.get("method")

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

            urls = [url]

    # Create a thread for each URL
    threads = [threading.Thread(target=make_request, args=(url,)) for url in urls]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All requests completed")

    return {"detail": f"Call API {config_api['api_name']} Success"}


@app.post("/api_nkp/{table}/{api_id}", status_code=status.HTTP_200_OK, tags=["NKP API"])
def get_bed(table: str, api_id: int, db: Session = Depends(get_db)):
    return receiver_controller.get_bed(table, api_id, db)
