#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import wave
import traceback
from io import BytesIO

from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
from flask import render_template
from flask import render_template_string

from flask import flash
from flask import redirect
from flask import send_file
from flask import url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional
import werkzeug
from vosk import Model, KaldiRecognizer, SetLogLevel
from google.cloud import texttospeech

html_template = '''
{% extends 'bootstrap/base.html' %}
{% import 'bootstrap/wtf.html' as wtf %}
{% block title %}Text to Speech Application{% endblock %}

{% block content %}

    <style>
        .label-txt {
            font-size: 22px;
            font-weight: bold;
            color: #4285f4;
        }

        .lang-label {
            font-size: 16px;
            font-weight: bold;
            color: #0f9d58;
            padding-right: 5px;
        }

        img {
            padding: 0;
            display: block;
            margin: 0 auto;
            max-height: 80%;
            max-width: 80%;
        }
    </style>

    <div class="container">
        <h1 style="text-align: center;">
            <span style="color: #0f9d58;">Text to Speech<br /></span>
            </span>
        </h1>

        <div class="row">
            <div class="col-md-16">
                <form action="" method="post" novalidate>
                    {{ form.hidden_tag() }}
                    <div class="form-group">
                        <br><br>
                        {{ form.text_field.label(class_='label-txt') }}<br>
                        {{ form.text_field(rows=10, cols=180, class_='form-control') }}<br>
                        {{ form.language_options.label(class_='lang-label') }} {{ form.language_options(formnovalidate=True) }}<br>
                        {{ form.gender_options.label(class_='lang-label') }} {{ form.gender_options(formnovalidate=True) }}
                    </div>
                    {{ form.submit(class_='btn btn-default') }}
                </form>
            </div>
        </div>
    </div>>
{% endblock %}
'''

# flask
app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'bendeghe-ekiem'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'media-project-credential.json'

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
model = Model("vosk-model-small-ja-0.22")

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
            gender = dict(
                [(1, texttospeech.SsmlVoiceGender.MALE), (2, texttospeech.SsmlVoiceGender.FEMALE)]
            ).get(int(form.gender_options.data))
            messages = json.dumps(
                {
                    'text': form.text_field.data,
                    'language': lang,
                    'gender': gender
                }
            )
            return redirect(url_for('.text_to_speech', messages=messages))
        return render_template_string(html_template, form=form)
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
    synthesis_input = texttospeech.SynthesisInput(text=messages['text'])

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=messages['language'],
        ssml_gender=messages['gender']
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # The response's audio_content is binary.
    file_obj = BytesIO()
    file_obj.write(response.audio_content)
    print('Audio content written to file "output.mp3"')

    return send_file(file_obj, download_name='output.mp3')


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
    language_options = SelectField(
        u'Input Language',
        validators=[Optional()],
        choices=language_list,
        default=9 ## ja-JP
    )
    gender_options = SelectField(
        u'Voice Gender',
        validators=[Optional()],
        choices=voice_gender,
        default=1
    )
    submit = SubmitField('Convert Text to Speech')

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)