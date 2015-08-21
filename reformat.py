# Fix data that doesn't have the correct date,holiday,time format 

# original: Sun 1 Apr 2012 00:00,0,4,1,0,0,,,,,
# fixed: 01/01/2011,1,0:00,

import sys
from datetime import datetime

data = open(sys.argv[1]).read().splitlines()
metadata = data[0].split(',')

print metadata[0] + ',' + metadata[1] + ',' + 'time,' + ','.join(metadata[2:])

for line in data[1:]:
	info = line.split(',')
	date = info[0]
	holiday = info[1]
	rest = info[2:]

	hour = date.split()[-1]
	date = ' '.join(date.split()[:-1])

	date_parts = date.split()
	if len(date_parts[1]) == 1:
		date_parts[1] = '0' + date_parts[1]
	date = ' '.join(date_parts)

	date_obj = datetime.strptime(date, '%a %d %b %Y')
	formatted_date = date_obj.strftime('%d/%m/%Y')

	print formatted_date + ',' + holiday + ',' + hour + ',' + ','.join(rest)
