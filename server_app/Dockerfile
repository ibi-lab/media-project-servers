#################################################################################################
# Build Julius
#################################################################################################

FROM ubuntu:20.04 AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \
    apt install --yes curl gcc libasound2-dev make unzip && \
    apt clean && \
    curl -fsSL https://github.com/julius-speech/julius/archive/refs/tags/v4.6.tar.gz | tar -xz && \
    mv /julius-4.6 /julius
WORKDIR /julius
RUN ./configure --build=aarch64 --prefix=/usr/local/lib/julius --with-mictype=alsa --enable-setup=standard && \
    make && \
    make install && \
    curl -fsSL "https://osdn.net/frs/redir.php?m=nchc&f=julius%2F71011%2Fdictation-kit-4.5.zip" -o dictation-kit.zip && \
    unzip dictation-kit.zip && \
    mv dictation-kit-* /usr/local/lib/julius/dictation-kit

#################################################################################################
# Build server app container
#################################################################################################

from ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \
    apt install --yes libasound2 libopenmpi-dev && \
    apt clean
COPY --from=build /usr/local/lib/julius /usr/local

WORKDIR /root
RUN apt-get install -y libarchive-tools python3 python3-pip python3-pexpect curl
ADD requirements.txt /root/requirements.txt
ADD media-project-credential.json /root/media-project-credential.json
RUN pip3 install --upgrade -r requirements.txt
RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip | bsdtar -xzf -

RUN ls
ADD app.py /root/app.py

CMD ["python3", "./app.py"]