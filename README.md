![Stampyboi logo](https://github.com/harrijin/stampyboi/blob/master/static/images/logo.png?raw=true)

# What is Stampyboi?

Stampyboi is a tool to help you quickly and easily find the timestamped video clips you're looking for. 

# Table of Contents

- [Features](#features)
- [Usage](#usage)
  * [Quick Start](#quick-start)
  * [Details](#details)
- [Demo Video](#demo-video)
- [How Stampyboi works](#how-stampyboi-works)
  * [Core Technologies](#core-technologies)
  * [Data Sources](#data-sources)

# Features

- Easy file uploads
- Easy conversion to .gif format
- Easy sharing to Facebook, Twitter, Reddit, and other social media
- Autosuggester: generated from the Stampyboi's index so that suggestions are guaranteed to return results
- Spellcheck: also generated from Stampyboi's index
- Word stemmer: [Porter Stemming Algorithm](https://tartarus.org/martin/PorterStemmer/def.txt)
- Stop word filter: [List of stampyboi stopwords](https://github.com/harrijin/stampyboi/blob/master/solrConfig/stopwords.txt)
- Phonetic matching filter: [Double metaphone algorithm](https://en.wikipedia.org/wiki/Metaphone#Double_Metaphone)

# Usage

## Quick Start

Simply type a quote from a YouTube video or Netflix show you're looking for and hit "Search".

## Details

![SCREENSHOT OF SEARCH PAGE](https://github.com/harrijin/stampyboi/blob/master/readmeImages/search.png?raw=true)

- Quote search bar: Takes in a quote to query. Includes autosuggest functionality. 
- "Options" button: Toggles options menu
- "About" button: Links to this repository

![SCREENSHOT OF OPTIONS](https://github.com/harrijin/stampyboi/blob/master/readmeImages/options.png?raw=true)

- Options menu: Allows user to narrow your search based on video type.
- YouTube source (optional): Allows user to paste in a link to a YouTube video to search. If left blank, the query will be searched against all YouTube videos in Stampyboi's index.
- Netflix source (optional): Same as YouTube source.
- File upload: Allows user to upload one or more audio/video files to be searched using [speech-to-text](#core-technologies). Can select from file explorer or drag and drop. Currently supported file-formats: wav, ogv, mp4, avi, mov, mpeg.

![SCREENSHOT OF RESULTS](https://github.com/harrijin/stampyboi/blob/master/readmeImages/results.png?raw=true)

- Stampyboi logo: Returns user to search page.
- Quote search bar (top right): Allows user to submit a new general query.
- Video result: Shows thumbnail, title, and list of timestamps that match the query. The user can jump to a specific part of the video by selecting the desired timestamp. Selecting the right-hand tab will link directly to the source video.

![SCREENSHOT OF VIDEO](https://github.com/harrijin/stampyboi/blob/master/readmeImages/video.png?raw=true)

- List of timestamps: Selecting the desired timestamp allows the user to seek to a specific part of the video.
- Share this boi (Netflix or YouTube videos only): Allows user to copy the currently selected timestamped link or share the currently selected timestamped link to Facebook, Twitter, or Reddit. YouTube videos also have the option of being converted into gifs.

# Demo Video

# How Stampyboi works

Stampyboi indexes videos by extracting and storing their timestamped transcripts. When a query is submitted to Stampyboi, it searches its expansive index of over 330,000 videos to find transcripts containing the queried phrase. When a video link is specified, Stampyboi first checks to see if that video is stored in its index. If the video is found, Stampyboi will filter the results to only show that specific video. If not, the video is transcribed, indexed, then searched for the queried phrase (user-uploaded video/audio files are searched and then immediately deleted from the server). That video will now show up in the results when future users make general queries. 

## Core Technologies

- [Apache Solr](https://lucene.apache.org/solr/)
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [DeepSpeech](https://deepspeech.readthedocs.io/en/v0.7.3/?badge=latest)
- [MoviePy](https://zulko.github.io/moviepy/ref/ref.html)

## Data Sources

- [YouTube8M](https://research.google.com/youtube8m/)
- [Netflix ID Dataset](https://healdb.tech/blog/netflix.html)
