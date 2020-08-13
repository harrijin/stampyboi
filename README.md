![Stampyboi logo](https://github.com/harrijin/stampyboi/blob/master/static/images/logo.png?raw=true)

# What is Stampyboi?

Stampyboi is a tool to help you quickly and easily find the timestamped video clips you're looking for. 

# Table of Contents



# Demo Video

# Features

- Autosuggester, generated from the Stampyboi's database so that suggestions are guaranteed to return results. 
- Spellcheck
- Word stemmer
- Stop word filter
- Phonetic matching filter
- Easy file uploads

# Usage

## Quick Start

Simply type a quote from a YouTube video or Netflix show you're looking for and hit "Search".

## Details

SCREENSHOT OF SEARCH PAGE

- Quote search bar: Takes in a quote to query. Includes autosuggest functionality. 
- "Options" button: Toggles options menu
- "About" button: Links to this repository

SCREENSHOT OF OPTIONS

- Options menu: Allows user to narrow your search based on video type
- YouTube source (optional): Allows user to paste in a link to a YouTube video to search. If left blank, the query will be searched against all YouTube videos in Stampyboi's index.
- Netflix source (optional): Same as YouTube source.
- File upload: Allows user to upload one or more audio/video files to be searched using [speech-to-text](#core-technologies). Currently supported file-formats: wav, ogv, mp4, avi, mov, mpeg.

SCREENSHOT OF RESULTS

- Stampyboi logo: Returns user to search page.
- Quote search bar (top right): Allows user to submit a new general query.
- Video result: Shows thumbnail, title, and list of timestamps that match the query. The user can jump to a specific part of the video by selecting the desired timestamp. Selecting the right-hand tab will link directly to the source video.
- "Load more" button: Allows user to load more results for the current query.

SCREENSHOT OF VIDEO

- List of timestamps: Selecting the desired timestamp allows the user to seek to a specific part of the video.
- Share this boi (Netflix or YouTube videos only): Allows user to copy the currently selected timestamped link or share the currently selected timestamped link to Facebook, Twitter, or Reddit. YouTube videos also have the option of being converted into gifs.



# Core Technologies

-[Apache Solr](https://lucene.apache.org/solr/)
-[Flask](https://flask.palletsprojects.com/en/1.1.x/)
-[YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
-[DeepSpeech](https://deepspeech.readthedocs.io/en/v0.7.3/?badge=latest)
-[MoviePy](https://zulko.github.io/moviepy/ref/ref.html)
