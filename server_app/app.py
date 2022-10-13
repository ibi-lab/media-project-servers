#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import wave
import traceback
import logging
from io import BytesIO

import platform

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
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename

import werkzeug
from vosk import Model, KaldiRecognizer, SetLogLevel
from google.cloud import texttospeech
import pexpect


# flask
app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'M3d1APr0j3cT'
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


@app.route('/stt', methods=['GET', 'POST'])
def speech_to_text_with_julius():
    try:
        form = SpeechToTextForm()
        if form.validate_on_submit():
            f = form.speech.data
            fileName = secure_filename(f.filename)
            filepath = os.path.join(
                app.instance_path, 'voices', fileName
            )
            if not os.path.exists(filepath):
                os.makedirs(os.path.dirname(filepath))
            f.save(filepath)
            logging.error(filepath)
            if '' == fileName:
                make_response(jsonify({'error':'filename must not empty.'}))

            julius = Julius()
            return make_response(jsonify(julius.speech_to_text(filepath)))
        return render_template('stt.html', form=form)
    except:
        return jsonify({'error': traceback.format_exc()})



@app.route('/stt/vosk', methods=['GET', 'POST'])
def speech_to_text_with_vosk():
    try:
        form = SpeechToTextForm()
        if form.validate_on_submit():
            f = form.speech.data
            fileName = secure_filename(f.filename)
            if '' == fileName:
                make_response(jsonify({'error':'filename must not empty.'}))

            wf = wave.open(f, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                return  jsonify({'error': "Audio file must be WAV format mono PCM."})

            ### あまり大きなファイルは想定していないので、全部を読み込む
            data = wf.readframes(-1)
            rec.AcceptWaveform(data)
            return make_response(jsonify(json.loads(rec.Result())))
        return render_template_string(stt_html_template, form=form)
    except:
        return jsonify({'error': traceback.format_exc()})


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

        if request.method == 'POST':
            return redirect(
                url_for(
                    '.text_to_speech', 
                    text=form.text_field.data, 
                    language=form.language_options.data, 
                    gender=form.gender_options.data
                )
            )
        return render_template('tts.html', form=form)
    except:
        return jsonify({'error': traceback.format_exc()})


@app.route('/tts/convert')
def text_to_speech():
    """
    Route to synthesize speech using Google Text-to-Speech API.
    """

    # Get requested text
    # messages = json.loads(request.args['messages'])
    if not 'text' in request.args \
        or not 'language' in request.args \
            or not 'gender' in request.args:
        return jsonify({
            'error': 'invalid arguments. text, language, gender should be specified.'
        })
    
    text = request.args['text']
    language = request.args['language']
    gender = request.args['gender']

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Get the language list
    voices = client.list_voices()
    voice_codes_list = list(dict.fromkeys([voice.language_codes[0] for voice in voices.voices]))
    language_list = [(ind + 1, voice) for ind, voice in enumerate(voice_codes_list)]

    lang_ = dict(language_list).get(int(language))
    gender_ = dict(
        [(1, texttospeech.SsmlVoiceGender.MALE), (2, texttospeech.SsmlVoiceGender.FEMALE)]
    ).get(int(gender))

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_,
        ssml_gender=gender_
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


class SpeechToTextForm(FlaskForm):
    """
    Create user form for submitting text for speech synthesis
    """
    speech = FileField(validators=[FileRequired()])

    submit = SubmitField('Convert Speech to Text')


class Julius(object):
    def __init__(
        self,
        julius_path='/usr/local/bin/julius',
        main_conf='/usr/local/dictation-kit/main.jconf',
        grammer_conf='/usr/local/dictation-kit/am-gmm.jconf'
    ):
        self.sh = pexpect.spawn(
            '%s -C %s -C %s -nostrip -input rawfile' % (
                julius_path, main_conf, grammer_conf
            )
        )
    
    def __del__(self):
        self.sh.close()

    def speech_to_text(self, wavefile_path):
        try:
            if not os.path.exists(wavefile_path):
                raise Exception('wave file not exists')
            logging.error('entering filename')
            self.sh.expect('enter filename->')
            self.sh.sendline(wavefile_path)
            logging.error('filename entered')
            self.sh.expect('pass1_best: ')
            self.sh.expect('pass1_best_wordseq: ')
            pass1_sentence = self.sh.before.decode(encoding='utf-8').strip()
            logging.error('get passphases')
            self.sh.expect('pass1_best_phonemeseq: ')
            pass1_wordseq = self.sh.before.decode(encoding='utf-8').strip()
            self.sh.expect('pass1_best_score: ')
            pass1_phonemeseq = self.sh.before.decode(encoding='utf-8').strip()
            self.sh.expect('###')
            pass1_score = float(self.sh.before)
            return {
                'sentence': pass1_sentence,
                'wordseq': pass1_wordseq,
                'phonemeseq': pass1_phonemeseq,
                'score': pass1_score
            }
        except:
            logging.error(traceback.format_exc())
            return {}

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)