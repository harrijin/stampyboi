import os, json

movieDirectory = r'O:\Git Projects\stampiboi netflix files\fixedMovieFiles'
showDirectory = r'O:\Git Projects\stampiboi netflix files\fixedShowFiles'
outputAddress = 'O:/Git Projects/stampiboi/flixIDConverter/netflixIDDictionary.json'
indexOfSeason = 4
indexOfEpisodes = 5
gapToSplitSeason = 100

#given a json file with a list of episodes in a series, returns a list of dictionary entries
def jsonToDictEntryShow(jsonInput):
	dictionary = json.load(jsonInput)
	title = getTitleForShow(dictionary)
	seasonCount = getSeasonCountForShow(dictionary)
	episodeList = getEpisodeListForShow(dictionary)
	index = 0
	episodeNum = 0
	seasonNum = 0
	previousID = 0
	entryList = []
	if episodeList != -1 and episodeList != 0:
		while index < len(episodeList):
			episodeInfo = getEpisodeInfoFromEntry(episodeList[index])
			if int(episodeInfo[1]) - previousID > gapToSplitSeason and seasonCount > seasonNum:
				seasonNum = seasonNum + 1
				episodeNum = 0
			episodeNum = episodeNum + 1
			entry = [title, seasonNum, episodeNum, episodeInfo[0], episodeInfo[1]]
			entryList.append(entry)
			previousID = int(episodeInfo[1])
			index = index + 1
		return entryList
	else:
		entry = [title, 1, 1, title, getIDFromDictionary(dictionary)]
		return [entry]

def getIDFromDictionary(dictionary):
	catalog_titleDictionary = dictionary["catalog_title"]
	url = catalog_titleDictionary["id"]
	idIndex = url.find("series/") + len("series/")
	if idIndex <= len("series/"):
		idIndex = url.find("movies/") + len("movies/")
	showID = url[idIndex:]
	return showID



def getTitleForShow(dictionary):
	catalog_titleDictionary = dictionary["catalog_title"]
	titleDictionary = catalog_titleDictionary["title"]
	#The other option (as opposed to regular) is "short"
	return titleDictionary["regular"]

def getSeasonCountForShow(dictionary):
	catalog_titleDictionary = dictionary["catalog_title"]
	linkList = catalog_titleDictionary["link"]
	seasonDictionary = linkList[indexOfSeason]
	if seasonDictionary["title"] != "seasons":
		seasonsFound = False
		for dic in linkList:
			if dic["title"] == "seasons":
				seasonDictionary = dic
				seasonsFound = True
		if seasonsFound == False:
			return 1
	if "catalog_titles" in seasonDictionary.keys():
		innerDictionary = seasonDictionary["catalog_titles"]
		seasonList = innerDictionary["link"]
		return len(seasonList)
	else:
		return 1

def getEpisodeListForShow(dictionary):
	catalog_titleDictionary = dictionary["catalog_title"]
	linkList = catalog_titleDictionary["link"]
	episodeDictionary = linkList[indexOfSeason]
	if episodeDictionary["title"] != "episodes":
		episodesFound = False
		for dic in linkList:
			if dic["title"] == "episodes":
				episodeDictionary = dic
				episodesFound = True
		if episodesFound == False:
			return 0
	if "catalog_titles" in episodeDictionary.keys():
		innerDictionary = episodeDictionary["catalog_titles"]
		episodeList = innerDictionary["link"]
		if "number_of_results" in innerDictionary.keys() and innerDictionary["number_of_results"] == 1:
			episodeList = [episodeList]
		return episodeList
	else:
		return -1

def getEpisodeInfoFromEntry(dictionary):
	episodeName = dictionary["title"]
	href = dictionary["href"]
	episodeNumberIndex = href.find("programs/") + len("programs/")
	episodeNumber = href[episodeNumberIndex:]
	return [episodeName, episodeNumber]

def generateDictionary():
	resultDic = {}
	for entry in os.scandir(showDirectory):
		if entry.is_file():
			with open(entry) as file:
				entryList = jsonToDictEntryShow(file)
				for entry in entryList:
					entryValue = [entry[0], entry[1], entry[2], entry[3]]
					print(entry[4] + ": " + str(entryValue))
					resultDic[int(entry[4])] = entryValue
	return resultDic

def writeDictAsJSON(dictionary, fileAddress):
	with open(fileAddress, "w") as outfile:
		json.dump(dictionary, outfile)

# "Main method" (runs on execution) ===================================================
dictionary = generateDictionary()
print(dictionary)
writeDictAsJSON(dictionary, outputAddress)


#with open('O:/Git Projects/stampiboi netflix files/fixedShowFiles/80049714.txt') as f:
#	print(jsonToDictEntryShow(f))