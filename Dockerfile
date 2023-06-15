FROM python:3.10.1-slim

WORKDIR /app

COPY requirements.txt .

# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
# CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
# Set the command to start Gunicorn
CMD ["gunicorn", "main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]