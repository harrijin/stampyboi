from flask import Flask, send_file, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def render_index():
  return(send_file("interface.html"))

@app.route('/results', methods=['POST'])
def return_results():
  quote = request.args['quote']
  if request.args['src'] == 'yt':
    source = request.args['source']
    # Create an instance of YouTube here
    results = "Quote: " + quote + " Source: " + source + " Results: " 
  elif request.args['src'] == 'flix':
    title = request.args['title']
    szn = request.args['szn']
    ep = request.args['ep']
    # Create an instance of FlixExtractor here
    results = "Quote: " + quote + " Show: " + title + " Season: " + szn + " Episode: " + ep + " Results: "
  else:
    results = "Error: Invalid searchSrc"

  return results