#= Catherine(Quan) Zhou 2018 Nov. =#
import os
import sys
import xlrd
import time
import string
import win32com
import win32com.client
from urllib.parse import urlsplit
from openpyxl import load_workbook
import datetime
import openpyxl
import codecs
from shutil import copyfile

outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
ppdeng = outlook.Folders("ppdeng")
# this is version 3.6 32-bits window 10 system

DIRPATH = "CSP_results_"+time.strftime("%Y%m%d")

### ========================================================================================= ###
###                          L O C A L   D A T A   (WRITE DICTIONARY)                         ###
### ========================================================================================= ###

def writeDict2file(filename, dataDict):
	fd = open(filename, "w")
	allkeys = dataDict.keys()
	for k in allkeys:
		# print(k)
		fd.write(k + " " + dataDict.get(k, "-Not Found-")[0] + " " + dataDict.get(k, "-Not Found-")[1] + "\n")
	fd.close()

def writeHis2ile(workbook, row):
	strline = ""
	for i in range(7):
		strline += str(row[i].value)+","

	strline += str(int(row[7].value))+","
	strline += str(row[8].value)+","
	strline += str(int(row[9].value))+","
	strline += str(int(row[10].value))+","
	strline += str(row[11].value)+","

	py_date = xlrd.xldate.xldate_as_datetime(row[12].value, workbook.datemode)
	strline += str(py_date)+","

	for i in range(13, 21):
		strline += str(row[i].value)+","

	strline = strline[:-1] + "\n"
	with codecs.open("SMS_SPECIAL_NUMBER_CURRENT.txt",'a+',encoding='utf8') as fd:
		fd.write(strline)

def readingxlsx():
	workbook = xlrd.open_workbook('UpToDate_BPT.xlsx') # the existing xlsx file 
	worksheet = workbook.sheet_by_name('Special Number')
	# first_row = worksheet.row(4293) # 4294 line starting effective info
	last_idx = worksheet.nrows - 1
	# first_idx = 8

	for idx in range(4293, worksheet.nrows):
		writeHis2ile(workbook, worksheet.row(idx))

### ========================================================================================= ###
###                          L O C A L   D A T A   (READ  DICTIONARY)                         ###
### ========================================================================================= ###

def read_historytxt():
	fd_history = open("SMS_SPECIAL_NUMBER_CURRENT.txt", "r")

	stored_entries = []
	billingID_search = {"Bell_Pre":{}, "Virgin_Pre":{}}

	for line in fd_history:
		cleaned = [i.strip() for i in line.strip().split(",")]
		stored_entries.append(cleaned)
		thirdpram = cleaned[3].split()
		if len(thirdpram) == 2:
			[brandName, billingID] = thirdpram
			billingID_search[brandName][billingID] = [cleaned[14], cleaned[18]]

	fd_history.close()

	return billingID_search, stored_entries

def checkBillingID(billingID_search, billingID):
	bell_billingIDs = billingID_search["Bell_Pre"].keys()
	virgin_billingIDs = billingID_search["Virgin_Pre"].keys()

	flag_bell = billingID in bell_billingIDs
	flag_virgin = billingID in virgin_billingIDs
	
	brandInd = -1
	if (flag_bell == True and flag_virgin == True) or (flag_bell == False and flag_virgin == False):
		# raise attention for manual interrupt
		brandInd = -1
	else:
		if flag_bell == True and flag_virgin == False:
			# it is bell billing ID
			brandInd = 0 # 0 is for Pre_Bell
		elif flag_virgin == True and flag_bell == False:
			# it is virgin billing ID
			brandInd = 1 # 1 is for Pre_Virgin

	return brandInd

### ========================================================================================= ###
###                            E M A I L                                                      ###
### ========================================================================================= ###


