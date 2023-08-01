
FROM python:3.9.0

MAINTAINER yicheng

RUN mkdir werewolf_kill
WORKDIR werewolf_kill

COPY ./server.py ./server.py
COPY ./protobufs ./protobufs
COPY ./environment.py ./environment.py
COPY ./role_setting.json ./role_setting.json
COPY ./role.py ./role.py
COPY ./requirement.txt ./requirement.txt

RUN apt-get update -y 
RUN pip install -r ./requirement.txt
RUN chmod +x ./server.py

CMD ["python" , "./server.py"]
