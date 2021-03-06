import os, re, ast, math
from flask import Flask, send_file, request, flash, redirect, url_for, render_template, Markup, session, send_from_directory
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
ALLOWED_AUDIO = ['.wav']
ALLOWED_VIDEO = ['.ogv', '.mp4', '.mpeg', '.avi', '.mov']
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

NETFLIX_ID_DIRECTORY = os.path.join(os.getcwd(), 'flixIDConverter', 'netflixIDDictionary.json')
# ===========Index pages===========

@app.route('/', methods=['GET'])
def render_index():
    return render_template('searchPage.html')

@app.route('/results', methods=['POST'])
def render_results():
    quote = request.form['quote']
    results = []
    results_info = [] # Tuples (count, connectionURL)
    # ===============Database Search===============
    if ("searchYt" not in request.form and "searchFlix" not in request.form and "searchFile" not in request.form): #request.form['search_src'] == 'none':
        results, count, connectionURL = search_solr(quote)
        return render_template("results.html", result=results, query=quote, results_info=[(count, connectionURL)])
    # =============YouTube=============
    if "searchYt" in request.form: #request.form['search_src'] == 'yt':
        source = request.form['yt_source']
        if len(source) > 0: # Check if a youtube link was provided
            videoID = ytVidId(source)
            if videoID: # Check if provided link is valid
                results, count, connectionURL = search_solr(quote,'yt',videoID)
                if results == 'No results found.': # Check if solr found the video id in the index. 8 is the length of [][][][]
                    print('video not found. transcribing and indexing')
                    transcriber = YouTube(videoID)
                    transcript = transcriber.getTranscript()
                    if not isinstance(transcript, str): # Check if getTranscript returned an error message
                        # try:
                        transcriptJSON = transcriber.getJSON()
                        solr.add(transcriptJSON, commit=True)
                        results, count, connectionURL = search_solr(quote,'yt',videoID)
                        # except:
                        #     print("solr server is down")

                    else:
                        results = transcript
            else:
                results = "ERROR: Invalid YouTube link"
        else:
            results, count, connectionURL = search_solr(quote,'yt')
        
        if not isinstance(results, str):
            results_info.append((count, connectionURL))

    # =============Netflix==============
    if "searchFlix" in request.form: #request.form['search_src'] == 'flix':
        source = request.form['flix_source']
        if len(source) > 0: # Check if a netflix link was provided
            videoID = flixVidId(source)
            if videoID: # Check if provided link is valid
                solr_results, count, connectionURL = search_solr(quote,'flix',videoID)
                if solr_results == 'No results found.': # Check if solr found the video id in the index. 8 is the length of [][][][]
                    print('video not found. transcribing and indexing')
                    transcriber = FlixExtractor(videoID)
                    transcriptJSON = transcriber.convertToJSON()
                    solr.add(transcriptJSON, commit=True)
                    solr_results, count, connectionURL = search_solr(quote,'flix',videoID)

            else:
                solr_results = "ERROR: Invalid Netflix link."
        else:
            solr_results, count, connectionURL = search_solr(quote,'flix')
        # title = request.form['flix_title']
        # szn = request.form['flix_szn']
        # ep = request.form['flix_ep']
        # if len(title) > 0:
        #     videoID = title + "^!" + szn + "_"+ep
        #     solr_results = search_solr(quote,'flix',videoID)
        #     if solr_results == 'No results found.': # Check if solr found the video id in the index
        #         if szn != '' and ep != '': # Check if season and episode are provided
        #             print('video not found. transcribing and indexing')
        #             try:
        #                 transcriber = FlixExtractor(title, int(szn), int(ep))
        #                 # results = "Title: " + title + "<br>Season #: " + szn + "<br>Episode #: " + ep + "<br>Results: <br>" + str(transcriber.getTranscript())
        #                 # transcriber.convertToJSON("jsonTranscripts/transcript.json")
        #                 transcriptJSON = transcriber.getJSON()
        #                 solr.add(transcriptJSON, commit=True)
        #                 solr_results = search_solr(quote,'flix',videoID)
        #             except(ValueError):
        #                 solr_results = "ERROR: Netflix show " + title + " not found"
        #             except IndexError as e:
        #                 solr_results = "ERROR:" + title +" season " + szn + " episode " + ep + " not found. " + str(e)
        # else:
        #     solr_results = search_solr(quote,'flix')

        if not isinstance(solr_results, str): # check that the netflix search didn't result in no results or an error
            results_info.append((count, connectionURL))
            if isinstance(results, str): # check if the youtube search resulted in no results or an error
                results = [] # convert results back into a list if it was an error string
            for video in solr_results:
                results.append(video)

    # ============File Upload===========
    if "searchFile" in request.form: #request.form['search_src'] == 'file':
        files = request.files.getlist('vid_upload[]')
        file_results = []
        for file in files:
            if file.filename == '':
                if not results or isinstance(results, str):
                    results = 'ERROR: No file selected'
                return render_template("results.html", result=results, query=quote)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                audioPath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(audioPath)
                transcriber = FileExtractor(audioPath, MODEL)
                transcriptList, length = transcriber.getTranscript()
                tupleList = findStringInTranscript(transcriptList, quote.lower())
                if tupleList:
                    file_result = formatTranscriptToDictionary("file", filename, tupleList)
                    file_result['length'] = int(length)
                    file_results.append(file_result)

        if isinstance(results, str): # check if the youtube or search resulted in no results or an error
            results = [] # convert results back into a list if it was an error string
        results[0:0] = file_results
        results_info.append((len(file_results), None))

    if not results: # Checkif results is still an empty list
        results = "No results found."
    return render_template("results.html", result=results, query=quote, results_info=results_info)

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

