import requests,json,sys,re,os,time
import threading
from datetime import datetime


from VideoIDHelper import *
from collections import deque
from bs4 import BeautifulSoup

def reportProgress():
	global t
	if toGather != 1:
		print("Processed {}/{} videos.".format(i,toGather))
	else:
		print("Processed 0/1 video.")
	t=threading.Timer(10.0, reportProgress)
	t.start()

def reportGathering():
	global t
	print("{} links gathered so far...".format(len(m)))
	t=threading.Timer(10.0, reportGathering)
	t.start()

#Globals
m={}
q=deque()
i=0
toGather=0
t = threading.Timer(10.0, reportProgress, [i,toGather])

def makeRequest(partialURL,parameter,ID):
	pars = {"parameter" : ID}
	return requests.get(partialURL, params=pars)
def makeRequestWithoutParameter(URL):
	return requests.get(URL)

def backUpAnnotations(ID):
	return makeRequestWithoutParameter("http://web.archive.org/save/https://www.youtube.com/annotations_invideo?video_id={}".format(ID))
def snapShotPage(ID):
	return makeRequest("http://web.archive.org/save/https://www.youtube.com/watch","v",ID)

def annotationsBackedUp(ID):
	return makeRequestWithoutParameter("http://archive.org/wayback/available?url=https://www.youtube.com/annotations_invideo?video_id={}".format(ID))
def snapShotTaken(ID):
	return makeRequestWithoutParameter("http://archive.org/wayback/available?url=https://www.youtube.com/watch?v={}".format(ID))


def main():
	global i,toGather
	first = True
	argument = ""
	print( "Hello today is: " + str(datetime.now().month) + "/" + str(datetime.now().day))
	#print( "Remember that we have time until: " + "1/15" + "for Annotations and Credits; and until " + "1/31" +" for Episodes (presumably PST 0:00) " )
	print( "Remember that we have time until: " + "1/15" + "for the Annotations (presumably PST 0:00) " )
	while first or argument == "":
		#argument ="horse"
		argument = input("Type in a URL to video or its ID: ")

		if argument == "":
			print("Program Terminated")
			break

		else:
			#Check for the initial link
			vID = idExtractor(argument)
			#print("vID: {}".format(vID))
			r = annotationsBackedUp(vID)
			if 'closest' in r.json()["archived_snapshots"]:
				print('That link seems to have been saved.')
				isY = input('But if you want to make sure that all sublinks have also been saved type y\n')
				if isY.rstrip().strip() != "y":
					continue

			err = gatherStartingFrom(vID)
			t.cancel()
			if err ==1:
				continue

			toGather = len(m)
			print("Discovered {} videos...".format(toGather))
			i=0
			successes=0
			Break=False
			reportProgress()
			#t.start()
			for ID in m:
				while True:
					code = backUp(ID)
					if code == 1:
						print("The video with id {} wasn't saved properly".format(vID))
						action=""
						while action!='r' and action!='a' and action!='i':
							action = ("Type r to retry,i to ignore or a to abort:\n")
							action = action.rstrip().strip()
						if action == 'r':
							continue
						if action == 'i':
							i+=1
							break
						if action == 'a':
							Break=True
							i+=1
							break
					else:
						m[ID]=True
						i+=1
						successes+=1
						break
				if Break:
					break
			t.cancel()
			if toGather == 1:
				print("{}/{} is now backed up!".format(successes,toGather))
			print("{}/{} are now backed up!".format(successes,toGather))
	
def gatherStartingFrom(vID):
	global m,q
	m={}
	q=deque()
	q.append(vID)
	m[vId] = False

	print("Gathering links... This might take a few moments...")
	reportGathering()
	while len(q) != 0:
		head = q.pop()
		code = gather(head)
		#check for errors
		if code == 1:
			print("An error occured while trying to gather the videos...")
			action=""
			while action!='r' and action!='a'  :
				action = input("Type r to retry or a to abort:\n")
				action = action.rstrip().strip()
			if action == 'r':
				#reset this
				q.append(head)
				continue
			if action == 'a':
				return 1
				break
		#q.pop()

	#print (m)
	return 0

def gather(vID):
	#OPEN vID's ANNOTATIONS BY REQUEST
	#Done
	#SCAN FOR ANYTHING THAT HAS /WATCH or the shortened URL
	#Done

	#TRY TO ADD TO M
	#IF CAN ADD TO M ADD TO Q
	#done

	#IF CAN'T ADD TO M MOVE ON
	#done
	#RETURN 1 if ERROR IS RAISED
	#done
	try:
		r = requests.get("https://www.youtube.com/annotations_invideo?video_id={}".format(vID))
		#print("https://www.youtube.com/annotations_invideo?video_id={}".format(vID))
		#xml = ""
		xml = str(r.text)
		soup = BeautifulSoup(xml, 'xml')
		#print(soup.prettify()[:300])
		#filteredSoup = [ x.attrs for x in soup.find_all(type=['text','highlight'])]
		#filteredSoup = [ x['value'] for x in soup.find_all('url') if (x['value'].find('/watch') != -1 or x['value'].find('.be') != -1)]
		filteredSoup=[ idExtractor(x['value']) for x in soup.find_all('url') if (x['value'].find('/watch') != -1 or x['value'].find('.be') != -1) ]
		#shortUrls=[ idExtractor(x['value']) for x in soup.find_all('url') if x['value'].find('.be') != -1]
		#print(longUrls)
		#print(shortUrls)
		#itct = soup.annotations["itct"]
		#newSoup=BeautifulSoup("<document><annotations itct=\""+itct+"\">"+"".join([str(x) for x in filteredSoup])+"</annotations></document>",'xml')
		#print(newSoup.prettify())


		for lId in filteredSoup:
			#print (lId)
			if not lId in m:
				m[lId] = False
				q.append(lId)
				#print("added {} to queue".format(lId))
			#else:
				#print("duplicate entry detected")
	except:
		return 1
	else:
		return 0



def backUp(vID):
	try:
		r = snapShotTaken(vID)
		if 'closest' not in r.json()["archived_snapshots"]:
			r2=snapShotPage(vID)
			if r2.status_code != 200:
				return 1
		r = annotationsBackedUp(vID)
		if 'closest' not in r.json()["archived_snapshots"]:
			r2=backUpAnnotations(vID)
			if r2.status_code != 200:
				return 1
	except Exception as e:
		print(e)
		return 1
	else:
		return 0


if __name__== "__main__":
	main()