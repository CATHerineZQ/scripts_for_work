import os
import re
import sys
import time

# return a list of info that will be use to loop over data later on
def generate_hpbatch(original_data1, original_data2, pushTo_date):

	#print original_data1, original_data2, pushTo_date

	uniq = 0

	returnlst = []
	dates = []
	
	for root, dirs, files in os.walk("/usr/local/load/ngcc/BC"):
	 	for file in files:
	 		#looking for files in format: hd_account_xxxxxxxxxxxxxx(14 digits)
	 		p1 = re.compile("hd_account_[0-9]{14}$")
	 		if p1.match(file) != None:
	 			#print "=======", file  # tested, got the coorect files
	 			#print "====ROOT====:", root
	 			dates.append(int(file[-14:]))


	filepath = "/usr/local/load/ngcc/BC/hd_account_" + str(max(dates))

	fd = open(filepath, "r")
	for line in fd:
		splited_line = line.split(",")

		#print len(splited_line), splited_line  # tested, all have length of 34
		if len(splited_line) == 34:
		    if (((splited_line[12] == original_data1) or (splited_line[12] == original_data2)) and (splited_line[8] == "2" or splited_line[8] == "3") and (splited_line[0] == "BellMobility" or splited_line[0] == "PCMobile")):
		    #if splited_line[0] == "BellMobility" or splited_line[0] == "PCMobile":  # ====================== FOR TESTING ======================
		    	# create uniq time string for column 8
		    	timestr = time.strftime("%y%m%d%H%M%S")
		    	uniq_str = timestr + "_" + str(uniq)
		    	uniq += 1
		    	# sunday = 0, monday = 1, tuesday = 2, wednesday = 3, thursday = 4, friday = 5, saturday = 6 
		    	push_days = "340" # set push_days var, set: Running this script on Thursday and push_days is 5 as default 
		    	# if time.strftime("%w") == "4":  #Thursday
		    	# 	push_days = "5"
		    	# if time.strftime("%w") == "5":  #Friday
		    	# 	push_days = "4"

		    	if splited_line[0] == "BellMobility":
		    		brand = "1"
		    		inactive_days = "120"
		    	if splited_line[0] == "PCMobile":
		    		brand = "5"
		    		inactive_days = "240"

		    	appendline = "RequestPaymentReload_v3|" + brand + "|3|1|" + splited_line[2] + "|0|RST|" + uniq_str + "|" + push_days + "|" + inactive_days + "|PPDOPS|NM1 MTC Topup"
		    	# print ">>>>>>>>>>>", appendline
		    	returnlst.append(appendline)
	fd.close()

	return returnlst

if __name__ == "__main__":

	print "Please make sure you are logged on with username reporting."
	original_data1 = raw_input("Please input 1st date in formate DD/MM/YYYY: ")
	original_data2 = raw_input("Please input 2st date in formate DD/MM/YYYY: ")
	pushTo_date = raw_input("Please input the date will be pushed to in formate DD/MM/YYYY: ")
	print "All 3 dates are recived. Generateing hpbatch file... ... "

	lines = generate_hpbatch(original_data1, original_data2, pushTo_date)
	# print lines  # tested, checking format
	print "***hpbatch file is generated successfully"

	print "Writing DAT file ... ..."
	# path = "/tmp/nm1_contingency.20170209.hpbatch_final.DAT"
	timestr = time.strftime("%y%m%d")
	tmp_path = "/tmp/nm1_contingency." + timestr + ".DAT"
	fd = open(tmp_path, "w")
	fd.write("PPDOps\n")
	# fd = open("/home/czhou/T2-pushExpiryDate/try.DAT", "w")  # the path for testing
	for line in lines:
		fd.write(line + "\n")
	fd.write("T" + str(len(lines)))
	fd.close()
	print "***DAT file is written successfully"

    # uncomment following while excute the script for perventing wrong trigger
    #########################################################################################################
	# shell_command = "scp " + tmp_path + " ppmadm@172.25.200.101:/var/opt/SIU/PPM/Batch/Input/BellMobility"
	# os.system(shell_command)
	#########################################################################################################

	print "finished sending the file: nm1_contingency." + timestr + ".DAT"
