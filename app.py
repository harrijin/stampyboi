import os, re
from flask import Flask, send_file, request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import deepspeech
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor
from .transcribers.file import FileExtractor
from urllib.request import urlopen
import urllib.parse
import json
from pathlib import Path
from enum import Enum
import pysolr


UPLOAD_FOLDER = './transcribers/uploadedFiles'
ALLOWED_EXTENSIONS = {'wav', 'ogv', 'mp4', 'mpeg', 'avi', 'mov'}
MODEL = deepspeech.Model('./transcribers/deepspeech-0.7.4-models.pbmm')
MODEL.enableExternalScorer('./transcribers/deepspeech-0.7.4-models.scorer')

SOLR_COLLECTION = 'stampyboi'
SOLR_HOST_DIR = '/Documents'

MAX_SUGGESTIONS = 7 # maximum number of videos to return for suggestions
SUGGESTION_REGEX = '(?:<b>)(.+?)(?:[\s.,:;!?])'

# Getting ip address of solr host from ~/Documents/solrhost.txt

WORKING_DIRECTORY = os.getcwd()
HOME = str(Path.home())
os.chdir(HOME + SOLR_HOST_DIR)
file = open("solrhost.txt", "r")
SOLR_HOST = str(file.read())
os.chdir(WORKING_DIRECTORY)

solr = pysolr.Solr('http://'+SOLR_HOST+'/solr/'+SOLR_COLLECTION)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            videoID = ytVidId(source)
            if videoID: # Check if provided link is valid
                results = search_solr(quote,'yt',videoID)
                if results == '[][][][]': # Check if solr found the video id in the index. 8 is the length of [][][][]
                    print('video not found. transcribing and indexing')
                    transcriber = YouTube(videoID)
                    transcript = transcriber.getTranscript()
                    if not isinstance(transcript, str): # Check if getTranscript returned an error message
                        try:
                            transcriptJSON = transcriber.getJSON()
                            solr.add(transcriptJSON, commit=True)
                            results = search_solr(quote,'yt',videoID)
                        except:
                            print("solr server is down")
                            # Add search function used for file uploads here

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
        if len(title) > 0: #and int(szn) > 0 and int(ep) > 0:
            videoID = title + "^!" + szn + "_"+ep
            results = search_solr(quote,'flix',videoID)
            if results == '[][][][]': # Check if solr found the video id in the index
                if szn != '' and ep != '':
                    print('video not found. transcribing and indexing')
                    try:
                        transcriber = FlixExtractor(title, int(szn), int(ep))
                        # results = "Title: " + title + "<br>Season #: " + szn + "<br>Episode #: " + ep + "<br>Results: <br>" + str(transcriber.getTranscript())
                        # transcriber.convertToJSON("jsonTranscripts/transcript.json")
                        transcriptJSON = transcriber.getJSON()
                        solr.add(transcriptJSON, commit=True)
                        results = search_solr(quote,'flix',videoID)
                    except(ValueError):
                        results = "ERROR: Netflix show " + title + " not found"
                    except IndexError as e:
                        results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found. " + str(e)
        else:
            results = search_solr(quote,'flix')

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
            results = "Quote: " + quote + "<br>File: " + filename + "<br>Results: <br>" + str(transcriber.getTranscript())
            os.remove(audioPath)

        else:
            results = 'ERROR: incorrect file format'

    else:
        results = "ERROR: Invalid searchsearch_src"

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

# ==============Helper Methods==============

def stringToTimestamps(script):
    result = []
    for index, phrase in enumerate(script.split()):
        if '<em>' in phrase:
            result.append(index)
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

def search_solr(quote, source='none', id=''):
    quote = '"'+quote.replace(" ", "+")+'"'
    connectionURL = 'http://'+ SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/select?q=script:' + quote + '&hl=on&hl.fl=script&hl.method=unified&omitHeader=true&hl.fragsize=0&hl.usePhraseHighlighter=true'
    # ===============Database Search===============
    if source == 'yt':
        connectionURL = connectionURL + '&fq=%2Btype:yt'
        if len(id) > 0:
            connectionURL = connectionURL + '%20%2Bid:' + id
    elif source == 'flix':
        connectionURL = connectionURL + '&fq=%2Btype:flix'
        if len(id) > 0:
            all_info = re.compile('^(.+?)\^!(\d{1,2})_(\d{1,3})$')
            if all_info.match(id):
                connectionURL = connectionURL + '%20%2Bid:"' + urllib.parse.quote(id) + '"'
            else:
                no_episode = re.compile('^(.+?)\^!(\d{1,2})_$')
                match = no_episode.match(id)
                if match:
                    title = match.group(1)
                    szn = match.group(2)
                else:# only info provided is the show name
                    title = id[:-3]
                connectionURL = connectionURL +'%20%2Btitle:'+title
            #connectionURL = connectionURL + '&fq=%2Btitle%3A"' + title.replace(" ", "+") + '"' + '%2Btype%3Aflix'
    try:
        print(connectionURL)
        connection = urlopen(connectionURL)
        response = json.load(connection)
    except:
        return "Sorry, the search server is currently down."
    resultIDs = []
    resultTypes = []
    resultScripts = []
    results = ""
    resultTimestamps=[]
    search_netflix_season = 'szn' in locals() # Check if results should be filtered by season
    for document in response['response']['docs']:
        docID = document['id']
        if search_netflix_season:
            match = all_info.match(docID)
            docSzn = match.group(2)
            if docSzn != szn:
                continue
        resultIDs.append(docID)
        resultTypes.append(document['type'])
        times = document['times']
        hilitedScript=response['highlighting'][resultIDs[-1]]['script'][0]
        resultScripts.append(hilitedScript)
        timestampIndices=stringToTimestamps(hilitedScript)
        docTimestamps=[]
        for index in timestampIndices:
            docTimestamps.append(times[index])
        resultTimestamps.append(docTimestamps)
    results = str(resultIDs) + str(resultTypes) + str(resultTimestamps) + str(resultScripts)
    return results