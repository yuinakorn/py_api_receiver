# py_api_receiver


This is a simple Python receiver for the [client sender]

# Usage This API

```python 
uvicorn main:app --reload
```

# Usage with Caller

รัน API Caller เพื่อเรียกใช้ API Client จาก Raspberry Pi

ตัว Receiver จะรอรับข้อมูลจาก Client 

# ตัวอย่างการใช้งาน

```http request
http://localhost:8000/callapi/{params}/{กลุ่ม รพ.}?wait_result=no&method={replace}|{deleteinsert}
```

