FROM python:3.10-alpine

# Create stdconfig directory
WORKDIR /

COPY solarflow.py /

RUN pip install requests paho-mqtt
CMD ["python","solarflow.py"]
