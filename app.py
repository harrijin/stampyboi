from flask import Flask, send_file, request
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor

app = Flask(__name__)

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
      results = "ERROR: Netflix show " + title + "not found"
    except(IndexError):
      results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found"
  else:
    results = "ERROR: Invalid searchSrc"

  return results