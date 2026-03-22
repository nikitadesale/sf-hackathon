FROM python:3.11-slim
WORKDIR /app
RUN pip install flask gunicorn
COPY main.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
