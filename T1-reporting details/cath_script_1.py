import os
import re
import sys
import time

# //20180511 &<< Catherine Zhou

# return a list of info that will be use to loop over data later on
def extract_from_csv(csv_src_path):
    fd = open(csv_src_path)
    flag = 0
    ids = []

    for line in fd:
        if flag != 0:
                ids.append(line.split(",")[2])
        flag = 1

    return ids

# return a list of data needed under the src directory path
# return data are filttered
def combine_data(dir_src_path, file_keyword, date_min, date_max, keywords_pos=[], keywords_neg=[]):
    pattern_pos, pattern_neg = "", ""
    for kp in keywords_pos:
        pattern_pos += kp + "|"
    pattern_pos = pattern_pos[:-1]
    for kn in keywords_neg:
        pattern_neg += kn + "|"
    pattern_neg = pattern_neg[:-1]

    filttered_data = []
    for root, dirs, files in os.walk(dir_src_path):
        for file in files:
            # extract date from the file name
            filedate = int(file[-14:-6])
            if (file_keyword in file) and (date_min <= filedate) and (date_max >= filedate) and (".gz" not in file):
                filepath = dir_src_path + "/" + file
                fd = open(filepath, "r")
                for line in fd:
                    if re.search(pattern_pos, line) and (re.search(pattern_neg, line) == None):
                        filttered_data.append(line)
                        #print("=======", line)
                fd.close()

    return filttered_data

def get_details(extratced, data):
    timestr = time.strftime("%Y%m%d%H%M%S")
    newfile_path = "produced_results_" + timestr + ".txt"
    fd = open(newfile_path, "w")
    pattern_ext = ""
    for i in extratced:
        pattern_ext += i + "|"
    pattern_ext = pattern_ext[:-1]

    results = []
    for line in data:
        if re.search(pattern_ext, line):
            fd.write(line)
            #for num in extratced:
            #   if num in line:
            #       fd.write(line)
    fd.close()
    return newfile_path



if __name__ == "__main__":
    # csv_src_path = "copyfile.csv"
    # dir_src_path = "/tmp/catherine/cdr"

    csv_src_path = raw_input("Please enter the full path of csv file: ")
    print("... ... extraction list from csv file")
    extratced = extract_from_csv(csv_src_path)

    dir_src_path = raw_input("Please enter the full path of data directory: ")

    file_keyword = raw_input("Please enter the keyword of the files you are looking for: ")
    
    print("Please fill out the date range below integer in format of xxxxxxxx.")
    date_min = int(raw_input("Starting Date: "))
    date_max = int(raw_input("Ending Date: "))


    pos_lst, neg_lst = [], []
    kp, kn = "START-//TER", "START-//TER"
    # kp, kn = "//TER", "//TER"
    print("=== Enter positive keywords one at a time. Enter '//TER' to terminate the step. ===")
    while kp != "//TER":
        kp = raw_input("Enter a POSITIVE keyword: ")
        pos_lst.append(kp)

    print("=== Enter negative keywords one at a time. Enter '//TER' to terminate the step. ===")
    while kn != "//TER":
        kn = raw_input("Enter a NEGATIVE keyword: ")
        neg_lst.append(kn)

    # pos_lst = ["SMSMOO", "SMSMOT", "SMSMT", "MOC", "MTC", "CFW"]
    # neg_lst = ["3100.2.13.1.0.00"]

    print("... ... filttering data")
    filttered_data = combine_data(dir_src_path, file_keyword, date_min, date_max, pos_lst, neg_lst)

    print("... ... getting details and writing to file")
    get_details(extratced, filttered_data)

    print("Done processing. Please check " + newfile_path + " file under current directory for output.")