def readingEmail():
	inbox = ppdeng.Folders("Inbox")
	messages = inbox.Items

	toConfigureLst, toRemoveLst, toUpdateLst = [], [], []
	toConfigure = "Request notification - State set to \"To Configure\"  And Launch date is"
	toRemove = "Request notification - State set to \"To Remove\"  And Remove date set to"
	toUpdate = "Request notification - State set to \"To Update\"  for"

	# It will sort in the opposite direction: ascending order, from the oldest to the most recent.
	messages.Sort("[ReceivedTime]", False)
	timelst = []
	for message in messages:
		if message.unread == True:
			recievingtime = message.ReceivedTime.strftime("%Y%m%d %H:%M")
			timelst.append(recievingtime)

			if toConfigure in message.subject:
				toConfigureLst.append([message.body, recievingtime])
				message.unread = False # to mark email to READ

			elif toRemove in message.subject:
				toRemoveLst.append([message.body, recievingtime])
				message.unread = False # to mark email to READ

			elif toUpdate in message.subject:
				toUpdateLst.append([message.body, recievingtime])
				message.unread = False # to mark email to READ

	return toConfigureLst, toRemoveLst, toUpdateLst, timelst


### ========================================================================================= ###
###                            D O   A C T I O N S                                            ###
### ========================================================================================= ###

# ------------------------------------ H E L P E R S ---------------------------------------- #

def cleanMessage(messagelst):

	splitedLines = [line.strip() for line in messagelst[0].splitlines()]

	messageSplited = []
	for line in splitedLines:
		messageSplited.extend(line.split("\t"))

	cleanedLst = list(filter(None, messageSplited))
	# print(cleanedLst)

	for i in cleanedLst:
		if "For involved application details" in i:
			lnk = i[i.index("<")+1: -1]

	tableIdx = cleanedLst.index("Bundle")
	typeName_MO, typeName_MT = cleanedLst[tableIdx+1], cleanedLst[tableIdx+11]
	shortCode = cleanedLst[tableIdx+2] # == cleanedLst[tableIdx+12]
	billingID_MO, billingID_MT = cleanedLst[tableIdx+6].replace(" ", ""), cleanedLst[tableIdx+16].replace(" ", "")
	alwaysAllowed_MO, alwaysAllowed_MT = cleanedLst[tableIdx+9], cleanedLst[tableIdx+19]
	inBundle_MO, inBundle_MT = cleanedLst[tableIdx+10], cleanedLst[tableIdx+20]

	# to fix the error caused by mixed orders
	if typeName_MO.strip() == "MT" and typeName_MT.strip() == "MO":
		tempMT, tempMO = typeName_MO, typeName_MT
		typeName_MO, typeName_MT = tempMO, tempMT
		tempMT, tempMO = billingID_MO, billingID_MT
		billingID_MO, billingID_MT = tempMO, tempMT
		tempMT, tempMO = alwaysAllowed_MO, alwaysAllowed_MT
		alwaysAllowed_MO, alwaysAllowed_MT = tempMO, tempMT
		tempMT, tempMO = inBundle_MO, inBundle_MT
		inBundle_MO, inBundle_MT = tempMO, tempMT

	findTitleIdx = cleanedLst.index("Application Name:")
	detailName = cleanedLst[findTitleIdx+1].strip()

	tableInfo = [typeName_MO, typeName_MT, shortCode, billingID_MO, billingID_MT, alwaysAllowed_MO, alwaysAllowed_MT, inBundle_MO, inBundle_MT, detailName]
	activeCheck1, activeCheck2 = cleanedLst[tableIdx+3], cleanedLst[tableIdx+13]

	EMrecievingtime = messagelst[1]

	return tableInfo, activeCheck1, activeCheck2, EMrecievingtime

def makeShorter(newstring):

	intlst = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
	flag = 0

	while flag != 1:
		if newstring[-1] in intlst:
			newstring = newstring[:-1]
		else:
			flag = 1

	if len(newstring) > 40:
		newstring = newstring[:40]

	newstring = newstring.strip()

	return newstring

def reformDate(str):
	oldfull = str.strip().split()
	oldfront = oldfull[0].split("-")
	newfront = oldfront[1] + "/" + oldfront[2] + "/" + oldfront[0]

	newstring = newfront + " " + oldfull[1]
	return newstring

