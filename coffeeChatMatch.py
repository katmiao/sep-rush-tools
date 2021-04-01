import csv
import random
import copy
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(linewidth=2000) 
random.seed(10)
import pandas

matchScoreMatrix = []
activeIdMap = {}
rusheeIdMap = {}
activeMatchCounts = {}
numRushees = 0
numActives = 0
matchScores = [5, 4, 3, 2, 1]
numSlots = 6
timeslotStrs = ["7:00-7:20PM", "7:20-7:40PM", "7:40-8:00PM", "8:00-8:20PM", "8:20-8:40PM", "8:40-9:00PM", ]

def timetableTrial(trialMatrix):
	# reset everything for this trial
	timetableScoreTotal = 0

	# keep dict of arrays of timeslots each rushees must still be scheduled for
	rusheeTimeslots = {}
	for i in range(numRushees):
		shuffledSlots = [j for j in range(numSlots)]
		random.shuffle(shuffledSlots) 
		rusheeTimeslots[i] = shuffledSlots

	# keep track of how many double slots each active/rushee has
	activeDoubleSlots = { i:0 for i in range(numActives)}
	rusheeDoubleSlots = { i:0 for i in range(numRushees)}

	# timetable structure: rows = actives, columns = timeslots
	timetable = [[[] for a in range(numSlots)] for b in range(numActives)]

	# keep track of which rushees still need to be scheduled
	todoRushees = list(range(numRushees))
	comebacktoRushees = [] # sometimes we'll have to skip a rushee for a target score

	# go thru match scores in descending order
	for targetScore in matchScores:
		# print("\nTARGET SCORE = {}\n===================".format(targetScore))
		
		todoRushees = todoRushees + comebacktoRushees
		comebacktoRushees = []

		# while there's still rushees to schedule and the target score is still in the matrix
		while len(rusheeTimeslots) > 0 and targetScore in trialMatrix and len(todoRushees) > 0: 
	
			# choose a rushee at random, find all actives with the target match score
			rusheeId = random.choice(todoRushees)
			targetActiveIds = [activeId for activeId, score in enumerate(trialMatrix[rusheeId]) if score == targetScore]
			print("- rushee {} ({}), targetActiveIds={}, available={}".format(rusheeId, rusheeIdMap[rusheeId], targetActiveIds, rusheeTimeslots[rusheeId]))

			if len(targetActiveIds) == 0:
				comebacktoRushees.append(rusheeId)
				todoRushees.remove(rusheeId)
				continue # if this rushee has no actives at this target score, skip and come back for lower target score

			activeId = random.choice(targetActiveIds)
			print("  trying active {} ({}), current schedule = {}".format(activeId, activeIdMap[activeId], timetable[activeId]))
			scheduled = False

			# try to find a timeslot that the rushee and active have available 
			for slot in rusheeTimeslots[rusheeId]:
			
				if len(timetable[activeId][slot]) < 2:

					# if this would be a double slot, check to see if it doesn't exceed max double slots
					if len(timetable[activeId][slot]) == 1 and (activeDoubleSlots[activeId] >= maxActiveDoubleSlots or rusheeDoubleSlots[rusheeIdMap[timetable[activeId][slot][0]]] > maxRusheeDoubleSlots or rusheeDoubleSlots[rusheeId] > maxRusheeDoubleSlots):
						continue

					# found a slot! add it to timetable, update the matchscore
					timetable[activeId][slot].extend(rusheeIdMap[rusheeId])
					trialMatrix[rusheeId][activeId] = 6
					timetableScoreTotal += targetScore
					scheduled = True
					print("  success!!! new schedule = {}".format(timetable[activeId]))

					# mark double slot if needed
					if len(timetable[activeId][slot]) == 2:
						activeDoubleSlots[activeId] += 1
						rusheeDoubleSlots[rusheeIdMap[timetable[activeId][slot][0]]] += 1
						rusheeDoubleSlots[rusheeId] += 1

					# remove slot for the rushee
					rusheeTimeslots[rusheeId].remove(slot)
					if len(rusheeTimeslots[rusheeId]) == 0:
						rusheeTimeslots.pop(rusheeId)
						todoRushees.remove(rusheeId)

					break

			if scheduled == False:
				trialMatrix[rusheeId][activeId] = 0
				# print("  failed :(")

		# print("rusheeTimeslots: {}\ntodoRushees: {}\ncomebacktoRushees: {}\n".format(rusheeTimeslots, todoRushees, comebacktoRushees))

	# print(rusheeTimeslots)
	timetableScoreTotal -= (25 * len(rusheeTimeslots))
	for row in timetable:
		for col in row:
			if len(col) == 0:
				timetableScoreTotal -= 15

	return (timetableScoreTotal, timetable, rusheeTimeslots)

	


