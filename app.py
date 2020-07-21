import os, re
from flask import Flask, send_file, request, flash, redirect, url_for, render_template, Markup, session
from werkzeug.utils import secure_filename
import deepspeech
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor
from .transcribers.file import FileExtractor
from urllib.request import urlopen
import json, datetime
from pathlib import Path
from enum import Enum


UPLOAD_FOLDER = './transcribers/uploadedFiles'
ALLOWED_EXTENSIONS = {'wav', 'ogv', 'mp4', 'mpeg', 'avi', 'mov'}
MODEL = deepspeech.Model('./transcribers/deepspeech-0.7.4-models.pbmm')
MODEL.enableExternalScorer('./transcribers/deepspeech-0.7.4-models.scorer')

SOLR_COLLECTION = 'stampyboi'
SOLR_HOST_DIR = '/Documents'

MAX_SUGGESTIONS = 7 # maximum number of videos to return for suggestions
SUGGESTION_REGEX = '(?:<b>)(.+?)(?:[\s.,:;!?])'

WORDS_OF_CONTEXT = 2 # the number of words on either side of the target to return as context

# Getting ip address of solr host from ~/Documents/solrhost.txt

WORKING_DIRECTORY = os.getcwd()
HOME = str(Path.home())
os.chdir(HOME + SOLR_HOST_DIR)
file = open("solrhost.txt", "r")
SOLR_HOST = str(file.read())
os.chdir(WORKING_DIRECTORY)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'\xee\xe7\x0e\xe8\x1c\x87x%\xc3\x95\xfd\xb1wI\x96\x97' # MUST CHANGE IF APP IS DEPLOYED

# ===========Index pages===========

@app.route('/', methods=['GET'])
def render_index():
    return render_template('searchPage.html')

@app.route('/results', methods=['POST'])
def render_results():
    quote = request.form['quote']
    # ===============Database Search===============
    if request.form['search_src'] == 'none':
        results = search_solr(quote)
    # =============YouTube=============
    elif request.form['search_src'] == 'yt':
        source = request.form['yt_source']
        if len(source) > 0: # Check if a youtube link was provided
            if ytVidId(source): # Check if provided link is valid
                transcriber = YouTube(ytVidId(source))
                transcript = transcriber.getTranscript()
                if not isinstance(transcript, str): # Check if getTranscript returned an error message
                    transcript = str(transcript)
                    results = "<br>YouTube Video ID: " + ytVidId(source) + "<br>Results: <br>" + transcript
                    transcriber.convertToJSON("jsonTranscripts/transcript.json")
                else:
                    results = transcript
            else:
                results = "ERROR: Invalid YouTube link"
        else:
            results = search_solr(quote,'yt')
    # =============Netflix==============
    elif request.form['search_src'] == 'flix':
        title = request.form['flix_title']
        szn = request.form['flix_szn']
        ep = request.form['flix_ep']
        try:
            szn = int(szn)
            ep = int(ep)
            if len(title) > 0 and int(szn) > 0 and int(ep) > 0:
                try:
                    transcriber = FlixExtractor(title, int(szn), int(ep))
                    results = "Title: " + title + "<br>Season #: " + szn + "<br>Episode #: " + ep + "<br>Results: <br>" + str(transcriber.getTranscript())
                    transcriber.convertToJSON("jsonTranscripts/transcript.json")
                except(ValueError):
                    results = "ERROR: Netflix show " + title + " not found"
                except(IndexError):
                    results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found"
            else:
                results = search_solr(quote,'flix', title)
        except:
            results = search_solr(quote,'flix', title)

    # ============File Upload===========
    elif request.form['search_src'] == 'file':
        # check if the post request has the file part
        if 'vid_upload' not in request.files:
            results = 'ERROR: No file part'
            return render_template("results.html", result=results)
        file = request.files['vid_upload']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            results = 'ERROR: No file selected'
            return render_template("results.html", result=results)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            audioPath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(audioPath)
            # while not os.path.exists(audioPath):
            #     pass
            transcriber = FileExtractor(audioPath, MODEL)
            transcriptList = transcriber.getTranscript()
            tupleList = findStringInTranscript(transcriptList, quote)
            if not tupleList:
                results = 'No results found.'
            else:
                results = [formatTranscriptToDictionary("file", filename, tupleList)]
            
            if os.path.exists(audioPath):
                os.remove(audioPath)

        else:
            results = 'ERROR: incorrect file format'

    else:
        results = "ERROR: Invalid searchsearch_src"

    session['results'] = results

    return render_template("results.html", result=results, query=quote)

@app.route('/suggest', methods=['POST'])
def get_suggestions():
    query = request.form['q']
    suggestionURL = 'http://'+ SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/suggest?wt=json&omitHeader=true&suggest.count=' + str(MAX_SUGGESTIONS) + '&suggest.q=' + query.replace(" ", "+")
    try:
        response = json.load(urlopen(suggestionURL))
    except:
        return str([""])
    suggestions = response['suggest']['mySuggester'][query]['suggestions']
    truncSuggestions = []
    for script in suggestions:
        results = stringToSuggestions(script["term"])
        for result in results:
            result = result.lower().replace("-"," ")
            if result not in truncSuggestions and result != query.lower():
                truncSuggestions.append(result)
                if len(truncSuggestions) >= MAX_SUGGESTIONS:
                    break
    return str(truncSuggestions)

