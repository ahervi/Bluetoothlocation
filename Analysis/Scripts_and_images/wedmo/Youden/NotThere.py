import csv
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import random
import difflib
import math
import numbers
import pickle
import matplotlib.pyplot as plt
import operator
import itertools
import math
import datetime
import scipy as sp
import scipy.stats
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * sp.stats.t._ppf((1+confidence)/2., n-1)
    return m, m-h, m+h

#size test does not vary with size
def rssiWithHumidity(timestamp, rssi):
	res = math.cos((2*math.pi*float(timestamp2hour(timestamp))-1)/24)
	if res < -0.5:		
		res = -0.5
	return rssi - res
def timestamp2hour(timestamp):
	return int(datetime.datetime.fromtimestamp(int(timestamp)).strftime('%H'))

def probabilityPredictionMain(clf4, X, XuntouchedF, threshold):
	YpredictionConsecutiveSignal = []
	
	probas4 = clf4.predict_proba(XuntouchedF)

	places = ['carte_bancaire', 'fenetre_casque', 'fenetre_russia', 'me', 'russia', 'the']

	for i in range(len(probas4)):

		probas = [probas4[i][j] for j in range(len(probas4[i]))]
		maxIndex = max(enumerate(probas),key=lambda x: x[1])[0]
		toAppend = [0]*len(probas)
		for j in range(len(probas)):
			if probas[j] > threshold:
				toAppend[j] = 1
		
		YpredictionConsecutiveSignal.append(toAppend)

	return YpredictionConsecutiveSignal
def placesToIndex(place):
	places = ['carte_bancaire', 'fenetre_casque', 'fenetre_russia', 'me', 'russia', 'the']
	for i in range(len(places)):
		if(places[i] == place):
			k = i
	return k

def probabilityPredictionSub(sizeTest, clf3_1, clf3_2, clf3_3, clf3_4, X1, X2, X3, X4, XuntouchedF,XuntouchedF1,XuntouchedF2,XuntouchedF3,XuntouchedF4, YuntouchedF):
	YpredictionConsecutiveSignal = []
	probas3_1 = clf3_1.predict_proba(XuntouchedF1)
	probas3_2 = clf3_2.predict_proba(XuntouchedF2)
	probas3_3 = clf3_3.predict_proba(XuntouchedF3)
	probas3_4 = clf3_4.predict_proba(XuntouchedF4)
	places = ['carte_bancaire', 'fenetre_casque', 'fenetre_russia', 'me', 'russia', 'the']

	for i in range(len(probas3_1)):

		probas = [probas3_1[i][j]+probas3_2[i][j]+probas3_3[i][j]+probas3_4[i][j] for j in range(len(probas3_1[i]))]
		maxIndex = max(enumerate(probas),key=lambda x: x[1])[0]
		YpredictionConsecutiveSignal.append(places[maxIndex])

	return YpredictionConsecutiveSignal
	
def givesClassifier(ID, DBS, XconsecutiveSignalCombinaisons, XconsecutiveSignal, YconsecutiveSignalCombinaisons, YconsecutiveSignal, XuntouchedF, YuntouchedF):
	clf4 = RandomForestClassifier(n_estimators=100)

	clf4 = clf4.fit(XconsecutiveSignal, YconsecutiveSignal)


	YpredictionConsecutiveSignal4 = clf4.predict(XuntouchedF)
	Yshould = YuntouchedF
	ratio4 = 0
	dicDB = dict()
	for db in DBS:
		dicDB[db[2]] = 0

	for j in range(len(YpredictionConsecutiveSignal4)):
		if Yshould[j] == YpredictionConsecutiveSignal4[j]:
			ratio4 += 1
		else:
			dicDB[Yshould[j]] += 1
	errors4= ratio4
	ratio4 = float(ratio4)

	ratio4 = ratio4 / len(Yshould)
	print("Similarity percentile : " + str(ratio4))
	print(str(len(Yshould)- errors4) + " errors ( " + str(100-100*float(errors4)/len(Yshould))+ "% ) on " + str(len(Yshould)) + " predicted samples out of " + str(len(XconsecutiveSignal)) + " training samples : " + str(dicDB))
	#with open("randomForestModel" + str(ID) ,"wb") as f:
		#pickle.dump(clf4, f)
	return clf4, YpredictionConsecutiveSignal4

