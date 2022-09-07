# linux/amd64
#FROM python:3.10.1-slim@sha256:a7deebfd654d0158999e9ae9a78ce4a9c7090816a2d1600d254fef8b7fd74cac

# m1
FROM python:3.10.1-slim
#FROM python:3.10.1-slim@sha256:af2fdce86a94ed06cad169db81602b3492501d302d83ef94e6f62794bd1bc821
#
WORKDIR /app

#
COPY ./requirements.txt /app/requirements.txt

#
#RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

#
COPY . /app

#
CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
