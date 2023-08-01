
FROM python:3.9.0

MAINTAINER yicheng

RUN mkdir werewolf_kill
WORKDIR werewolf_kill

COPY ["./server.py"  ,"./environment.py" , "./role_setting.json" , "./role.py" , "./requirement.txt" , "./"] 
COPY ./protobufs ./protobufs

RUN apt-get update -y 
RUN pip install -r ./requirement.txt
RUN chmod +x ./server.py

CMD ["python" , "-u" ,"./server.py"]