@app.route('/load', methods=['POST'])
def load_more():
    info = request.json
    results_info = info['results_info']
    start = info['start']
    results = []

    for entry in results_info:
        if entry[0] > start and entry[1] is not None:
            url = f'{entry[1]}&start={str(start)}'
            results.extend(search_solr(url=url)[0])

    return render_template('resultList.html', result=results, results_info=results_info, next_start=start+10)

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.context_processor
def utility():
    def time_string(sec):
        delta = datetime.timedelta(seconds=sec)
        stamp = (datetime.datetime.min + delta).time()
        stamp = stamp.strftime('%H:%M:%S') if stamp.hour > 0 else stamp.strftime('%M:%S')
        return stamp
    def get_extension(filename):
        extension = os.path.splitext(filename)[1]
        return extension[1:], (extension in ALLOWED_VIDEO)
    def to_type_string(typeCode):
        map = {'yt' : 'YouTube', 'flix' : 'Netflix', 'file' : 'File Upload'}
        if typeCode in map:
            return map[typeCode]
        return ''
    def get_video_link(typeCode, id, sec=None):
        map = {'yt' : 'https://youtu.be/', 'flix' : 'https://netflix.com/watch/'}
        if typeCode in map:
            if sec is not None:
                return map[typeCode] + id + '?t=' + str(sec)
            return map[typeCode] + id
        return ''
    def total_count(results_info):
        count = 0
        for entry in results_info:
            count += entry[0]
        return count
    def is_load_more(results_info, start):
        for entry in results_info:
            if entry[0] > start and entry[1] is not None:
                return True
        return False
    return dict(time_string=time_string, get_extension=get_extension, to_type_string=to_type_string, \
    get_video_link=get_video_link, is_load_more=is_load_more, total_count=total_count)

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
    ext = os.path.splitext(filename)[1]
    return '.' in filename and (ext in ALLOWED_AUDIO or ext in ALLOWED_VIDEO)

def search_solr(quote='', source='none', id='', url=None):
    if not url:
        quote = '"'+quote.replace(" ", "+")+'"'
        connectionURL = 'http://'+ SOLR_HOST + '/solr/'+SOLR_COLLECTION+'/select?q=script:' + quote + '&hl=on&hl.fl=script&hl.method=unified&omitHeader=true&hl.fragsize=0&hl.usePhraseHighlighter=true&hl.tag.pre=<b>&hl.tag.post=</b>'
        # ===============Database Search===============
        if source == 'yt':
            connectionURL = connectionURL + '&fq=%2Btype:yt'
        elif source == 'flix':
            connectionURL = connectionURL + '&fq=%2Btype:flix'
                # all_info = re.compile('^(.+?)\^!(\d{1,2})_(\d{1,3})$')
                # if all_info.match(id):
                #     connectionURL = connectionURL + '%20%2Bid:"' + urllib.parse.quote(id) + '"'
                # else:
                #     no_episode = re.compile('^(.+?)\^!(\d{1,2})_$')
                #     match = no_episode.match(id)
                #     if match:
                #         title = match.group(1)
                #         szn = match.group(2)
                #     else:# only info provided is the show name
                #         title = id[:-3]
                #     connectionURL = connectionURL +'%20%2Btitle:'+title
                # #connectionURL = connectionURL + '&fq=%2Btitle%3A"' + title.replace(" ", "+") + '"' + '%2Btype%3Aflix'
        if len(id) > 0:
            connectionURL = connectionURL + '%20%2Bid:' + id
    else:
        connectionURL = url

    print(connectionURL)
    try:
        connection = urlopen(connectionURL)
        response = json.load(connection)
    except:
        return "Sorry, the search server is currently down.", None, None

    results = []
    count = response['response']['numFound']
    # search_netflix_season = 'szn' in locals() # Check if results should be filtered by season

    for document in response['response']['docs']:
        docID = document['id']
        # if search_netflix_season:
        #     match = all_info.match(docID)
        #     docSzn = match.group(2)
        #     if docSzn != szn:
        #         continue
        if not response['highlighting'][docID]['script']:   # Unindexed video
            count -= 1
            continue
        highlightedScript = response['highlighting'][docID]['script'][0]
        highlights = extractHighlights(highlightedScript, document['times'])
        videoInfo = formatTranscriptToDictionary(document['type'], docID, highlights)
        if document['type'] == 'yt':
            info = getYouTubeInfo(docID)
        else:
            info = getNetflixInfo(docID)
        videoInfo.update(info)
        results.append(videoInfo)

    if len(results) == 0:
        results = "No results found."

    return results, count, connectionURL

