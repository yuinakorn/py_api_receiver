import json
import requests
from fastapi import FastAPI, Request, status, HTTPException, Depends, Body
from dotenv import dotenv_values
from starlette.middleware.cors import CORSMiddleware

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


def sent_to_cmu(api_name, json_data):
    print("api_name = ", api_name)
    print("sent_to_cmu")
    url = config_env["CMU_DENT_URL"]
    print(url)
    data = {"table_name": api_name, "data": json_data}

    payload = json.dumps(data)
    headers = {
        'Content-Type': 'application/json'
    }

    # response = requests.request("POST", url, headers=headers, data=payload)

    print(data)

    return data