def givesTriList(list):
	res1 = []
	res2 = []
	res3 = []
	res4 = []
	for l in list:
		res1.append([l[0],l[1],l[2]])
		res2.append([l[0],l[1], l[3]])

		res3.append([l[0], l[2],l[3]])
		res4.append([l[1],l[2],l[3]])
	res = [res1, res2, res3, res4]
	return res

def givesList(DB_NAME, BSSID, size):
	
	FILENAME = DB_NAME[:-3] + ".csv"


	with sqlite3.connect(DB_NAME) as conn:
		c = conn.cursor()
		MAXID = 4

		
		RSSIS = []
		RSSI_HEADER = []
		for i in range(MAXID):
			RSSI_HEADER.append("RPI" + str(i + 1))
		RSSIS.append(RSSI_HEADER)

		rssiContent = []


	with sqlite3.connect(DB_NAME) as conn:
		cursor = conn.cursor()
		cursor.execute("""select ID, NAME, BSSID, TIME_STAMP, RSSI from COMBINED WHERE BSSID = ? ORDER BY TIME_STAMP ASC""", (BSSID,))
		rows = cursor.fetchall()
		extractedSignalsList = []

		for row in rows:
			extractedSignalsList.append([row[0], row[1].encode("ascii"), row[2].encode("ascii"), row[3], row[4]])
	#We have the rssis list by rpis' id : [id, RSSI] -> extractedSignalsList
	TIME_WINDOW = 15


	#index of the extractedSignalsList containing the succesive RSSIs by id : [RSSI1, RSSI2, ... , RSSIIDMAX] -> consecutiveSignalsList
	i = -1



	consecutiveSignalsList = []
	consecutiveSignal = [0]*MAXID
	#Initialisation of the timers for each RPIS : 

	timersBefore = [0]*MAXID

	# initialisation of the timers:
	k = 0
	while 0 in timersBefore:
		timersBefore[extractedSignalsList[k][0] - 1] = extractedSignalsList[k][3]
		k += 1

	timersAfter = [0]*MAXID

	idRPI = extractedSignalsList[0][0] - 1
	#index of extractedSignalsList
	j = 0

	while j < len(extractedSignalsList):
		row = extractedSignalsList[j]
		timersAfter[idRPI] = int(row[3])
		idRPI = row[0] - 1

		if isinstance(row[4], numbers.Number) and row[4] < 1:

			#If there have not been an update from all RPIS in the TIME_WINDOW : abandon of current index 
			# One of the RPIS have not manifested himself
			for l in range(MAXID):
				if timersAfter[idRPI] - timersBefore[l] > TIME_WINDOW and l != idRPI:
					consecutiveSignal[l] = 0
					timersBefore[l] = timersAfter[idRPI]

		
			#consecutiveSignal[idRPI] = rssiWithHumidity(timersAfter[idRPI], row[4])
			consecutiveSignal[idRPI] = row[4]

			if not 0 in consecutiveSignal and (len(consecutiveSignalsList) == 0 or (len(consecutiveSignalsList) > 0 and consecutiveSignal != consecutiveSignalsList[-1])): 
				roundedSignal = [0]*MAXID
				for m in range(MAXID):
					roundedSignal[m] = int(10 * consecutiveSignal[m]) / 10.0
				consecutiveSignalsList.append(roundedSignal)
				i += 1
			timersBefore[idRPI] = timersAfter[idRPI]

		j+=1
	lengthAfter = len(consecutiveSignalsList)
	#trying
	random.seed(1)
	b = range(len(consecutiveSignalsList))
	random.shuffle(b)
	consecutiveSignalsList = [consecutiveSignalsList[i] for i in b] # or:


	sizeUntouched = size
	lengthUntouched = int(math.floor(sizeUntouched*len(consecutiveSignalsList)))
	Xuntouched = consecutiveSignalsList[lengthUntouched:]
	consecutiveSignalsList = consecutiveSignalsList[:lengthUntouched]
	#Debut du test de consecutiveSignalaison
	ultiList = []
	for p in range(len(consecutiveSignalsList) - 1):
		extractedSignalsList1 = consecutiveSignalsList[p]
		extractedSignalsList2 = consecutiveSignalsList[p+1]
		consecutiveSignal = []
		i = 0
		MAX = len(extractedSignalsList1)

		for z in range(len(extractedSignalsList1)):
			for e in range(len(extractedSignalsList1)):
				for r in range(len(extractedSignalsList1)):
					oneCombinaison = [elem for elem in extractedSignalsList1]
					oneCombinaison[z] = extractedSignalsList2[z]
					oneCombinaison[e] = extractedSignalsList2[e]
					oneCombinaison[r] = extractedSignalsList2[r]
					consecutiveSignal.append(oneCombinaison)

		consecutiveSignal.sort()
		consecutiveSignal = list(consecutiveSignal for consecutiveSignal,_ in itertools.groupby(consecutiveSignal))
		consecutiveSignal.insert(0, extractedSignalsList2)
		consecutiveSignal.insert(0, extractedSignalsList1)
		ultiList.extend(consecutiveSignal)
	return [ultiList, givesTriList(ultiList), consecutiveSignalsList, givesTriList(consecutiveSignalsList), Xuntouched, givesTriList(Xuntouched)]
