FROM python:3.10-slim

# install pyarmor
RUN pip install pyarmor

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

# copy assets
COPY app.py templates/ static/

EXPOSE 5000
CMD ["python","app.py"]
