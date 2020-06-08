from flask import Flask, send_file, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def render_index():
    return(send_file("interface.html"))

@app.route('/results', methods=['POST'])
def return_results():
    quote = request.args['quote']
    source = request.args['source']
    results = "Quote: " + quote + " Source: " + source + " Results: " 
    return results