def findStringInTranscript(transcriptList, targetString):
    targetStringSplit = targetString.split()
    firstWord = targetStringSplit[0]
    targetTuples = []
    x = 0
    while x < len(transcriptList):
        if (transcriptList[x])[0] == firstWord:
            y = 1
            equal = True
            while y < len(targetStringSplit) and x + y < len(transcriptList):
                if (transcriptList[x + y])[0] != targetStringSplit[y]:
                    equal = False
                y += 1
            if equal:
                z = 1
                resultString = "<b>" + targetString + "</b>"
                while z <= WORDS_OF_CONTEXT:
                    if x - z >= 0:
                        resultString = (transcriptList[x - z])[0] + " "  + resultString
                    if x + len(targetStringSplit) + z - 1 < len(transcriptList):
                        resultString = resultString + " " + (transcriptList[x + len(targetStringSplit) + z - 1])[0]
                    z += 1
                targetTuples.append((Markup(resultString), (transcriptList[x])[1]))
        x += 1
    #targetTuples = list(filter(lambda x:firstWord in x, transcriptList))
    return targetTuples

def formatTranscriptToDictionary(type, id, tupleList):
    resultDict = {"type": type, "id": id, "list": tupleList}
    return resultDict

def getYouTubeInfo(id):
    info = {}

    apiUrl = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails'
    fields = 'items(snippet(title,channelTitle,channelId,publishedAt,thumbnails/medium/url),statistics(viewCount),contentDetails(duration))'
    with urlopen(f'{apiUrl}&id={id}&key={secret.yt_key}&fields={fields}') as response:
        data = json.loads(response.read().decode())['items'][0]
        snippet = data['snippet']
        contentDetails = data['contentDetails']
        statistics = data['statistics']

        info['title'] = snippet['title']
        info['channel'] = snippet['channelTitle']
        info['channelId'] = snippet['channelId']
        date = snippet['publishedAt']
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        info['date'] = date.strftime('%b %-d, %Y')
        info['thumb'] = snippet['thumbnails']['medium']['url']
        length = contentDetails['duration']
        length = [f'{int(chunk):02d}' for chunk in re.findall(r'\d+', length)]
        if len(length) == 1:    # Prevents single number if video is under 1 min
            length.insert(0, '00')
        info['length'] = ':'.join(length) # Format to H:M:S

        views = int(statistics['viewCount'])
        if views >= 1000:
            power = int(math.log10(views))
            unit = power - power % 3
            views /= 10 ** unit

            if power == unit:
                significand = f'{views:.1f}'
            else:
                significand = f'{round(views):d}'

            unitName = ''
            unitNames = {3:'K', 6:'M', 9:'B', 12:'T'}
            if unit in unitNames:
                unitName = unitNames[unit]
            
            viewsString = f'{significand}{unitName} views'
        else:
            viewsString = f'{views} views'

        info['views'] = viewsString
    return info

def getNetflixInfo(id):
    with open(NETFLIX_ID_DIRECTORY, "r") as file:
        dictionary = json.load(file)
    entry = dictionary[id]
    return {'title': entry[0], 'season': entry[1], 'episode': entry[2], 'episodeTitle': entry[3]}

def flixVidId(url):
    idIndex = url.find("watch/") + len("watch/")
    if idIndex <= len("watch/"):
        return False
    showID = url[idIndex:]
    #8 digits is the length of the netflix ID
    if len(showID) > 8:
        showID = showID[:8]
    return showID
