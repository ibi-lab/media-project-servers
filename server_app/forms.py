#!/usr/bin/env python

from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename

import werkzeug
from google.cloud import texttospeech


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
    input_type = SelectField(
        u'Input Type',
        validators=[Optional()],
        choices=[(1, 'text'), (2, 'ssml')],
        default=1
    )
    submit = SubmitField('Convert Text to Speech')


class SpeechToTextForm(FlaskForm):
    """
    Create user form for submitting text for speech synthesis
    """
    speech = FileField(validators=[FileRequired()])
    engine = SelectField(
        u'Speech Recognition Engine',
        choices=[(1, 'julius'), (2, 'kaldi'), (3, 'gcp')]
    )
    submit = SubmitField('Convert Speech to Text')


class STTYomiForm(FlaskForm):
    """
    """
    id_field = StringField(u'学籍番号', validators=[DataRequired()])
    text_field = TextAreaField(u'読み', validators=[DataRequired()])
    submit = SubmitField('読みファイルの作成')


class STTVocaForm(FlaskForm):
    """
    """
    id_field = StringField(u'学籍番号', validators=[DataRequired()])
    text_field = TextAreaField(u'ボキャブラリー', validators=[DataRequired()])
    submit = SubmitField('ボキャブラリーファイルの作成')


class STTPhoneForm(FlaskForm):
    """
    """
    id_field = StringField(u'学籍番号', validators=[DataRequired()])
    text_field = TextAreaField(u'音素', validators=[DataRequired()])
    submit = SubmitField('音素ファイルの作成')


class STTPGrammerForm(FlaskForm):
    """
    """
    id_field = StringField(u'学籍番号', validators=[DataRequired()])
    text_field = TextAreaField(u'構文', validators=[DataRequired()])
    submit = SubmitField('構文ファイルの作成')
