from python

WORKDIR /root
RUN apt-get update && apt-get install -y libarchive-tools
ADD requirements.txt /root/requirements.txt
ADD media-project-credential.json /root/media-project-credential.json
RUN pip3 install --upgrade -r requirements.txt
RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip | bsdtar -xzf -

ADD app.py /root/app.py

CMD ["python", "./app.py"]