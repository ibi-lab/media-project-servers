#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import wave
import traceback

from flask import Flask, request, make_response, jsonify, \
    render_template, flash, redirect, send_file, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional
import werkzeug
from vosk import Model, KaldiRecognizer, SetLogLevel
from google.cloud import texttospeech

# flask
app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = ''
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

###
### モデルは各国の言語モデルが以下に公開されている
###
### https://alphacephei.com/vosk/models
###
### 現在、使っているのは、日本語のスモールサイズモデル
###
### * vosk-model-small-ja-0.22 48M
###
### Cloud Run実行時に読み込まれるが、この読み込みは毎回の実行時ではなく、
### 少なくともしばらくは読み込み済みで実行してくれるため、オーバーヘッドに
### 含まれない（おそらく、Preemptibleオブジェクトが入れ替わるときに
### 再読み込みされている）
###
model = Model("model")

### 対象の音声は44.1kHzのサンプリングレートのみ
rec = KaldiRecognizer(model, 44100)
rec.SetWords(True)
rec.SetPartialWords(True)

@app.route('/sst', methods=['POST'])
def upload_multipart():

    if 'uploadFile' not in request.files:
        make_response(jsonify({'error':'uploadFile is required.'}))

    file = request.files['uploadFile']
    fileName = file.filename
    if '' == fileName:
        make_response(jsonify({'error':'filename must not empty.'}))

    wf = wave.open(file, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        return  jsonify({'error': "Audio file must be WAV format mono PCM."})

    ### あまり大きなファイルは想定していないので、全部を読み込む
    data = wf.readframes(-1)
    rec.AcceptWaveform(data)
    return make_response(jsonify(json.loads(rec.Result())))

@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return 'error : file size is overed.'


@app.route('/tts', methods=['GET', 'POST'])
def text_to_speech_form():
    """
    Route to display home page and form to receive text from user for speech synthesis.
    """
    try:
        form = TextToSpeechForm()

        # Instantiates a client
        client = texttospeech.TextToSpeechClient()

        # Get the language list
        voices = client.list_voices()
        voice_codes_list = list(dict.fromkeys([voice.language_codes[0] for voice in voices.voices]))
        language_list = [(ind + 1, voice) for ind, voice in enumerate(voice_codes_list)]

        if request.method == 'POST':
            lang = dict(language_list).get(int(form.language_options.data))
            gender = dict([(1, texttospeech.enums.SsmlVoiceGender.MALE),
                        (2, texttospeech.enums.SsmlVoiceGender.FEMALE)]).get(int(form.gender_options.data))
            messages = json.dumps({'text': form.text_field.data,
                                'language': lang,
                                'gender': gender})
            return redirect(url_for('.translate', messages=messages))
        return render_template('main.html', form=form)
    except:
        return jsonify({'error': traceback.format_exc()})


@app.route('/tts/translate')
def text_to_speech():
    """
    Route to synthesize speech using Google Text-to-Speech API.
    """

    # Get requested text
    messages = json.loads(request.args['messages'])

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=messages['text'])

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.types.VoiceSelectionParams(
        language_code=messages['language'],
        ssml_gender=messages['gender'])

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary.
    with open('./static/output.mp3', 'wb') as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

    return send_file('./static/output.mp3', attachment_filename='output.mp3')


class TextToSpeechForm(FlaskForm):
    """
    Create user form for submitting text for speech synthesis
    """
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Performs the list voices request
    voices = client.list_voices()

    # Get language list
    voice_codes_list = list(dict.fromkeys([voice.language_codes[0] for voice in voices.voices]))
    language_list = [(ind + 1, voice) for ind, voice in enumerate(voice_codes_list)]

    # Get voice gender
    voice_gender = [(1, "Male"), (2, "Female")]

    text_field = TextAreaField('Input Text', validators=[DataRequired()])
    language_options = SelectField(u'Input Language', validators=[Optional()],
                                choices=language_list, default=12)
    gender_options = SelectField(u'Voice Gender', validators=[Optional()],
                                choices=voice_gender, default=1)
    submit = SubmitField('Convert Text to Speech')

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)