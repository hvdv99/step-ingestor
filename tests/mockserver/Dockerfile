FROM python:3.13.9-alpine3.22
COPY . .
USER root
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
EXPOSE 6000
ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "6000"]