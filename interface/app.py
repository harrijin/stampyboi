from flask import Flask, send_file, request
from transcribers.youtube import YouTube
from transcribers.flix import FlixExtractor

app = Flask(__name__)

@app.route('/', methods=['GET'])
def render_index():
  return(send_file("interface.html"))

@app.route('/results', methods=['POST'])
def return_results():
  quote = request.args['quote']
  if request.args['src'] == 'yt':
    source = request.args['source']
    transcriber = YouTube(source)
    results = str(transcriber.getTranscript())
  elif request.args['src'] == 'flix':
    title = request.args['title']
    szn = request.args['szn']
    ep = request.args['ep']
    transcriber = FlixExtractor(title, int(szn), int(ep))
    results = str(transcriber.getTranscript())
  else:
    results = "Error: Invalid searchSrc"

  return results