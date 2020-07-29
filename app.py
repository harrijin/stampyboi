import os, re, ast
from flask import Flask, send_file, request, flash, redirect, url_for, render_template, Markup, session
from werkzeug.utils import secure_filename
import deepspeech
from .transcribers.youtube import YouTube
from .transcribers.flix import FlixExtractor
from .transcribers.file import FileExtractor
from . import secret
from urllib.request import urlopen
import json, datetime, urllib.parse
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

WORDS_OF_CONTEXT = 2 # the number of words on either side of the target to return as context

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
app.secret_key = secret.app_key # MUST CHANGE IF APP IS DEPLOYED

# ===========Index pages===========

@app.route('/', methods=['GET'])
def render_index():
    return render_template('searchPage.html')

@app.route('/results', methods=['POST'])
def render_results():
    # ENABLE IF TESTING WITHOUT SEARCH ENGINE *****************************************************************
    DUMMY = False
    if DUMMY:
        longList = [
            ('quote at 123 sec', 123),
            ('quote at 234 sec', 234),
            ('quote at 345 sec', 345),
            ('quote at 456 sec, this one is really long and might have to go to the next line re9g8gheruhiadfjnhgfnjdfgdsfgdsfg aaaa aaaaaaaa aaaaaaaaaa aaaaaa aaaaa', 456),
            ('quote at 567 sec', 567),
            ('quote at 678 sec', 678),
            ('quote at 789 sec', 789),
            ('quote at 890 sec', 890),
            ('quote at 900 sec', 900),
            ('quote at 1001 sec', 1001),
        ]
        results = [
            {"type": "yt", "id": 'bS5P_LAqiVg', 'list':longList},
            {"type": "yt", "id": 'eJ-T3i8Ap3U', 'list':[('quote one at 2 sec', 2),('quote two at 69', 69)]},
            {"type": "yt", "id": 'rtgY1q0J_TQ', 'list':[('quote one at 4 sec', 4),('quote two at 42', 42)]},
        ]
        results[0].update(getYouTubeInfo('bS5P_LAqiVg'))
        results[1].update(getYouTubeInfo('eJ-T3i8Ap3U'))
        results[2].update(getYouTubeInfo('rtgY1q0J_TQ'))

        return render_template("results.html", result=results, query=request.form['quote'])
    # END OF DUMMY TEST*****************************************************************************************

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
                if results == 'No results found.': # Check if solr found the video id in the index. 8 is the length of [][][][]
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
        if len(title) > 0:
            videoID = title + "^!" + szn + "_"+ep
            results = search_solr(quote,'flix',videoID)
            if results == 'No results found.': # Check if solr found the video id in the index
                if szn != '' and ep != '': # Check if season and episode are provided
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
                    return str(truncSuggestions)
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

@app.route('/video', methods=['POST'])
def receive_video():
    doc = request.json
    for item in doc['list']:
        text = item[0]
        item[0] = Markup(text)
    stamp = int(doc.pop('index'))

    return render_template("video.html", doc=doc, stamp=stamp)

@app.context_processor
def utility():
    def time_string(sec):
        delta = datetime.timedelta(seconds=sec)
        stamp = (datetime.datetime.min + delta).time()
        return stamp.strftime('%H:%M:%S')
    return dict(time_string=time_string)

# ==============Helper Methods==============

def extractHighlights(script, times):
    result = []
    script_list = script.split()
    for index, phrase in enumerate(script_list):
        begin = phrase.rfind('<b>')
        if begin != -1:
            end = phrase.rfind('</b>')
            if end < begin:
                buildPhrase = []
                for i in range(index + 1, len(script_list)):
                    buildPhrase.append((re.sub('-', ' ', phrase)))
                    if ('</b>' in script_list[i]):
                        break
                result.append((Markup(' '.join(buildPhrase)), int(times[index])))
            else:
                result.append((Markup(re.sub('-', ' ', phrase)), int(times[index])))
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
    connectionURL = 'http://'+ SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/select?q=script:' + quote + '&hl=on&hl.fl=script&hl.method=unified&omitHeader=true&hl.fragsize=0&hl.usePhraseHighlighter=true&hl.tag.pre=<b>&hl.tag.post=</b>'
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

    results = []
    search_netflix_season = 'szn' in locals() # Check if results should be filtered by season

    for document in response['response']['docs']:
        docID = document['id']
        if search_netflix_season:
            match = all_info.match(docID)
            docSzn = match.group(2)
            if docSzn != szn:
                continue
        highlightedScript = response['highlighting'][docID]['script'][0]
        highlights = extractHighlights(highlightedScript, document['times'])
        videoInfo = formatTranscriptToDictionary(document['type'], docID, highlights)
        if document['type'] == 'yt':
            ytInfo = getYouTubeInfo(docID)
            if ytInfo:
                videoInfo.update(ytInfo)
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

def getYouTubeInfo(id):
    with urlopen('https://www.googleapis.com/youtube/v3/videos?part=snippet&id=' + id + '&key=' + secret.yt_key) as response:
        data = json.loads(response.read().decode())
        info = data['items'][0]['snippet']
        title = info['title']
        channel = info['channelTitle']
        date = info['publishedAt']
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').strftime('%b %-d, %Y')
        thumb = info['thumbnails']['medium']['url']
    if title and channel and date and thumb:
        return {'title': title, 'channel': channel, 'date': date, 'thumb': thumb}