def buildEntry(inittype, tableInfo, billingID_search):

	[typeName_MO, typeName_MT, shortCode, billingID_MO, billingID_MT, alwaysAllowed_MO, alwaysAllowed_MT, inBundle_MO, inBundle_MT, detailName] = tableInfo

	# If the shortcode is a range of numbers, do it manually.
	if "-" in shortCode:
		return -1, -1

	brandInd_MO = checkBillingID(billingID_search, billingID_MO)
	brandInd_MT = checkBillingID(billingID_search, billingID_MT)

	if (brandInd_MO == 0) and (brandInd_MT == 0): # brand is Bell_Pre

		subBrand = "Bell_Pre"
	elif (brandInd_MO == 1) and (brandInd_MT == 1): # brand is Virgin_Pre

		subBrand = "Virgin_Pre"
	else: # brandInd == -1 OR brandInd == -1
		# DON'T KNOW THE BRAND
		return -1, -1


	########################################################################################################################################################
	timestr = time.strftime("%m/%d/%Y")

	description_MO = billingID_MO+" "+detailName
	description_MO = description_MO.replace("-", "").replace(";", "").replace(",", "").replace("  ", " ").replace("'", "''")
	if len(description_MO) > 40:
		description_MO = makeShorter(description_MO)

	description_MT = billingID_MT+" "+detailName
	description_MT = description_MT.replace("-", "").replace(";", "").replace(",", "").replace("  ", " ").replace("'", "''")
	if len(description_MT) > 40:
		description_MT = makeShorter(description_MT)

	########################################################################################################################################################
	
	datetimeobj = datetime.datetime.strptime(timestr+' 10:00:00', '%m/%d/%Y %H:%M:%S')

	entry_MO = [inittype, "", "Prod", subBrand+" "+billingID_MO, shortCode, subBrand, "0000000"+shortCode, "0", "SMSC", "3", "2", "P", datetimeobj, "N", billingID_search[subBrand][billingID_MO][0], "", "N", "N", billingID_search[subBrand][billingID_MO][1], "", description_MO]
	entry_MT = [inittype, "", "Prod", subBrand+" "+billingID_MT, shortCode, subBrand, billingID_MT[:2]+"12345"+shortCode, "0", "SMSC", "3", "1", "P", datetimeobj, "N", billingID_search[subBrand][billingID_MT][0], "", "N", "N", billingID_search[subBrand][billingID_MT][1], "", description_MT]

	return entry_MO, entry_MT