DB_NAME = "WEDNESDAYWEEK4AFTERNOON"

DBS = [[DB_NAME, "C1:CF:31:F3:29:6C", "russia"], [DB_NAME, "C7:64:6C:03:B9:40", "me"], [DB_NAME, "DA:E7:8C:CA:05:CF", "fenetre_casque"], [DB_NAME, "F2:39:F2:6A:80:89", "fenetre_russia"], [DB_NAME, "C7:62:97:12:1E:35", "the"], [DB_NAME, "E4:FA:6E:AF:58:19", "carte_bancaire"]]
XuntouchedF4 = []
# C
graph2 = []
graph3 = []
graph4 = []

size = 0.50
XconsecutiveSignalCombinaisons = []
XconsecutiveSignalCombinaisons1 = []
XconsecutiveSignalCombinaisons2 = []
XconsecutiveSignalCombinaisons3 = []
XconsecutiveSignalCombinaisons4 = []
YconsecutiveSignalCombinaisons = []

XconsecutiveSignal = []
XconsecutiveSignal1 = []
XconsecutiveSignal2 = []
XconsecutiveSignal3 = []
XconsecutiveSignal4 = []
YconsecutiveSignal = []
YuntouchedF = []
XuntouchedF = []
XuntouchedF1 = []
XuntouchedF2 = []
XuntouchedF3 = []
XuntouchedF4 = []

for name in DBS:
	bigList = givesList(name[0]+".db", name[1], size)

	extractedSignalsList4 ,extractedSignalsList3_1, extractedSignalsList3_2, extractedSignalsList3_3, extractedSignalsList3_4= bigList[0], bigList[1][0], bigList[1][1], bigList[1][2], bigList[1][3]
	XconsecutiveSignalCombinaisons.extend(extractedSignalsList4)
	XconsecutiveSignalCombinaisons1.extend(extractedSignalsList3_1)
	XconsecutiveSignalCombinaisons2.extend(extractedSignalsList3_2)
	XconsecutiveSignalCombinaisons3.extend(extractedSignalsList3_3)
	XconsecutiveSignalCombinaisons4.extend(extractedSignalsList3_4)
	YconsecutiveSignalCombinaisons.extend([name[2]]*len(extractedSignalsList4))	
	
	extractedSignalsListfinal4 ,extractedSignalsListfinal3_1, extractedSignalsListfinal3_2, extractedSignalsListfinal3_3, extractedSignalsListfinal3_4= bigList[2], bigList[3][0], bigList[3][1], bigList[3][2], bigList[3][3]
	extractedSignalsListU, extractedSignalsListU1, extractedSignalsListU2, extractedSignalsListU3, extractedSignalsListU4 =  bigList[4], bigList[5][0], bigList[5][1], bigList[5][2], bigList[5][3]
	XconsecutiveSignal.extend(extractedSignalsListfinal4)
	XconsecutiveSignal1.extend(extractedSignalsListfinal3_1)
	XconsecutiveSignal2.extend(extractedSignalsListfinal3_2)
	XconsecutiveSignal3.extend(extractedSignalsListfinal3_3)
	XconsecutiveSignal4.extend(extractedSignalsListfinal3_4)
	YconsecutiveSignal.extend([name[2]]*len(extractedSignalsListfinal4))		
	XuntouchedF.extend(extractedSignalsListU)
	XuntouchedF1.extend(extractedSignalsListU1)
	XuntouchedF2.extend(extractedSignalsListU2)
	XuntouchedF3.extend(extractedSignalsListU3)
	XuntouchedF4.extend(extractedSignalsListU4)

	YuntouchedF.extend([name[2]]*len(extractedSignalsListU))


