import os
import re
import sys
import time




def extract_from_csv(csv_src_path):
	lines = []
	tosplit = []
	fd = open(csv_src_path)
	for line in fd:
		tosplit.append(line.split("\r"))
	fd.close()

	for line in tosplit:
		line = line[0].split(",")
		#print "=================", line
		if (len(line) >= 10) and (line[6].strip() != ""):
			lines.append(line)

	return lines

def weedkend_call(info):

	lines = []

	for line in info:
		if line[9].strip() == "BellMobility":
			br = "1"
		else:
			br = "5"

		strline = "RequestPaymentReload_v3|" + br + "|3|1|" + line[2] + "|" + str(int(line[6])*(100)) + "|RST||||PPDOps|NM1_contingency"

		lines.append(strline)

	# strline = "RequestPaymentReload_v3|"&IF(J2="BellMobility",1,5)&"|3|1|"&C2&"|"&G2*100&"|RST||||PPDOps|NM1_contingency"

	return lines

def monday_call(info):

	lines = []

	for line in info:
		if line[9].strip() == "BellMobility":
			br = "1"
		else:
			br = "5"

		strline = "RequestAdjustment|" + br + "|3|1|" + line[2] + "|" + str(int(line[6])*(-100)) + "|0|PRPR||PPDOps|NM1_contingency"

		lines.append(strline)

	# strline = "RequestAdjustment|"&IF(J2="BellMobility",1,5)&"|3|1|"&C2&"|"&-G2*100&"|0|PRPR||PPDOps|NM1_contingency_02142017"

	return lines


if __name__ == "__main__":

	
	day = raw_input("The CSV file(s) is for Saturday/Sunday/Monday. Please Enter: ")

	######## FOR TESTING ###########
	# csvfile = "try.csv"
	# day = "Saturday"
	################################

	if day == "Monday":
		csvfile_saturday = raw_input("Please input the absolute path of Saturday csv file: ")
		csvfile_sunday = raw_input("Please input the absolute path of Sunday csv file: ")
		print "Extracting information from CSV file... ..."
		info_saturday = extract_from_csv(csvfile_saturday)
		info_sunday = extract_from_csv(csvfile_sunday)

		info = [] + info_saturday + info_sunday


		lines = monday_call(info)

	elif  day == "Saturday" or day == "Sunday":
		csvfile = raw_input("Please input the absolute path of the csv file: ")
		print "Extracting information from CSV file... ..."
		info = extract_from_csv(csvfile)

		lines = weedkend_call(info)


	print "Writing DAT file... ..."
	timestr = time.strftime("%y%m%d")
	new_path = day + "-" + timestr + ".DAT"
	fd = open(new_path, "w")
	fd.write("PPDOps\n")
	for line in lines:
		fd.write(line + "\n")
	fd.write("T" + str(len(lines)) + "\n")
	fd.close()
	print "***DAT file is written successfully"

	# uncomment following while excute the script for perventing wrong trigger
	# not confirmed path below
    #########################################################################################################
	shell_command = "scp " + new_path + " ppmadm@172.25.200.101:/var/opt/SIU/PPM/Batch/Input/BellMobility"
	os.system(shell_command)
	#########################################################################################################

	print "finished sending the file: " + new_path