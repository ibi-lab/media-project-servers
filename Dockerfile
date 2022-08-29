from python

WORKDIR /root
RUN pip3 install Flask werkzeug 
RUN pip3 install flask-wtf
RUN pip3 install flask_bootstrap
RUN pip install --upgrade google-cloud-texttospeech
RUN pip3 install vosk

ADD app.py /root/app.py
ADD model /root/model/
# ADD voice2conv.wav /root/voice2conv.wav

CMD ["python", "./app.py"]