random.seed(1)

b = range(len(XconsecutiveSignalCombinaisons))

random.shuffle(b)
XconsecutiveSignalCombinaisons = [XconsecutiveSignalCombinaisons[i] for i in b] # or:
XconsecutiveSignalCombinaisons1 = [XconsecutiveSignalCombinaisons1[i] for i in b] # or:
XconsecutiveSignalCombinaisons2 = [XconsecutiveSignalCombinaisons2[i] for i in b] # or:
XconsecutiveSignalCombinaisons3 = [XconsecutiveSignalCombinaisons3[i] for i in b] # or:
XconsecutiveSignalCombinaisons4 = [XconsecutiveSignalCombinaisons4[i] for i in b] # or:

YconsecutiveSignalCombinaisons = [YconsecutiveSignalCombinaisons[i] for i in b] # or:


b = range(len(XconsecutiveSignal))

random.shuffle(b)
XconsecutiveSignal = [XconsecutiveSignal[i] for i in b] # or:
XconsecutiveSignal1 = [XconsecutiveSignal1[i] for i in b] # or:
XconsecutiveSignal2 = [XconsecutiveSignal2[i] for i in b] # or:
XconsecutiveSignal3 = [XconsecutiveSignal3[i] for i in b] # or:
XconsecutiveSignal4 = [XconsecutiveSignal4[i] for i in b] # or:

YconsecutiveSignal = [YconsecutiveSignal[i] for i in b] # or:

per = []
graphN = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
graphPN = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
graphP = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
graphNN = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
thresholds = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
Youdi = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
Equal = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
NumberOfClf = 300
for j in range(NumberOfClf):
	print("We are at " + str(j) + " out of " + str(NumberOfClf))
	
	Yshould = YuntouchedF
	clf4, YpredictionConsecutiveSignal4 = givesClassifier("4", DBS, XconsecutiveSignalCombinaisons, XconsecutiveSignal, YconsecutiveSignalCombinaisons, YconsecutiveSignal, XuntouchedF, YuntouchedF)


	taille = 1000
	maximum = 100
	for i in range(0,taille + 1):
		threshold = i*maximum/float(taille*100)
		per.append(threshold)
		YpredictionConsecutiveSignal = probabilityPredictionMain(clf4, XconsecutiveSignal, XuntouchedF, threshold)
	 	falseNegative = 0
	 	falsePositive = 0
		for k in range(len(YpredictionConsecutiveSignal)):

			if YpredictionConsecutiveSignal[k][placesToIndex(YuntouchedF[k])] == 0 :
				falseNegative += 1
				#ratio += float(len(YpredictionConsecutiveSignal[k]))/(len(DBS)-1)
				#ratio += 1
			for l in range(len(YpredictionConsecutiveSignal[k])):
				if YpredictionConsecutiveSignal[k][l] == 1 and placesToIndex(YuntouchedF[k]) != l:
					falsePositive += 1
		falseNegativeNumber = falseNegative
		falsePositiveNumber = falsePositive
		falsePositive = float(falsePositive) / (len(YpredictionConsecutiveSignal)*(len(YpredictionConsecutiveSignal[0])-1))
		falseNegative = float(falseNegative) / len(YpredictionConsecutiveSignal)
		#graph3.append(100-100*float(errors)/len(YpredictionConsecutiveSignal))
		graphP[j].append(falsePositive)
		graphN[j].append(falseNegative)
		graphPN[j].append(falsePositiveNumber)
		graphNN[j].append(falseNegativeNumber)
		Youdi[j].append(1-falseNegative-falsePositive)
		Equal[j].append(abs(falseNegative-falsePositive))
		thresholds[j].append(threshold)
		#print(100*(float(i)/maximum))
		#print(100*float(errors)/len(YpredictionConsecutiveSignal))
		print(100*i/float(taille))
