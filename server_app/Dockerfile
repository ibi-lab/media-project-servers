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
    apt install --yes libasound2 libopenmpi-dev gnupg2 curl && \
    apt clean

RUN set -e; \
    apt-get update -y && apt-get install -y \
    tini \
    lsb-release; \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s`; \
    echo "deb http://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    tee /etc/apt/sources.list.d/gcsfuse.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key add -; \
    apt-get update; \
    apt-get install -y gcsfuse \
    && apt-get clean

# Set fallback mount directory
ENV MNT_DIR /mnt/stt_settings
ENV BUCKET stt_settings
# ENV PORT 3000
# EXPOSE 3000

ADD run.sh /root/run.sh
COPY --from=build /usr/local/lib/julius /usr/local
WORKDIR /root
COPY templates/ /root/templates/
RUN apt-get install -y libarchive-tools python3 python3-pip python3-pexpect curl
ADD requirements.txt /root/requirements.txt
ADD media-project-credential.json /root/media-project-credential.json
RUN pip3 install --upgrade -r requirements.txt
RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip | bsdtar -xzf -

RUN ls
COPY *.py /root/

CMD ["python3", "./app.py"]

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"] 

# Pass the startup script as arguments to Tini
# CMD ["/root/run.sh"]
# [END cloudrun_fuse_dockerfile]