import json
import requests
from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values
# from starlette.middleware.cors import CORSMiddleware

# for Minio
import os
from configobj import ConfigObj
from s3fs import S3FileSystem

config_env = dotenv_values(".env")

app = FastAPI()


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

def send_cmdac(api_name: str, json_data):
    # ตรวจสอบไฟล์ที่จะสร้าง และลบไฟล์เก่าออก
    hcode = json_data["hcode"]
    file_name = f"{api_name}_{hcode}.json"
    file_path_name = f"./files_upload/{file_name}"

    # delete file if exists
    if os.path.exists(file_path_name):
        os.remove(file_path_name)
        print("file deleted.")
        with open(file_path_name, 'w') as f:
            json.dump(json_data, f)
            print("file re-created.")
    else:
        # create a new file with json_data
        with open(file_path_name, 'w') as f:
            json.dump(json_data, f)
            print("file new created.")

    # อ่านค่าจาก config.ini
    conf: dict = ConfigObj('config.ini', raise_errors=True)
    conf.keys()

    # อ่านค่าจาก section ที่ชื่อว่า minio ใน config.ini จากนั้นสร้าง connection ไปที่ minio
    minio_conf = conf["minio"]

    s3: S3FileSystem = S3FileSystem(
        anon=False,
        key=minio_conf["key"],
        secret=minio_conf["secret"],
        endpoint_url=minio_conf["endpoint_url"],
    )

    bucket = conf["minio"]["bucket"]
    path_prefix = conf["minio"]["path"]
    # list all files in bucket
    # s3.ls(f"{bucket}/{path_prefix}")

    # upload file to minio server
    s3_filepath: str = f"{bucket}/{path_prefix}/{file_name}"
    local_filepath: str = file_path_name

    # check file exists
    if s3.exists(s3_filepath):
        print(f"{s3_filepath} - file exists ")
        print("Overwrite if exists.")

    # upload file (Overwrite if exists)
    print("Upload file to : ", local_filepath)
    s3.put(local_filepath, s3_filepath)

    # show file upload
    s3.ls(s3_filepath)

    print("file uploaded.")

    return s3.ls(s3_filepath)


def select_api(api_name: str, json_data):
    # global api_url
    print("inside select_api")

    upper_api_name = api_name.upper()

    print("api_name = ", upper_api_name)

    # if upper_api_name == 'SEND_SMOG_R1':
    #     api_url = config_env["SEND_SMOG_R1"]
    # elif upper_api_name == 'SEND_CLEFT_CMU':
    #     api_url = config_env["SEND_CLEFT_CMU"]

    # api_url = config_env["SEND_CLEFT_CMU"]

    api_url = config_env[str(upper_api_name)]
    print("api_url = ", api_url)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", api_url, headers=headers, data=payload)
    print("payload = ", payload)

    print("response = ", response.text)

    return {"message": response.text}

    # if api_name == 'send_smog_r1':
    #     send_smog_r1(json_data)
    # elif api_name == 'send_cleft_cmu':
    #     print(f"inside select_api {api_name}")
    #     print("request json = ", json_data)
    #     sent_to_cmu(json_data)
    # else:
    #     print("API not found")


# ไม่ได้ใช้แล้ว
def send_smog_r1(json_data):
    url = config_env["SMOG_R1_URL"]

    # json_data = request.json()
    print(url)
    # print(json_data)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print("payload = ", payload)
    return response


# ไม่ได้ใช้แล้ว
def sent_to_cmu(json_data):
    print("inside function: sent_to_cmu")
    url = config_env["CMU_DENT_URL"]
    print(url)
    # json_data = request.json()
    # data = {"data": json_data}
    # payload = json.dumps(data)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print("payload = ", payload)

    return response
