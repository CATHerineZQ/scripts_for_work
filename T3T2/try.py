import os
import re
import sys
import time

import datetime



def getFutureDate(pushnum):
	today = datetime.date.today()
	date = str(today + datetime.timedelta(days=pushnum))
	year, month, day = date[:4], date[5:7], date[-2:]
	return day+"/"+month+"/"+year

saturday, sunday, tuesday = getFutureDate(2), getFutureDate(3), getFutureDate(5)

print(saturday, sunday, tuesday)
print( "Saturday: " + saturday)
print( "  Sunday: " + sunday)
print( " Tuesday: " + tuesday)


#11/10/2018 12/10/2018 14/10/2018


# timestr = time.strftime("%d/%m/%Y")
# # print(timestr)

# today = datetime.date.today() # should be current date, thursday date
# sat = str(today + datetime.timedelta(days=2))  # Saturday date
# sun = str(today + datetime.timedelta(days=3))  # Sunday date
# tue = str(today + datetime.timedelta(days=5))  # Sunday date

# satY, satM, satD = sat[:4], sat[5:7], sat[-2:]
# sunY, sunM, sunD = sun[:4], sun[5:7], sun[-2:]
# tueY, tueM, tueD = tue[:4], tue[5:7], tue[-2:]

# saturday = satD+"/"+satM+"/"+satY
# sunsay = sunD+"/"+sunM+"/"+sunY
# tuesday = tueD+"/"+tueM+"/"+tueY


# print(saturday, sunsay, tuesday)