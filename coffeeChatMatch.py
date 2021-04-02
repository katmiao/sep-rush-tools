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
activeUnavailability = {}
rusheeUnavailability = {}
activeMatchCounts = {}
numRushees = 0
numActives = 0
matchScores = [5, 4, 3, 2, 1]
numSlots = 6
timeslotStrs = ["7:00-7:20PM", "7:20-7:40PM", "7:40-8:00PM", "8:00-8:20PM", "8:20-8:40PM", "8:40-9:00PM", ]

def timetableTrial(trialMatrix):
	# reset everything for this trial
	timetableScoreTotal = 0
	matchscoreStats = {5:0, 4:0, 3:0, 2:0, 1:0}
	chatCount = 0

	# keep dict of arrays of timeslots each rushees must still be scheduled for
	rusheeTimeslots = {}
	for i in range(numRushees):
		shuffledSlots = [j for j in range(numSlots)]
		random.shuffle(shuffledSlots) 
		rusheeTimeslots[i] = shuffledSlots
	for rusheeId, unavailableSlots in rusheeUnavailability.items():
		for slot in unavailableSlots:
			rusheeTimeslots[rusheeId].remove(slot)

	# keep track of how many double slots each active/rushee has
	activeDoubleSlots = { i:0 for i in range(numActives)}
	rusheeDoubleSlots = { i:0 for i in range(numRushees)}

	# timetable structure: rows = actives, columns = timeslots
	timetable = [[[] for a in range(numSlots)] for b in range(numActives)]
	for activeId, unavailableSlots in activeUnavailability.items():
		for slot in unavailableSlots:
			timetable[activeId][slot].extend("x")

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
			# print("- rushee {} ({}), targetActiveIds={}, available={}".format(rusheeId, rusheeIdMap[rusheeId], targetActiveIds, rusheeTimeslots[rusheeId]))

			if len(targetActiveIds) == 0:
				comebacktoRushees.append(rusheeId)
				todoRushees.remove(rusheeId)
				continue # if this rushee has no actives at this target score, skip and come back for lower target score

			activeId = random.choice(targetActiveIds)
			# print("  trying active {} ({}), current schedule = {}".format(activeId, activeIdMap[activeId], timetable[activeId]))
			scheduled = False
			scheduledSlot = -1

			# try to find a timeslot that the rushee and active have available 
			for slot in rusheeTimeslots[rusheeId]:

				# actives may not be paired with more than 2 rushees at a time
				if len(timetable[activeId][slot]) < 2:

					# check if active is available
					if len(timetable[activeId][slot]) == 1 and timetable[activeId][slot][0] == 'x':
						continue

					# if this would be a double slot, check to see if it doesn't exceed max double slots
					if len(timetable[activeId][slot]) == 1 and (activeDoubleSlots[activeId] >= maxActiveDoubleSlots or rusheeDoubleSlots[rusheeIdMap[timetable[activeId][slot][0]]] > maxRusheeDoubleSlots or rusheeDoubleSlots[rusheeId] > maxRusheeDoubleSlots):
						continue

					# found a slot! add it to timetable, update the matchscore
					scheduledSlot = slot
					timetable[activeId][slot].extend(rusheeIdMap[rusheeId])
					trialMatrix[rusheeId][activeId] = 6
					timetableScoreTotal += targetScore
					matchscoreStats[targetScore] += 1
					chatCount += 1
					scheduled = True
					# print("  success!!! new schedule = {}".format(timetable[activeId]))

					# mark double slot if needed
					if len(timetable[activeId][slot]) == 2:
						activeDoubleSlots[activeId] += 1
						rusheeDoubleSlots[rusheeIdMap[timetable[activeId][slot][0]]] += 1
						rusheeDoubleSlots[rusheeId] += 1

					break

			if scheduled == True:
				# remove slot for the rushee
				rusheeTimeslots[rusheeId].remove(scheduledSlot)
				# print("removed {} for {}. remaining={}".format(scheduledSlot, rusheeIdMap[rusheeId], rusheeTimeslots[rusheeId]))
				if len(rusheeTimeslots[rusheeId]) == 0:
					rusheeTimeslots.pop(rusheeId)
					todoRushees.remove(rusheeId)

			if scheduled == False:
				trialMatrix[rusheeId][activeId] = 0
				# print("  failed :(")

		# print("rusheeTimeslots: {}\ntodoRushees: {}\ncomebacktoRushees: {}\n".format(rusheeTimeslots, todoRushees, comebacktoRushees))

	# deduct 25 points for every empty rushee slot, deduct 15 points for every empty active slot
	timetableScoreTotal -= (25 * len(rusheeTimeslots))
	for row in timetable:
		for col in row:
			if len(col) == 0:
				timetableScoreTotal -= 15

	# returns:
	# 1) final score for timetable
	# 2) the timetable itself
	# 3) the unscheduled rushee slots
	# 4) the matchscore stats (count for each matchscore)
	# 5) the avg matchscore
	print(chatCount)
	return (timetableScoreTotal, timetable, rusheeTimeslots, matchscoreStats, timetableScoreTotal/float(chatCount))

	


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

# process active availability
with open('activeAvailability.tsv', 'r') as csvfile:
	activeReader = csv.reader(csvfile, delimiter='\t')
	next(activeReader) # first row is header

	for activeRow in activeReader:

		activeId = activeIdMap[activeRow[0]]
		unavailableSlots = activeRow[1].split(", ")
		activeUnavailability[activeId] = []

		if len(unavailableSlots) > 0 and unavailableSlots[0] != "":
			for slot in unavailableSlots:
				slotNum = int(slot)
				activeUnavailability[activeId].append(slotNum)
				
print("activeUnavailability = {}".format(activeUnavailability))

# process rushee availability
with open('rusheeAvailability.tsv', 'r') as csvfile:
	rusheeReader = csv.reader(csvfile, delimiter='\t')
	next(rusheeReader) # first row is header

	for rusheeRow in rusheeReader:

		rusheeId = rusheeIdMap[rusheeRow[0]]
		unavailableSlots = rusheeRow[1].split(", ")
		rusheeUnavailability[rusheeId] = []

		if len(unavailableSlots) > 0 and unavailableSlots[0] != "":
			for slot in unavailableSlots:
				slotNum = int(slot)
				rusheeUnavailability[rusheeId].append(slotNum)
				
print("rusheeUnavailability = {}".format(rusheeUnavailability))


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
for n in range(1000):
	print("\nTRIAL #{}".format(n))
	trialMatrix = copy.deepcopy(matchScoreMatrix)
	timetableScore, timetable, rusheeTimeslots, matchscoreStats, matchscoreAvg = timetableTrial(trialMatrix)
	if timetableScore > bestScore:
		bestTimetable = timetable
		bestScore = timetableScore
		bestRusheeTimeslots = rusheeTimeslots
		bestMatchscoreStats = matchscoreStats
		bestMatchscoreAvg = matchscoreAvg

	print("timetableScore={}, new bestScore={}".format(timetableScore, bestScore))

print("\n\nbestScore = {}".format(bestScore))
for rusheeId, slots in bestRusheeTimeslots.items():
	print("unscheduled rusheeId={}: {}".format(rusheeIdMap[rusheeId], slots))
print("bestMatchscoreStats = {}".format(bestMatchscoreStats))
print("bestMatchscoreAvg = {}".format(bestMatchscoreAvg))
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