@app.route('/spellcheck', methods=['POST'])
def check_spelling():
    query = '"' + request.form['q'] + '"'
    spellcheckURL = 'http://' + SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/spell?wt=json&omitHeader=true&q=script:'+query.replace(' ', '+')
    try:
        response = json.load(urlopen(spellcheckURL))
    except:
        return str([""])
    suggestions = response['spellcheck']['collations'][1::2]
    return str(suggestions).replace('"','')

@app.route('/receive-video', methods=['POST'])
def receive_video():
    id, start = None, None
    if 'results' in session and not isinstance(session['results'], str):
        stamps = []
        doc = session['results'][int(request.form['doc'])]  # Get the doc result that the user wants to go to
        id = doc['id']
        for item in doc['list']:
            text = item[0]
            sec = int(item[1])
            time = str(datetime.timedelta(seconds=sec))
            stamps.append({'text':text, 'sec':sec, 'time':time})
        stampIndex = int(request.form['stamp'])
        start = stamps[stampIndex]['sec']
    else:
        stamps = "ERROR: No video loaded."

    session['stamps'] = stamps
    session['start'] = start
    session['id'] = id

    return redirect(url_for('render_video'))

@app.route('/video')
def render_video():
    if all(x in session for x in ['stamps', 'start', 'id']):
        stamps = session['stamps']
        start = session['start']
        id = session['id']
    else:
        stamps = "ERROR: No video loaded."
        start, id = None, None
    return render_template("video.html", stamps=stamps, start=start, id=id)

# ==============Helper Methods==============

def extractHighlights(script, times):
    result = []
    script_list = script.split()
    for index, phrase in enumerate(script_list):
        begin = phrase.rfind('<em>')
        if begin != -1:
            end = phrase.rfind('</em>')
            if end < begin:
                buildPhrase = []
                for i in range(index + 1, len(script_list)):
                    buildPhrase.append((re.sub('-', ' ', phrase)))
                    if ('</em>' in script_list[i]):
                        break
                result.append((Markup(' '.join(buildPhrase)), times[index]))
            else:
                result.append((Markup(re.sub('-', ' ', phrase)), times[index]))
    return result

def stringToSuggestions(script):
    suggestions = re.findall(SUGGESTION_REGEX, script)
    result = [suggestion.replace("<b>","").replace("</b>","") for suggestion in suggestions]
    return result # returns a list of strings to use as suggestions

class Source(Enum):
    YOUTUBE = 1
    NETFLIX = 2
    UPLOAD = 3
    OTHER = 4

def sourceFromURL(url):
    if "netflix.com" in url:
         return Source.NETFLIX
    if "youtube.com" in url or "youtu.be" in url:
        return Source.YOUTUBE
    return Source.OTHER

def ytVidId(url):
    ytRegEx = re.compile('(?:/|%3D|v=|vi=)([0-9A-z-_]{11})(?:[%#?&]|$)')
    valid = ytRegEx.search(url)
    if valid:
        return valid.group(1)
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def search_solr(quote, source='none', title=''):
    quote = '"'+quote.replace(" ", "+")+'"'
    connectionURL = 'http://'+ SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/select?q=script:' + quote + '&hl=on&hl.fl=script&hl.method=unified&omitHeader=true&hl.fragsize=0&hl.usePhraseHighlighter=true'
    # ===============Database Search===============
    if source == 'yt':
        connectionURL = connectionURL + '&fq=type:yt'
    elif source == 'flix':
        if len(title) > 0:
            connectionURL = connectionURL + '&fq=%2Btitle%3A"' + title.replace(" ", "+") + '"' + '%2Btype%3Aflix'
        else:
            connectionURL = connectionURL + '&fq=type:flix'
    try:
        connection = urlopen(connectionURL)
        response = json.load(connection)
    except:
        return "Sorry, the search server is currently down."
    
    results = []

    for document in response['response']['docs']:
        highlightedScript = response['highlighting'][document['id']]['script'][0]
        highlights = extractHighlights(highlightedScript, document['times'])
        videoInfo = formatTranscriptToDictionary(document['type'], document['id'], highlights)
        results.append(videoInfo)

    if not results:
        return 'No results found.'

    return results

def findStringInTranscript(transcriptList, targetString):
    targetStringSplit = targetString.split()
    firstWord = targetStringSplit[0]
    targetTuples = []
    x = 0
    while x < len(transcriptList):
        if (transcriptList[x])[0] == firstWord:
            y = 1
            equal = True
            while y < len(targetString.split()) and x + y < len(transcriptList):
                if (transcriptList[x + y])[0] != targetStringSplit[y]:
                    equal = False
                y += 1
            if equal:
                z = 1
                resultString = targetString
                while z <= WORDS_OF_CONTEXT:
                    if x - z >= 0:
                        resultString = (transcriptList[x - z])[0] + " "  + resultString
                    if x + len(targetStringSplit) + z - 1 < len(transcriptList):
                        resultString = resultString + " " + (transcriptList[x + len(targetStringSplit) + z - 1])[0]
                    z += 1
                targetTuples.append((resultString, (transcriptList[x])[1]))
        x += 1
    #targetTuples = list(filter(lambda x:firstWord in x, transcriptList))
    return targetTuples

def formatTranscriptToDictionary(type, id, tupleList):
    resultDict = {"type": type, "id": id, "list": tupleList}
    return resultDict