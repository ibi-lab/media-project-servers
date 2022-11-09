#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import wave
import traceback
import logging
from io import BytesIO
import datetime
import os
from os.path import isdir, isfile, join
import signal
import tempfile

import platform
from flask import abort
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
from google.cloud import speech
from google.protobuf.json_format import MessageToJson, MessageToDict

# flask
app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'M3d1APr0j3cT'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'media-project-credential.json'

from forms import TextToSpeechForm, SpeechToTextForm, \
    STTYomiForm, STTVocaForm, STTPhoneForm, STTPGrammerForm

from backbones import Julius

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
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)
rec.SetPartialWords(True)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/stt', methods=['GET', 'POST'])
def speech_to_text():
    try:
        form = SpeechToTextForm()
        if form.validate_on_submit():
            engine = form.engine.data
            if engine == '1':
                logging.error('Julius speech to text is selected')
                f = form.speech.data
                fileName = secure_filename(f.filename)
                # filepath = os.path.join(
                #     app.instance_path, 'voices', fileName
                # )
                # if not os.path.exists(filepath):
                #     os.makedirs(os.path.dirname(filepath))
                temp = tempfile.NamedTemporaryFile()
                f.save(temp.name)
                logging.error(temp.name)
                if '' == fileName:
                    make_response(jsonify({'error':'filename must not empty.'}))

                julius = Julius()
                return make_response(jsonify(julius.speech_to_text(temp.name)))
            elif engine == '2': ## Mode Kaldi
                logging.error('Kaldi speech to text is selected')
                f = form.speech.data
                fileName = secure_filename(f.filename)
                if '' == fileName:
                    make_response(jsonify({'error':'filename must not empty.'}))

                wf = wave.open(f, "rb")
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    return  jsonify({'error': "Audio file must be WAV format mono PCM."})
                data = wf.readframes(-1)
                # new_rate = 44100
                # data = 
                rec.AcceptWaveform(data)
                return make_response(jsonify(json.loads(rec.Result())))
            elif engine == '3':
                logging.error('gcp speech to text is selected')
                f = form.speech.data
                client = speech.SpeechClient()
                logging.error('client created')
                audio = speech.RecognitionAudio(content=f.read())
                logging.error('audio created')
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="ja-JP",
                )
                logging.error('config done and go operation')
                operation = client.long_running_recognize(config=config, audio=audio)

                # print("Waiting for operation to complete...")
                response = operation.result(timeout=90)
                for result in response.results:
                    # The first alternative is the most likely one for this portion.
                    logging.error(u"Transcript: {}".format(result.alternatives[0].transcript))
                    logging.error("Confidence: {}".format(result.alternatives[0].confidence))            
                return make_response(jsonify(MessageToDict(response._pb)))
            else:
                logging.error('no mode')
        return render_template('stt.html', form=form)
    except:
        return jsonify({'error': traceback.format_exc()}), 500


@app.route('/stt_gcloud', methods=['GET', 'POST'])
def speech_to_text_with_gcloud():
    try:
        form = SpeechToTextForm()

        if form.validate_on_submit():
            f = form.speech.data
            # fileName = secure_filename(f.filename)
            # filepath = os.path.join(
            #     app.instance_path, 'voices', fileName
            # )
            # if not os.path.exists(filepath):
            #     os.makedirs(os.path.dirname(filepath))
            # f.save(filepath)
            # logging.error(filepath)
            # if '' == fileName:
            #     make_response(jsonify({'error':'filename must not empty.'}))
            logging.error('stt form is valid')
            client = speech.SpeechClient()
            logging.error('client created')
            audio = speech.RecognitionAudio(content=f.read())
            logging.error('audio created')
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ja-JP",
            )

            logging.error('config done and go operation')
            operation = client.long_running_recognize(config=config, audio=audio)

            # print("Waiting for operation to complete...")
            response = operation.result(timeout=90)
            for result in response.results:
                # The first alternative is the most likely one for this portion.
                logging.error(u"Transcript: {}".format(result.alternatives[0].transcript))
                logging.error("Confidence: {}".format(result.alternatives[0].confidence))            
            return make_response(jsonify(MessageToDict(response._pb)))
        return render_template('stt.html', form=form)
    except:
        logging.error(traceback.format_exc())
        return jsonify({'error': traceback.format_exc()}), 500