# -------------------------------- T o  C o n f i g u r e ---------------------------------- #
def doConfigure(toConfigureLst, billingID_search, fd_sql, stored_entries, local_stored):

	toConfigManualflag = False

	casecounter = 1
	timestr = time.strftime("%m/%d/%Y")
	# clean data
	for message in toConfigureLst:
		tableInfo, activeCheck1, activeCheck2, EMrecievingtime = cleanMessage(message)
		if activeCheck1 == "Active" and activeCheck2 == "Active":
			entry_MO, entry_MT = buildEntry("C.New", tableInfo, billingID_search)
			if (entry_MO == -1 and entry_MT == -1):
				toConfigManualflag = True
				unknowmessage = ["=========== Unrecognized Case "+str(casecounter)+" ================", "Recieved At: " + EMrecievingtime, tableInfo[-1], "short code: "+tableInfo[2], "Billing ID [MO/MT]: "+tableInfo[3] + "/"+ tableInfo[4], "=============================================="]
				casecounter += 1
				# fd_unknow = codecs.open(DIRPATH+"\\ToConfigure_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+", encoding='utf8')
				fd_unknow = open(DIRPATH+"\\ToConfigure_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+")
				for line in unknowmessage:
					fd_unknow.write(line+"\n")
				fd_unknow.close()
			else:
				entry_MO_found, entry_MT_found = None, None
				fg1, fg2 = 0, 0
				for entry in local_stored:
					if entry[0] == entry_MO[0] and entry[5] == entry_MO[5] and entry[6] == entry_MO[6]:
						fg1 = 1
					if entry[0] == entry_MT[0] and entry[5] == entry_MT[5] and entry[6] == entry_MT[6]:
						fg2 = 1
				if fg1 == 0 and fg2 == 0:
					for entry in stored_entries:
						if (entry[5] == entry_MO[5] and entry[6] == entry_MO[6]):
							entry_MO_found = entry
							stored_entries.remove(entry_MO_found)
							timestr = reformDate(entry_MO_found[12])
							date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"
							deldestr_MO = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MO[6]+"' and SUB_BRAND='"+entry_MO[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='2' and "+date_str+";\n"
							fd_sql.write(deldestr_MO)
					for entry in stored_entries:
						if (entry[5] == entry_MT[5] and entry[6] == entry_MT[6]):
							entry_MT_found = entry
							stored_entries.remove(entry_MT_found)
							timestr = reformDate(entry_MT_found[12])
							date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"
							deldestr_MT = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MT[6]+"' and SUB_BRAND='"+entry_MT[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='1' and "+date_str+";\n"
							fd_sql.write(deldestr_MT)

					timestr = time.strftime("%m/%d/%Y")
					todate_str = "TO_DATE('"+timestr+" 10:00:00', 'MM/DD/YYYY HH24:MI:SS')"
					line_MO = "Insert into PC3_SPECIAL_NUMBER (SUB_BRAND, SPECIAL_NUMBER, ROAMING_IND, CALL_SOURCE, SERVICE_TYPE, CALL_DIRECTION, FULL_OR_PREFIX_IND, EFFECTIVE_DATE, DROP_CALL_IND, SPECIAL_NUMBER_GROUP, AUTOMATICALLY_AUTHORIZED, BLACK_LISTED, AREA, DESCRIPTION)  Values ('"+entry_MO[5]+"', '"+entry_MO[6]+"', "+entry_MO[7]+", '"+entry_MO[8]+"', '"+entry_MO[9]+"', '"+entry_MO[10]+"', '"+entry_MO[11]+"', "+todate_str+", '"+entry_MO[13]+"', '"+entry_MO[14]+"', '"+entry_MO[16]+"', '"+entry_MO[17]+"', '"+entry_MO[18]+"', '"+entry_MO[20]+"');\n"
					line_MT = "Insert into PC3_SPECIAL_NUMBER (SUB_BRAND, SPECIAL_NUMBER, ROAMING_IND, CALL_SOURCE, SERVICE_TYPE, CALL_DIRECTION, FULL_OR_PREFIX_IND, EFFECTIVE_DATE, DROP_CALL_IND, SPECIAL_NUMBER_GROUP, AUTOMATICALLY_AUTHORIZED, BLACK_LISTED, AREA, DESCRIPTION)  Values ('"+entry_MT[5]+"', '"+entry_MT[6]+"', "+entry_MT[7]+", '"+entry_MT[8]+"', '"+entry_MT[9]+"', '"+entry_MT[10]+"', '"+entry_MT[11]+"', "+todate_str+", '"+entry_MT[13]+"', '"+entry_MT[14]+"', '"+entry_MT[16]+"', '"+entry_MT[17]+"', '"+entry_MT[18]+"', '"+entry_MT[20]+"');\n"
					fd_sql.write(line_MO)
					fd_sql.write(line_MT)
					stored_entries.append(["A.Final Loaded"]+entry_MO[1:])
					stored_entries.append(["A.Final Loaded"]+entry_MT[1:])
					local_stored.append(entry_MO)
					local_stored.append(entry_MT)

					# add history entries to the CSP_logfile.txt log file for the notifactions successfuly processed.
					# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
					fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
					line = "[" + message[1] + "]To Configure: <" + tableInfo[-1] + "> "
					fd_log.write(line + "\n")
					fd_log.close()
		else:
			i=0

	return stored_entries, local_stored, toConfigManualflag

# ---------------------------------- T o  R e m o v e -------------------------------------- #

def doRemove(toRemoveLst, billingID_search, fd_sql, stored_entries, local_stored):

	toRemoveManualflag = False

	# clean data
	for message in toRemoveLst:
		tableInfo, activeCheck1, activeCheck2, EMrecievingtime = cleanMessage(message)
		entry_MO, entry_MT = buildEntry("C.ToBeDeleted", tableInfo, billingID_search)

		if (entry_MO == -1 and entry_MT == -1):
			toRemoveManualflag = True
			timestr = time.strftime("%m/%d/%Y")
			unknowmessage = ["=========== Unrecognized Case "+str(casecounter)+" ================", "Recieved At: " + EMrecievingtime, tableInfo[-1], "short code: "+tableInfo[2], "Billing ID [MO/MT]: "+tableInfo[3] + "/"+ tableInfo[4], "=============================================="]
			casecounter += 1
			# fd_unknow = codecs.open(DIRPATH+"\\ToRemove_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+", encoding='utf8')
			fd_unknow = open(DIRPATH+"\\ToRemove_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+")
			for line in unknowmessage:
				fd_unknow.write(line+"\n")
			fd_unknow.close()
		else:
			entry_MO_found, entry_MT_found = None, None
			for entry in stored_entries:
				if (entry[5] == entry_MO[5] and entry[6] == entry_MO[6]):
					entry_MO_found = entry
					stored_entries.remove(entry_MO_found)
					timestr = reformDate(entry_MO_found[12])
					date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"
					deldestr_MO = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MO[6]+"' and SUB_BRAND='"+entry_MO[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='2' and "+date_str+";\n"
					fd_sql.write(deldestr_MO)

			for entry in stored_entries:
				if (entry[5] == entry_MT[5] and entry[6] == entry_MT[6]):
					entry_MT_found = entry
					stored_entries.remove(entry_MT_found)
					timestr = reformDate(entry_MT_found[12])
					date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"

					deldestr_MT = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MT[6]+"' and SUB_BRAND='"+entry_MT[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='1' and "+date_str+";\n"
					fd_sql.write(deldestr_MT)

			# add history entries to the CSP_logfile.txt log file for the notifactions successfuly processed.
			# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
			fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
			line = "[" + message[1] + "]To Remove: <" + tableInfo[-1] + "> "
			fd_log.write(line + "\n")
			fd_log.close()

	return stored_entries, local_stored, toRemoveManualflag

# ---------------------------------- T o  U p d a t e --------------------------------------- #

def doUpdate(toUpdateLst, billingID_search, fd_sql, stored_entries, local_stored):

	toUpdateManualflag = False

	# clean data
	for message in toUpdateLst:
		tableInfo, activeCheck1, activeCheck2, EMrecievingtime = cleanMessage(message)
		entry_MO, entry_MT = buildEntry("C.Modified", tableInfo, billingID_search)
		if (entry_MO == -1 and entry_MT == -1):
			toUpdateManualflag = True
			timestr = time.strftime("%m/%d/%Y")
			unknowmessage = ["=========== Unrecognized Case "+str(casecounter)+" ================", "Recieved At: " + EMrecievingtime, tableInfo[-1], "short code: "+tableInfo[2], "Billing ID [MO/MT]: "+tableInfo[3] + "/"+ tableInfo[4], "=============================================="]
			casecounter += 1
			# fd_unknow = codecs.open(DIRPATH+"\\ToUpdate_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+", encoding='utf8')
			fd_unknow = open(DIRPATH+"\\ToUpdate_Manualfile_"+time.strftime("%Y%m%d")+".txt", "a+")
			for line in unknowmessage:
				fd_unknow.write(line+"\n")
			fd_unknow.close()
		else:
			# delete existing entires
			entry_MO_found, entry_MT_found = None, None

			for entry in stored_entries:
				if (entry[5] == entry_MO[5] and entry[6] == entry_MO[6]):
					entry_MO_found = entry
					stored_entries.remove(entry_MO_found)
					timestr = reformDate(entry_MO_found[12])
					date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"
					deldestr_MO = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MO[6]+"' and SUB_BRAND='"+entry_MO[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='2' and "+date_str+";\n"
					fd_sql.write(deldestr_MO)
			for entry in stored_entries:
				if (entry[5] == entry_MT[5] and entry[6] == entry_MT[6]):
					entry_MT_found = entry
					stored_entries.remove(entry_MT_found)
					timestr = reformDate(entry_MT_found[12])
					date_str ="TO_CHAR(EFFECTIVE_DATE, 'MM/DD/YYYY HH24:MI:SS')= '"+timestr+"'"
					deldestr_MT = "delete from PC3_SPECIAL_NUMBER where SPECIAL_NUMBER='"+entry_MT[6]+"' and SUB_BRAND='"+entry_MT[5]+"' and ROAMING_IND=0 and CALL_SOURCE='SMSC' and SERVICE_TYPE='3' and CALL_DIRECTION='1' and "+date_str+";\n"
					fd_sql.write(deldestr_MT)

			# add history entries to the CSP_logfile.txt log file for the notifactions successfuly processed.
			# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
			fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
			line = "[" + message[1] + "]To Remove: <" + tableInfo[-1] + "> "
			fd_log.write(line + "\n")
			fd_log.close()

			# adding existing entires
			entry_MO_found, entry_MT_found = None, None
			flag11, flag22 = 0, 0
			for entry in stored_entries:
				if (entry[5] == entry_MO[5] and entry[6] == entry_MO[6]):
					flag11 = 1
				if (entry[5] == entry_MT[5] and entry[6] == entry_MT[6]):
					flag22 = 1
			timestr = time.strftime("%m/%d/%Y")
			todate_str = "TO_DATE('"+timestr+" 10:00:00', 'MM/DD/YYYY HH24:MI:SS')"
			if flag11 == 0:
				line_MO = "Insert into PC3_SPECIAL_NUMBER (SUB_BRAND, SPECIAL_NUMBER, ROAMING_IND, CALL_SOURCE, SERVICE_TYPE, CALL_DIRECTION, FULL_OR_PREFIX_IND, EFFECTIVE_DATE, DROP_CALL_IND, SPECIAL_NUMBER_GROUP, AUTOMATICALLY_AUTHORIZED, BLACK_LISTED, AREA, DESCRIPTION)  Values ('"+entry_MO[5]+"', '"+entry_MO[6]+"', "+entry_MO[7]+", '"+entry_MO[8]+"', '"+entry_MO[9]+"', '"+entry_MO[10]+"', '"+entry_MO[11]+"', "+todate_str+", '"+entry_MO[13]+"', '"+entry_MO[14]+"', '"+entry_MO[16]+"', '"+entry_MO[17]+"', '"+entry_MO[18]+"', '"+entry_MO[20]+"');\n"
				fd_sql.write(line_MO)
				entry_MO[0] = "C.New"
				stored_entries.append(["A.Final Loaded"]+entry_MO[1:])
			if flag22 == 0:
				line_MT = "Insert into PC3_SPECIAL_NUMBER (SUB_BRAND, SPECIAL_NUMBER, ROAMING_IND, CALL_SOURCE, SERVICE_TYPE, CALL_DIRECTION, FULL_OR_PREFIX_IND, EFFECTIVE_DATE, DROP_CALL_IND, SPECIAL_NUMBER_GROUP, AUTOMATICALLY_AUTHORIZED, BLACK_LISTED, AREA, DESCRIPTION)  Values ('"+entry_MT[5]+"', '"+entry_MT[6]+"', "+entry_MT[7]+", '"+entry_MT[8]+"', '"+entry_MT[9]+"', '"+entry_MT[10]+"', '"+entry_MT[11]+"', "+todate_str+", '"+entry_MT[13]+"', '"+entry_MT[14]+"', '"+entry_MT[16]+"', '"+entry_MT[17]+"', '"+entry_MT[18]+"', '"+entry_MT[20]+"');\n"
				fd_sql.write(line_MT)
				entry_MT[0] = "C.New"
				stored_entries.append(["A.Final Loaded"]+entry_MT[1:])

			# add history entries to the CSP_logfile.txt log file for the notifactions successfuly processed.
			# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
			fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
			line = "[" + message[1] + "]To Configure: <" + tableInfo[-1] + "> "
			fd_log.write(line + "\n")
			fd_log.close()

	return stored_entries, local_stored, toUpdateManualflag


if __name__ == "__main__":

	#*********************************************************************************************************#
	# Uncomment below line ONLY IF needs update currently local data txt files with most up-to-date xlsx file #
	# --------------------------------------------------------------------------------------------------------#
	# readingxlsx()       # read from newest xlsx file                                                        #
	#*********************************************************************************************************#

	flag = False

	while flag == False:

		ifcopied = input("Do you want to using the newest SMS_SPECIAL_NUMBER_CURRENT.txt? (YES/NO): ")

		if ifcopied.upper() == "NO":
			flag = True
		if ifcopied.upper() == "YES" :
			dirpath = os.getcwd()
			files = os.listdir(dirpath)
			dates = []
			for file in files:
				if "CSP_results_" in file:
					dates.append(int(file[-8:]))
			dates.sort()
			latestdir = dirpath + "\\" + "CSP_results_" + str(dates[-1])
			copyfile(latestdir + "\\SMS_SPECIAL_NUMBER_CURRENT.txt", dirpath + "\\SMS_SPECIAL_NUMBER_CURRENT.txt")
			print("Newest SMS_SPECIAL_NUMBER_CURRENT.txt is copied to current working directory. Process continues ...")
			flag = True

	if not os.path.exists(DIRPATH):
		os.mkdir(DIRPATH)
		print("Directory ", DIRPATH, " Created")
	else:
		print("Directory " + DIRPATH + " is already exists. Exiting the program...")
		exit()

	# read local data from data txt files
	billingID_search, stored_entries = read_historytxt() # read from existing txt files


	# seperate emails depend on needs
	toConfigureLst, toRemoveLst, toUpdateLst, timelst = readingEmail()
	if len(timelst) == 0:
		print("No unread notification emails detected.")
		os.rmdir(DIRPATH)
		exit()
	local_stored = []

	# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
	fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
	startline = "===== { [" + timelst[0] + " to "+ timelst[-1] + "] " + "starting to log... } =====\n"
	fd_log.write(startline)
	fd_log.close()

	# sql file create
	timestr = time.strftime("%Y%m%d")
	# fd_sql = codecs.open(DIRPATH+"\\BPT"+timestr+"_Special_number.sql", "w", encoding='utf8')
	fd_sql = open(DIRPATH+"\\BPT"+timestr+"_Special_number.sql", "w")
	fd_sql.write("SET DEFINE OFF;\n")
	# fd_history_new = codecs.open(DIRPATH+"\\SMS_SPECIAL_NUMBER_CURRENT.txt", "w", encoding='utf8')
	fd_history_new =open(DIRPATH+"\\SMS_SPECIAL_NUMBER_CURRENT.txt", "w")

	# perform ToRemove
	stored_entries, local_stored, toRemoveManualflag = doRemove(toRemoveLst, billingID_search, fd_sql, stored_entries, local_stored)
	if toRemoveManualflag == True:
		print("Please check ToRemove_Manualfile file in results directory, MANUAL ENTRY REQUIRED")
	
	# perform ToConfigure 
	stored_entries, local_stored, toConfigManualflag = doConfigure(toConfigureLst, billingID_search, fd_sql, stored_entries, local_stored)
	if toConfigManualflag == True:
		print("Please check ToConfigure_Manualfile file in results directory, MANUAL ENTRY REQUIRED")

	# perform ToUpdate
	stored_entries, local_stored, toUpdateManualflag = doUpdate(toUpdateLst, billingID_search, fd_sql, stored_entries, local_stored)
	if toUpdateManualflag == True:
		print("Please check ToUpdate_Manualfile file in results directory, MANUAL ENTRY REQUIRED")

	for entry in stored_entries:
		line = ""
		for item in entry:
			line += str(item) + ","
		line = line[:-1]
		line += "\n"
		fd_history_new.write(line)

	# sql file finished
	fd_sql.write("commit;\n")
	fd_sql.close()
	fd_history_new.close()

	# print counting results

	fd_count = open(DIRPATH+"\\BPT"+timestr+"_Special_number.sql", "r")
	insertC, deleteC = 0, 0
	for line in fd_count:
		k = line.split()[0].strip()
		if k == "Insert":
			insertC += 1
		if k == "delete":
			deleteC += 1
	fd_count.close()

	sumline = "===== { [" + timelst[0] + " to "+ timelst[-1] + "] " + "Insert Count: " + str(insertC) + "  Delete Count: " + str(deleteC) + " } =====\n"
	# fd_log = codecs.open(DIRPATH+"\\CSP_logfile.txt", "a+", encoding='utf8')
	fd_log = open(DIRPATH+"\\CSP_logfile.txt", "a+")
	fd_log.write(sumline)
	fd_log.close()