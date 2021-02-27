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
numActives = -1
matchScores = [4, 3, 2, 1]

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
				activeMatchCounts[active] = {4:0, 3:0, 2:0, 1:0, 0:0}

			# matchScoreMatrix = [[0 for a in range(numActives)] for b in range(numRushees)]
			# matchScoreMatrix = [[0] * numActives] * numRushees
			i += 1
			continue

		matchScoreMatrix.append([2 for a in range(numActives)])
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
# 	* cell = match score (0 to 4)
# print(np.matrix(matchScoreMatrix))

matchScoreMatrix = np.array(matchScoreMatrix)

# count up the match scores for each active
for i, row in enumerate(matchScoreMatrix):
	for j, col in enumerate(row):
		activeMatchCounts[activeIdMap[j]][col] += 1
# print(activeMatchCounts)


bestTimetable = None
bestMatchScore = -1

# the name of the game: randomize & optimize >:)
for n in range(1):

	rusheeTimeslots = {}
	for i in range(numRushees):
		shuffledSlots = [0, 1, 2, 3]
		random.shuffle(shuffledSlots)
		rusheeTimeslots[i] = shuffledSlots

	# rows = actives, columns = timeslots
	timetable = [[[] for a in range(4)] for b in range(numActives)]

	# pick a random order to give 2-matches
	randomRusheeOrder = list(range(numRushees))
	random.shuffle(randomRusheeOrder)

	# # assign as many 2-matches as possible 
	# while len(randomRusheeOrder) > 0:
	# 	rusheeId = randomRusheeOrder.pop()
	# 	if len(rusheeTimeslots[rusheeId]) > 0:
	# 		slot = rusheeTimeslots[rusheeId].pop()
	# 		if len(rusheeTimeslots[rusheeId]) == 0:
	# 			rusheeTimeslots.pop(rusheeId)
	# 		print("processing rusheeId={} for slot={}".format(rusheeId, slot))

	# 		for activeId, score in enumerate(matchScoreMatrix[rusheeId]):
	# 			if score == 2:
	# 				if len(timetable[activeId][slot]) < 2:
	# 					timetable[activeId][slot].append(rusheeIdMap[rusheeId])
					
	# for row in timetable:
	# 	print(row)

	# # assign 1-matches and 0-matches for the remaining slots
	# while len(rusheeTimeslots) > 0:
	# 	rusheeId = np.randint(0, numRushees)
	# 	for activeId, score in enumerate(matchScoreMatrix[rusheeId]):
	# 		if score == 1: 





	# trying something!!!!!!!!!!!!!!
	todoRushees = list(range(numRushees))
	comebacktoRushees = []
	timetableScoreTotal = 0

	# go thru match scores in descending order
	for targetScore in matchScores:
		print("\n\n\nlen(rusheeTimeslots)={}, targetScore={}".format(len(rusheeTimeslots), targetScore))
		todoRushees = todoRushees + comebacktoRushees
		comebacktoRushees = []

		# while there's still rushees to schedule and the target score is still in the matrix
		while len(rusheeTimeslots) > 0 and targetScore in matchScoreMatrix and len(todoRushees) > 0: 

			# print(matchScoreMatrix)
	
			# choose a rushee at random, find all actives with the target match score
			rusheeId = random.choice(todoRushees)
			print("-chose {}, {}, row={}".format(rusheeId, rusheeIdMap[rusheeId], matchScoreMatrix[rusheeId]))
			targetActiveIds = [activeId for activeId, score in enumerate(matchScoreMatrix[rusheeId]) if score == targetScore]
			print("rusheeId={}, targetActiveIds={}".format(rusheeId, targetActiveIds))
			if len(targetActiveIds) == 0:
				comebacktoRushees.append(rusheeId)
				todoRushees.remove(rusheeId)
				continue # if this rushee has no actives at this target score, skip

			
			activeId = random.choice(targetActiveIds)

			scheduled = False

			# try to find a timeslot that the rushee and active have available 
			for slot in rusheeTimeslots[rusheeId]:
			
				if len(timetable[activeId][slot]) < 2:
					# found a slot! add it to timetable, update the matchscore, remove that slot for the rushee
					print("   scheduling rusheeId={} for activeId={} at slot={}".format(rusheeId, activeId, slot))
					timetable[activeId][slot].extend(rusheeIdMap[rusheeId])
					matchScoreMatrix[rusheeId][activeId] = 5
					timetableScoreTotal += targetScore
					scheduled = True
					rusheeTimeslots[rusheeId].remove(slot)
					if len(rusheeTimeslots[rusheeId]) == 0:
						rusheeTimeslots.pop(rusheeId)
						todoRushees.remove(rusheeId)
					break

			if scheduled == False:
				matchScoreMatrix[rusheeId][activeId] = -5

	for row in timetable:
		print(row)