@app.route('/stt_julius', methods=['GET', 'POST'])
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
        return jsonify({'error': traceback.format_exc()}), 500



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
        return render_template_string('stt.html', form=form)
    except:
        return jsonify({'error': traceback.format_exc()}), 500


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
                    gender=form.gender_options.data,
                    input_type=form.input_type.data
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
            or not 'gender' in request.args \
            or not 'input_type' in request.args:
        return jsonify({
            'error': 'invalid arguments. text, language, gender, input_type should be specified.'
        })
    
    text = request.args['text']
    gender = request.args['gender']
    input_type = request.args['input_type']

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Get the language list
    voices = client.list_voices()
    voice_codes_list = list(dict.fromkeys([voice.language_codes[0] for voice in voices.voices]))
    # language_list = [(ind + 1, voice) for ind, voice in enumerate(voice_codes_list)]

    # lang_ = dict(language_list).get(int(language))
    gender_ = dict(
        [(1, texttospeech.SsmlVoiceGender.MALE), (2, texttospeech.SsmlVoiceGender.FEMALE)]
    ).get(int(gender))

    # Set the text input to be synthesized
    # logging.error('input_type: %s', input_type)
    if input_type == "1":
        synthesis_input = texttospeech.SynthesisInput(text=text)
    else:
        logging.error('type ssml')
        synthesis_input = texttospeech.SynthesisInput(ssml=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code='ja-JP',
        ssml_gender=gender_
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        # audio_encoding=texttospeech.AudioEncoding.MP3
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000
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
    print('Audio content written to file "output.wav"')
    file_obj.seek(0)
    return send_file(
        file_obj, 
        as_attachment=True, 
        download_name='output.wav', 
        mimetype='audio/wav'
    )



@app.route('/gedit', methods=['GET', 'POST'])
def dict_editors():
    try:
        yomi_form = STTYomiForm(prefix='yomi_')
        voca_form = STTVocaForm(prefix='voca_')
        phone_form = STTPhoneForm(prefix='phone_')
        grammer_form = STTPGrammerForm(prefix='grammer_')

        if yomi_form.validate_on_submit() and yomi_form.submit.data:
            logging.error('yomi_form submitted.')
        elif voca_form.validate_on_submit() and voca_form.submit.data:
            logging.error('voca_form submitted.')
        elif phone_form.validate_on_submit() and phone_form.submit.data:
            logging.error('phone_form submitted.')        
        elif grammer_form.validate_on_submit() and phone_form.submit.data:
            logging.error('grammer_form submitted.')

        return render_template(
            'gedit.html', 
            yomi_form=yomi_form,
            voca_form=voca_form,
            phone_form=phone_form,
            grammer_form=grammer_form
        )
    except:
        return jsonify({'error': traceback.format_exc()})



# Set config for file system path and filename prefix
mnt_dir = os.environ.get('MNT_DIR', '/mnt/nfs/filestore')
filename = os.environ.get('FILENAME', 'test')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    """
    Redirects to the file system path to interact with file system
    Writes a new file on each request
    """
    # Redirect to mount path
    path = '/' + path
    if (not path.startswith(mnt_dir)):
        return redirect(mnt_dir)

    # Add parent mount path link
    html = '<html><body>\n'
    if (path != mnt_dir):
        html += f'<a href=\"{mnt_dir}\">{mnt_dir}</a><br/><br/>\n'
    else:
        # Write a new test file
        try:
            write_file(mnt_dir, filename)
        except Exception:
            abort(500, description='Error writing file.')

    # Return all files if path is a directory, else return the file
    if (isdir(path)):
        for file in os.listdir(path):
            full_path = join(path, file)
            if isfile(full_path):
                html += f'<a href=\"{full_path}\">{file}</a><br/>\n'
    else:
        try:
            html += read_file(path)
        except Exception:
            abort(404, description='Error retrieving file.')

    html += '</body></html>\n'
    return html


def write_file(mnt_dir, filename):
    '''Write files to a directory with date created'''
    date = datetime.datetime.utcnow()
    file_date = '{dt:%a}-{dt:%b}-{dt:%d}-{dt:%H}:{dt:%M}-{dt:%Y}'.format(dt=date)
    with open(f'{mnt_dir}/{filename}-{file_date}.txt', 'a') as f:
        f.write(f'This test file was created on {date}.')


def read_file(full_path):
    '''Read files and return contents'''
    with open(full_path, 'r') as reader:
        return reader.read()


# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True)