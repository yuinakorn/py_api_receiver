import json
import requests
from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values

# from starlette.middleware.cors import CORSMiddleware

config_env = dotenv_values("../.env")

app = FastAPI()


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# api_url = config_env["API_URL"]

async def sent_to_cmu(request):
    print("inside function: sent_to_cmu")
    url = config_env["CMU_DENT_URL"]
    print(url)
    json_data = await request.json()
    # data = {"data": json_data}
    # payload = json.dumps(data)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(payload)

    return response


def select_api(api_name, request):
    if api_name == 'send_smog_r1':
        send_smog_r1(request)
    elif api_name == 'send_cleft_cmu':
        print("inside select_api send_cleft_cmu")
        sent_to_cmu(request)


def send_smog_r1(request):
    url = config_env["SMOG_R1_URL"]

    json_data = request.json()
    print(url)
    # print(json_data)

    payload = json.dumps(json_data)
    headers = {
        'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload)