# populate matchScoreMatrix with rushee preferences
with open('rusheeResponses.tsv', 'r') as csvfile:
	rusheeReader = csv.reader(csvfile, delimiter='\t')
	next(rusheeReader) # first row is header
	# numRushees = len(list(rusheeReader)) - 1
	i = -1

	for rusheeRow in rusheeReader:
		# first row of the form responses should just be a dummy response that includes every active 
		if i == -1:
			activeList = rusheeRow[1].split(", ")
			numActives = len(activeList)
			for j, active in enumerate(activeList):
				activeIdMap[active] = j
				activeIdMap[j] = active
				activeMatchCounts[active] = { s:0 for s in matchScores}

			i += 1
			continue

		matchScoreMatrix.append([3 for a in range(numActives)])
		rusheeIdMap[rusheeRow[0]] = i
		rusheeIdMap[i] = [rusheeRow[0]]
		yesActives = rusheeRow[1].split(", ")
		noActives = rusheeRow[2].split(", ")

		if len(yesActives) > 0 and yesActives[0] != "":
			for active in yesActives:
				activeId = activeIdMap[active]
				matchScoreMatrix[i][activeId] += 1

		if len(noActives) > 0 and noActives[0] != "":
			for active in noActives:
				activeId = activeIdMap[active]
				matchScoreMatrix[i][activeId] -= 1

		i += 1
		numRushees += 1

# populate matchScoreMatrix with active preferences
with open('activeResponses.tsv', 'r') as csvfile:
	activeReader = csv.reader(csvfile, delimiter='\t')
	next(activeReader) # first row is header

	for activeRow in activeReader:

		activeId = activeIdMap[activeRow[0]]
		yesRushees = activeRow[1].split(", ")
		noRushees = activeRow[2].split(", ")
		# timeslots = activeRow[3].split(", ")

		if len(yesRushees) > 0 and yesRushees[0] != "":
			for rushee in yesRushees:
				rusheeId = rusheeIdMap[rushee]
				matchScoreMatrix[rusheeId][activeId] += 1

		if len(noRushees) > 0 and noRushees[0] != "":
			for rushee in noRushees:
				rusheeId = rusheeIdMap[rushee]
				matchScoreMatrix[rusheeId][activeId] -= 1


# so now we have a 2D matrix with...
# 	* rows = rushees
# 	* columns = actives
# 	* cell = match score (1 to 5)
# print(np.matrix(matchScoreMatrix))
matchScoreMatrix = np.array(matchScoreMatrix)

# maxActiveDoubleSlots = (numRushees % numActives) * numSlots / numActives
# maxRusheeDoubleSlots = (numRushees % numActives) * numSlots / numRushees + 1
maxActiveDoubleSlots = 1
maxRusheeDoubleSlots = 1

bestTimetable = None
bestScore = -1
bestRusheeTimeslots = None

# the name of the game: randomize & optimize >:)
for n in range(100):

	trialMatrix = copy.deepcopy(matchScoreMatrix)
	timetableScore, timetable, rusheeTimeslots = timetableTrial(trialMatrix)
	if timetableScore > bestScore:
		bestTimetable = timetable
		bestScore = timetableScore
		bestRusheeTimeslots = rusheeTimeslots

	print("timetableScore={}, new bestScore={}".format(timetableScore, bestScore))

# bestTimetable = pandas.DataFrame(bestTimetable)

print("\n\nbestScore = {}".format(bestScore))
for rusheeId, slots in rusheeTimeslots.items():
	print("unscheduled rusheeId={}: {}".format(rusheeIdMap[rusheeId], slots))
# for row in bestTimetable:
# 	print(row)

activeNames = [name for name in activeIdMap if isinstance(name, str)]
rusheeNames = [name for name in rusheeIdMap if isinstance(name, str)]

def timetableForActives(timetable):
	for activeId, row in enumerate(timetable):
		print("\n{}'s coffee chats...".format(activeIdMap[activeId]))
		for i, slot in enumerate(row):
			print("{}: {}".format(timeslotStrs[i], " & ".join(slot)))

timetableForActives(bestTimetable)


