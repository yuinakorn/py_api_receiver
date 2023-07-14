import json
import requests
from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values

# from starlette.middleware.cors import CORSMiddleware

config_env = dotenv_values(".env")

app = FastAPI()


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# api_url = config_env["API_URL"]

def select_api(api_name: str, json_data):
    global api_url
    print("inside select_api")
    upper_api_name = api_name.upper()

    print("api_name = ", upper_api_name)

    if upper_api_name == 'SEND_SMOG_R1':
        api_url = config_env["SEND_SMOG_R1"]
    elif upper_api_name == 'SEND_CLEFT_CMU':
        api_url = config_env["SEND_CLEFT_CMU"]

    # api_url = config_env[str(upper_api_name)]
    print("api_url = ", api_url)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", api_url, headers=headers, data=payload)
    print("payload = ", payload)

    return {"message": response}

    # if api_name == 'send_smog_r1':
    #     send_smog_r1(json_data)
    # elif api_name == 'send_cleft_cmu':
    #     print(f"inside select_api {api_name}")
    #     print("request json = ", json_data)
    #     sent_to_cmu(json_data)
    # else:
    #     print("API not found")


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
