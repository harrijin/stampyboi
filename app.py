import os
from flask import Flask, send_file, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor

UPLOAD_FOLDER = '/deepspeech/uploadedFiles'
ALLOWED_EXTENSIONS = {'wav'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def render_index():
    return(send_file("interface.html"))

@app.route('/results', methods=['POST'])
def return_results():
    quote = request.args['quote']
    if request.args['src'] == 'yt':
        source = request.args['source'] # source is now a youtube video ID
        transcriber = YouTube(source)
        results = "Quote: " + quote + "<br>YouTube Video ID: " + source + "<br>Results: <br>" + str(transcriber.getTranscript())
    elif request.args['src'] == 'flix':
        title = request.args['title']
        szn = request.args['szn']
        ep = request.args['ep']
        try:
            transcriber = FlixExtractor(title, int(szn), int(ep))
            results = "Title: " + title + "<br>Season #: " + szn + "<br>Episode #: " + ep + "<br>Results: <br>" + str(transcriber.getTranscript())
        except(ValueError):
            results = "ERROR: Netflix show " + title + " not found"
        except(IndexError):
            results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found"
    elif request.args['src'] == 'file':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No file selected' 
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            results = 'successful file upload'
        else:
            return 'Invalid file format'
    else:
        results = "ERROR: Invalid searchSrc"

    return results
