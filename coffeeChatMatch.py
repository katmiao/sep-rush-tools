import csv
import random
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(linewidth=2000) 

matchScoreMatrix = []
activeIdMap = {}
rusheeIdMap = {}
activeMatchCounts = {}
numRushees = 0
numActives = 0
matchScores = [5, 4, 3, 2, 1]
numSlots = 4
timeslotStrs = ["7:00-7:30PM", "7:30-8:00PM", "8:00-8:30PM", "8:30-9:00PM"]

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

		for active in yesActives:
			activeId = activeIdMap[active]
			matchScoreMatrix[i][activeId] += 1

		for active in noActives:
			if active == "":
				break
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

		for rushee in yesRushees:
			rusheeId = rusheeIdMap[rushee]
			matchScoreMatrix[rusheeId][activeId] += 1

		for rushee in noRushees:
			if rushee == "":
				break
			rusheeId = rusheeIdMap[rushee]
			matchScoreMatrix[rusheeId][activeId] -= 1


# so now we have a 2D matrix with...
# 	* rows = rushees
# 	* columns = actives
# 	* cell = match score (1 to 5)
# print(np.matrix(matchScoreMatrix))
matchScoreMatrix = np.array(matchScoreMatrix)

maxActiveDoubleSlots = (numRushees % numActives) * numSlots / numActives
maxRusheeDoubleSlots = (numRushees % numActives) * numSlots / numRushees

bestTimetable = None
bestScore = -1

# the name of the game: randomize & optimize >:)
for n in range(10):

	# reset everything for this trial
	trialMatrix = matchScoreMatrix
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
	timetable = [[[] for a in range(4)] for b in range(numActives)]

	# keep track of which rushees still need to be scheduled
	todoRushees = list(range(numRushees))
	comebacktoRushees = [] # sometimes we'll have to skip a rushee for a target score

	# go thru match scores in descending order
	for targetScore in matchScores:
		print("\nTARGET SCORE = {}\n===================".format(targetScore))
		
		todoRushees = todoRushees + comebacktoRushees
		comebacktoRushees = []

		# while there's still rushees to schedule and the target score is still in the matrix
		while len(rusheeTimeslots) > 0 and targetScore in trialMatrix and len(todoRushees) > 0: 
	
			# choose a rushee at random, find all actives with the target match score
			rusheeId = random.choice(todoRushees)
			targetActiveIds = [activeId for activeId, score in enumerate(trialMatrix[rusheeId]) if score == targetScore]
			print("- rushee {} ({}), targetActiveIds={}".format(rusheeId, rusheeIdMap[rusheeId], targetActiveIds))

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
					trialMatrix[rusheeId][activeId] = 0
					timetableScoreTotal += targetScore
					scheduled = True
					print("  success!!! new schedule = {}".format(timetable[activeId]))

					# mark double slot if needed
					if len(timetable[activeId][slot]) == 2:
						activeDoubleSlots[activeId] += 1
						# OOOOOOOOO 
						rusheeDoubleSlots[rusheeId] += 1

					# remove slot for the rushee
					rusheeTimeslots[rusheeId].remove(slot)
					if len(rusheeTimeslots[rusheeId]) == 0:
						rusheeTimeslots.pop(rusheeId)
						todoRushees.remove(rusheeId)

					break

			if scheduled == False:
				trialMatrix[rusheeId][activeId] = 0
				print("  failed :(")

	# for row in timetable:
	# 	print(row)

	if timetableScoreTotal > bestScore:
		bestTimetable = timetable
		bestScore = timetableScoreTotal

	print("\ntimetableScoreTotal={}, new bestScore={}\n\n".format(timetableScoreTotal, bestScore))




print("bestScore = {}".format(bestScore))
for row in bestTimetable:
	print(row)


def timetableForActives(timetable):
	for activeId, row in enumerate(timetable):
		print("\n{}'s coffee chats...".format(activeIdMap[activeId]))
		for i, slot in enumerate(row):
			print("{}: {}".format(timeslotStrs[i], " & ".join(slot)))

timetableForActives(bestTimetable)


