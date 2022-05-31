FROM python:latest

WORKDIR /usr/app/script/

COPY . .

RUN pip3 install -r requirements.txt

CMD [ "python", "tools.py"]