thresholdsY = []
thresholdsE = []
for i in range(NumberOfClf):
	maxIndexY = max(enumerate(Youdi[i]),key=lambda x: x[1])[0]
	maxIndexE = min(enumerate(Equal[i]),key=lambda x: x[1])[0]

	thresholdsY.append(thresholds[i][maxIndexY]) 
	thresholdsE.append(thresholds[i][maxIndexE]) 

graphP = [sum(x)/float(NumberOfClf) for x in zip(*graphP)]
per = per[:taille+1]
print(len(graphP))
print(len(per))
graphN = [sum(x)/float(NumberOfClf) for x in zip(*graphN)]
graphPN = [sum(x)/float(NumberOfClf) for x in zip(*graphPN)]
Youdi = [sum(x)/float(NumberOfClf) for x in zip(*Youdi)]
graphNN = [sum(x)/float(NumberOfClf) for x in zip(*graphNN)]



print("Youden threshold")
print(np.mean(thresholdsY))
print(np.std(thresholdsY))
print(mean_confidence_interval(thresholdsY))
print(mean_confidence_interval(thresholdsY, 0.99))
print(mean_confidence_interval(thresholdsY, 0.999))
print(mean_confidence_interval(thresholdsY, 0.9999))



print("Equal rates threshold")
print(np.mean(thresholdsE))
print(np.std(thresholdsE))
print(mean_confidence_interval(thresholdsE))
print(mean_confidence_interval(thresholdsE, 0.99))
print(mean_confidence_interval(thresholdsE, 0.999))
print(mean_confidence_interval(thresholdsE, 0.9999))

fig, axes1 = plt.subplots() 
axes2 = axes1.twinx()

plt.gca().set_color_cycle(['black', 'green', 'blue', 'red', 'orange'])
axes = plt.gca()


axes1.set_ylim([0,1])
axes1.set_ylabel("Youden's index", color = 'black')
axes1.plot(per,Youdi,color='black')


axes1.set_xlabel('threshold')
plt.savefig("youdenIndex.png")

plt.show()

plt.clf()
plt.close()
ig, axes1 = plt.subplots() 
axes2 = axes1.twinx()

plt.gca().set_color_cycle(['black', 'green', 'blue', 'red', 'orange'])
axes = plt.gca()


axes1.set_ylim([0,0.06])
axes2.set_ylim([0,0.06])
axes1.set_ylabel('false negative rate', color = 'black')
axes1.plot(per,graphN,color='black')

axes2.plot(per,graphP,color = 'green')

axes2.set_ylabel('false positive rate', color = 'green')
axes1.set_xlabel('threshold')

plt.savefig("both.png")
plt.show()
plt.clf()
plt.close()
fig, axes1 = plt.subplots() 
axes2 = axes1.twinx()
plt.gca().set_color_cycle(['black', 'green', 'blue', 'red', 'orange'])
axes = plt.gca()



axes1.set_ylim([0,1000])
axes2.set_ylim([0,1000])
axes1.set_ylabel('false negative', color = 'black')
axes1.plot(per,graphNN,color='black')

axes2.plot(per,graphPN,color = 'green')


axes2.set_ylabel('false positive', color = 'green')
axes1.set_xlabel('threshold')
plt.savefig("bothNumber.png")
plt.show()

plt.clf()
plt.close()
fig, axes1 = plt.subplots() 
axes2 = axes1.twinx()
plt.gca().set_color_cycle(['black', 'green', 'blue', 'red', 'orange'])
axes = plt.gca()



axes1.set_ylabel('false negative', color = 'black')
axes1.plot(per,graphNN,color='black')



axes1.set_xlabel('threshold')
plt.savefig("falseneg.png")
plt.show()
plt.clf()
plt.close()
fig, axes1 = plt.subplots() 
plt.gca().set_color_cycle(['black', 'green', 'blue', 'red', 'orange'])
axes = plt.gca()



axes1.plot(per,graphPN,color = 'green')


axes1.set_ylabel('false positive', color = 'green')
axes1.set_xlabel('threshold')
plt.savefig("falsepos.png")
plt.show()

