#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, make_response, jsonify
import os
import json
import werkzeug
from datetime import datetime
import wave
from vosk import Model, KaldiRecognizer, SetLogLevel

# flask
app = Flask(__name__)

# ★ポイント1
# limit upload file size : 128 MB
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False

model = Model("model")
rec = KaldiRecognizer(model, 44100)
rec.SetWords(True)
rec.SetPartialWords(True)

# ★ポイント2
# ex) set UPLOAD_DIR_PATH=C:/tmp/flaskUploadDir
# UPLOAD_DIR = os.getenv("UPLOAD_DIR_PATH")

# rest api : request.files with multipart/form-data
# <form action="/data/upload" method="post" enctype="multipart/form-data">
#   <input type="file" name="uploadFile"/>
#   <input type="submit" value="submit"/>
# </form>
@app.route('/upload', methods=['POST'])
def upload_multipart():

    # ★ポイント3
    if 'uploadFile' not in request.files:
        make_response(jsonify({'result':'uploadFile is required.'}))

    file = request.files['uploadFile']
    fileName = file.filename
    if '' == fileName:
        make_response(jsonify({'result':'filename must not empty.'}))

    # ★ポイント4
    # saveFileName = datetime.now().strftime("%Y%m%d_%H%M%S_") \
    #     + werkzeug.utils.secure_filename(fileName)
    # file.save(os.path.join(UPLOAD_DIR, saveFileName))

    wf = wave.open(file, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        return  jsonify({'error': "Audio file must be WAV format mono PCM."})

    data = wf.readframes(-1)
    rec.AcceptWaveform(data)
    return make_response(jsonify(json.loads(rec.Result())))

# ★ポイント5
@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return 'result : file size is overed.'

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)