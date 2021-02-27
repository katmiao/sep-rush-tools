import csv
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(linewidth=2000) 

matchScoreMatrix = []
activeIdMap = {}
rusheeIdMap = {}
activeMatchCounts = {}
numRushees = -1
numActives = -1
matchScores = [2, 1, 0, -1, -2]

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
				activeMatchCounts[active] = {2:0, 1:0, 0:0, -1:0, -2:0}

			# matchScoreMatrix = [[0 for a in range(numActives)] for b in range(numRushees)]
			# matchScoreMatrix = [[0] * numActives] * numRushees
			i += 1
			continue

		matchScoreMatrix.append([0 for a in range(numActives)])
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
# 	* cell = match score (-2 to 2)
print(np.matrix(matchScoreMatrix))

# count up the match scores for each active
for i, row in enumerate(matchScoreMatrix):
	for j, col in enumerate(row):
		activeMatchCounts[activeIdMap[j]][col] += 1
print(activeMatchCounts)


timetable = [[""] * 4] * numRushees

























