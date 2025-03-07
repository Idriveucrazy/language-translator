import os
from flask import Flask, request, render_template, send_file
from deep_translator import GoogleTranslator
import speech_recognition as sr
from gtts import gTTS
import uuid

app = Flask(__name__)

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    "english": "en",
    "french": "fr",
    "hindi": "hi",
    "spanish": "es",
    "german": "de",
    "italian": "it"
    # Add more as needed
}


def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data)


def translate_text(text, target_language_code):
    return GoogleTranslator(source='auto', target=target_language_code).translate(text)


def text_to_speech(text, language_code):
    tts = gTTS(text=text, lang=language_code)
    output_audio_path = f"static/output_{uuid.uuid4()}.mp3"
    tts.save(output_audio_path)
    return output_audio_path


@app.route('/')
def index():
    return render_template('index.html', languages=SUPPORTED_LANGUAGES.keys())


@app.route('/translate', methods=['POST'])
def translate_audio():
    if 'audio' not in request.files or request.files['audio'].filename == '':
        return "Error: No audio file uploaded."

    target_language_name = request.form.get('language').lower()
    target_language_code = SUPPORTED_LANGUAGES.get(target_language_name)

    if target_language_code is None:
        return f"Error: Language '{target_language_name}' is not supported. Supported languages: {list(SUPPORTED_LANGUAGES.keys())}"

    audio_file = request.files['audio']
    audio_path = f"static/input_{uuid.uuid4()}.wav"
    audio_file.save(audio_path)

    try:
        transcribed_text = transcribe_audio(audio_path)
    except Exception as e:
        os.remove(audio_path)
        return f"Error during transcription: {e}"

    try:
        translated_text = translate_text(transcribed_text, target_language_code)
    except Exception as e:
        os.remove(audio_path)
        return f"Error during translation: {e}"

    try:
        output_audio_path = text_to_speech(translated_text, target_language_code)
    except Exception as e:
        os.remove(audio_path)
        return f"Error during text-to-speech: {e}"

    os.remove(audio_path)

    return render_template('result.html', transcribed_text=transcribed_text, translated_text=translated_text, output_audio=output_audio_path)


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f"static/{filename}", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
