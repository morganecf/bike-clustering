"""
Contains method for aggregating ecovis data into csv format,
and running clustering. 
""" 

import os
import math
from collections import defaultdict
from datetime import datetime, timedelta, date

# WWI, AMI, PPI

# inclusive season start and end months
season_start = 4
season_end = 11

# inclusive start/end periods for AMI 
AM_start = 7
AM_end = 9
mid_start = 11
mid_end = 13

# upper boundary for top months for PPI 
PPI_top = 12
# lower boundary for bottom months for PPI
PPI_bottom = 28

years = [2011, 2012, 2013, 2014]

# helper functions 
def is_location(v): return not (v.endswith('IN') or v.endswith('OUT'))
def is_weekday(date, holiday): return not holiday and date.weekday() < 5
def is_in_season(date): return date.month >= 4 and date.month <= 11
#def is_in_season(date): return True 
def is_morning(hour): return hour >= AM_start and hour <= AM_end
def is_midday(hour): return hour >= mid_start and hour <= mid_end 

def week_to_monday(year, week):
	ret = datetime.strptime('%04d-%02d-1' % (year, week), '%Y-%W-%w')
	if date(year, 1, 4).isoweekday() > 4:
	    ret -= timedelta(days=7)
	return ret

# aggregate data 
def counter(filename):
	lines = open(filename).read().splitlines()
	metadata = lines[0].split(',')
	locations = {}

	# metric counts will be stored here for each location 
	data = {}
	for year in years:
		for index, value in enumerate(metadata[3:]):
			if is_location(value):
				name = value + str(year)
				locations[index] = value 
				data[name] = {
					'weekend_traffic': 0,
					'weekday_traffic': 0,
					'num_weekdays': 0,
					'num_weekends': 0,
					'morning_traffic': 0,
					'midday_traffic': 0,
					'by_week': defaultdict(int)		# will collect counts for each week 
				}

	# go through each datapoint
	for line in lines[1:]:
		info = line.split(',')
		# skip any blank lines 
		if info[0] == '':
			continue 

		# day/month/year format
		date = datetime.strptime(info[0], '%d/%m/%Y')

		# only count in-season information
		if not is_in_season(date):
			continue 

		holiday = int(info[1])
		time = info[2]	
		week = date.isocalendar()[1]
		hour = int(time.split(':')[0])

		for i, aadt in enumerate(info[3:]): 
			# skip over in/out counts 
			if i not in locations:
				continue 
			# skip over blank entries for aadt
			if aadt == '':
				continue

			aadt = int(aadt) 
			name = locations[i] + str(date.year)

			# days start at 0:00, i.e., midnight  
			if time == '0:00' or time == '00:00':
				if is_weekday(date, holiday):
					data[name]['num_weekdays'] += 1
				else:
					data[name]['num_weekends'] += 1 

			# aggregate aadt counts 
			if is_weekday(date, holiday):
				data[name]['weekday_traffic'] += aadt 
			else:
				data[name]['weekend_traffic'] += aadt 

			# new week starts at weekday #0
			data[name]['by_week'][week] += aadt

			# increment morning/midday data if possible
			if is_morning(hour):
				data[name]['morning_traffic'] += aadt
			elif is_midday(hour):
				data[name]['midday_traffic'] += aadt

	# all data has been aggregated! now calculate indexes 
	no_data = []
	for location, counts in data.iteritems():
		num_days = float(counts['num_weekends'] + counts['num_weekdays'])

		if num_days == 0:
			print location, 'has no AADT'
			no_data.append(location)
			continue

		# WWI (ratio of average daily weekend traffic to average daily weekday traffic)
		avg_daily_weekend_traffic = counts['weekend_traffic'] / float(counts['num_weekends'])
		avg_daily_weekday_traffic = counts['weekday_traffic'] / float(counts['num_weekdays'])
		data[location]['WWI'] = avg_daily_weekend_traffic / avg_daily_weekday_traffic

		# AMI 1 (ratio of average morning to midday traffic)
		avg_morning_traffic = counts['morning_traffic'] / num_days
		avg_midday_traffic = counts['midday_traffic'] / num_days
		data[location]['AMI'] = avg_morning_traffic / avg_midday_traffic

		# PPI (avg of top 12 weeks / avg of following 20)
		week_vals = list(data[location]['by_week'].iteritems())
		week_vals.sort(key=lambda t: t[1], reverse=True)
 
		# print '====================', location, '================================'
		# for month_bin, count in week_vals:
		# 	print month_bin, '\t', count
		top_average = sum((t[1] for t in week_vals[:PPI_top])) / float(PPI_top)
		bottom_average = sum((t[1] for t in week_vals[PPI_top:PPI_bottom])) / float(PPI_bottom - PPI_top + 1)
		data[location]['PPI'] = top_average / bottom_average
		# print 'num weeks:', len(week_vals)
		# print 'sum of aadt for this year:', sum((t[1] for t in week_vals))
		# print 'average weekly aadt:', sum((t[1] for t in week_vals)) / float(len(week_vals))
		# print 'average weekly for top 12 months:', top_average
		# print 'average weekly for next 20 months:', bottom_average
		# print 'PPI:', data[location]['PPI']
		# print '=================================================================='

	# remove locations with no data
	for nd in no_data:
		del data[nd]

	return data 

# Save the features as a csv 
def save(data, output, extra=None):
	out = open(output, 'w')
	out.write('location,WWI,AMI,PPI\n')
	for location, counts in data.iteritems():
		info = [location, str(counts['WWI']), str(counts['AMI']), str(counts['PPI'])]
		out.write(','.join(info) + '\n')
	if extra:
		for extra_data in extra:
			for location, counts in extra_data.iteritems():
				info = [location, str(counts['WWI']), str(counts['AMI']), str(counts['PPI'])]
				out.write(','.join(info) + '\n')
	out.close()

# Print out the counters in each cluster 
def print_clusters(labels, locations):
	groups = {}
	i = 0
	for label in labels:
		if label in groups:
			groups[label].append(locations[i])
		else:
			groups[label] = [locations[i]]
		i += 1
	print 'k=' + str(len(groups))
	for group, names in groups.iteritems():
		names = ', '.join(names)
		print 'Cluster#' + str(group) + ': ' + names 
	print ""


# Cluster the locations using K-Means clustering 
def cluster(features, locations):
	import numpy as np
	from sklearn import cluster 

	feature_mat = np.empty([len(features), len(features[0])])

	for row, values in enumerate(features):
		for col, feature in enumerate(values):
			feature_mat[row,col] = feature

	# can vary max_iter and n_init to try to escape local minima 
	km2 = cluster.KMeans(n_clusters=2)
	km3 = cluster.KMeans(n_clusters=3)
	km4 = cluster.KMeans(n_clusters=4)

	clusters2 = km2.fit(feature_mat).labels_
	clusters3 = km3.fit(feature_mat).labels_
	clusters4 = km4.fit(feature_mat).labels_

	print_clusters(clusters2, locations)
	print_clusters(clusters3, locations)
	print_clusters(clusters4, locations)


# Parse a file of features into a data structure 
def create_feature_set(filename, year=None):
	if year:
		year = str(year)
	lines = open(filename).read().splitlines()
	features = []
	locations = []
	for line in lines[1:]:
		location = line.split(',')[0]
		if year and location.endswith(year):
			locations.append(location)
			indexes = [float(v) for v in line.split(',')[1:]]
			features.append(indexes)
	return features, locations 



### EXTRAPOLATION/DISAGGREGATED METHOD STUFF ### 

exclude = ('Rachel12014', 
		   #'Gare de Tremblant Cyclists2014', 
		   #'Mirabel Cyclists2014', 
		   #'GareNominingue Cyclists2014', 
		   #'Prevost Cyclists2014',
		   'Prevost Cyclists2011',
		   'GareNominingue Cyclists2011',
		   'Mirabel Cyclists2011',
		   #'Gare de Tremblant Cyclists2011',
		   'Totem_Laurier2011',
		   'Prevost Cyclists2013',
		   'Maisonneuve_12013',
		   'TR Island Cyclists2013',
		   'Joyce St NB Cyclists2013')

# Create dict of traffic for each day in a year (or hour in a year, if hourly is set to True)
def traffic_counts(filename, year, hourly=False):
	lines = open(filename).read().splitlines()
	metadata = lines[0].split(',')
	
	traffic = {}
	locations = {}

	# Initialize dict for each location for this year
	for index, value in enumerate(metadata[3:]):
		if is_location(value):
			name = value + str(year)
			if name in exclude:
				continue
			traffic[name] = defaultdict(int)
			locations[index] = value

	# Go through each datapoint
	for line in lines[1:]:
		info = line.split(',')
		# Skip any blank lines 
		if info[0] == '':
			continue 

		# day/month/year format
		if not hourly:
			date = datetime.strptime(info[0], '%d/%m/%Y')
		else:
			date = datetime.strptime(info[0] + ' ' + info[2], '%d/%m/%Y %H:00')
			# Skip over lines between 8 PM - 6 AM, inclusive 
			if date.hour >= 20 or date.hour <= 6:
				continue

		# Skip over lines not belonging to this year 
		if date.year != year:
			continue

		######## TODO::: ???? only count in-season information ########
		if not is_in_season(date):
			continue 

		for i, count in enumerate(info[3:]): 
			# skip over in/out counts and blank entries for aadt
			if i not in locations or count == '': 
				continue 
			# Aggregate aadt for each location for each day (or hour)
			count = int(count) 
			name = locations[i] + str(year)
			traffic[name][date] += count
			traffic[name]['traffic'] += count

	# Get yearly AADT for each counter 
	for counter, info in traffic.iteritems():
		# Skip over counters that have no information
		if len(info) <= 1:
			print 'Missing data for:', counter 
			continue
		info['AADT'] = info['traffic'] / float(len(info) - 1)
		del info['traffic']

	return traffic

# Disaggregated method for estimating AADT of short-term counter
# in a given year 
def estimate_disaggregate(filename, short, year):
	name = short + str(year)
	# Get the traffic per day for each counter by year 
	traffic = traffic_counts(filename, year)
	# Get the long term counters 
	longterms = [location for location in traffic.keys() if not location.startswith(short)]
	# The short term counter 
	shortterm = traffic[name]
	# Bin the short term counts by week 
	short_weeks = {}
	for date, count in shortterm.iteritems():
		if date == 'AADT':
			continue
		week = date.isocalendar()[1]
		try:
			short_weeks[week][date] = count
		except KeyError:
			short_weeks[week] = {date: count}
	# Sample by week - get the estimated AADT for each day of the week 
	# and then take average (sdb * (aadt / db) = estimate)
	estimates = {}
	for week, days in short_weeks.iteritems():
		# Find estimates for each day of the week for each long-term counter
		daily_estimates = defaultdict(int)
		for day, count in days.iteritems():
			# Use each counter as a sample long-term counter 
			for longterm in longterms:
				db = traffic[longterm][day]
				aadt = traffic[longterm]['AADT']
				factor = aadt / float(db)
				estimate = count * factor
				daily_estimates[longterm] += estimate
		# Now find averages 
		for longterm, daily_total in daily_estimates.iteritems():
			average_estimate = daily_total / float(len(days))
			daily_estimates[longterm] = average_estimate 
		# Now save 
		estimates[week] = daily_estimates 
	# Get the actual aadt for this counter 
	actual = traffic[name]['AADT']
	return estimates, actual

def save_disaggregated_results(weekly_estimates, actual_aadt, outf, reference=None):
	out = open(outf, 'w')
	out.write('week,long-term counter,estimate,actual,error\n')
	for week, estimates in weekly_estimates.iteritems():
		if reference is None:
			for longterm, estimate in estimates.iteritems():
				err = estimate - actual_aadt
				line = [str(week), longterm, str(estimate), str(actual_aadt), str(err)]
				out.write(','.join(line) + '\n')
		else:
			estimate = estimates[reference]
			err = estimate - actual_aadt
			line = [str(week), reference, str(estimate), str(actual_aadt), str(err)]
			out.write(','.join(line) + '\n')
	out.close()

# Save all the estimates and errors 
def disaggregated_results(counter, year, reference=None):
	estimates, actual = estimate_disaggregate('data/montreal_hour_direction-holiday_err-removed.csv', counter, year)
	if reference is None:
		save_disaggregated_results(estimates, actual, 'data/disaggregated-results/' + str(year) + '/' + counter.lower() + '.csv', reference=reference)
	else:
		save_disaggregated_results(estimates, actual, 'data/disaggregated-results/' + str(year) + '/' + counter.lower() + '_' + reference.lower() + '.csv', reference=reference)

# Save the best estimate for each week 
def test_disaggregated(counter, year):
	weekly_estimates, actual = estimate_disaggregate('data/montreal_hour_direction-holiday_err-removed.csv', counter, year)
	out = open('data/disaggregated-results/' + str(year) + '/' + counter.lower() + '_best.csv', 'w')
	out.write('week,best long-term counter,best estimate,actual,best error\n')
	for week, estimates in weekly_estimates.iteritems():
		best_counter = None
		best_estimate = None
		best_err = 99999999999999
		best_err_raw = None
		for longterm, estimate in estimates.iteritems():
			err = estimate - actual 
			if abs(err) < best_err:
				best_err = abs(err)
				best_err_raw = err
				best_estimate = estimate
				best_counter = longterm 
		line = [str(week), best_counter, str(best_estimate), str(actual), str(best_err_raw)]
		out.write(','.join(line) + '\n')
	out.close()

# Get a counter's weekly aggregated traffic counts given its 
# total daily counts
def weekly_traffic_counts(daily_counts, sigma=None):
	# Bin the short term counts by week 
	by_week = {}
	for date, count in daily_counts.iteritems():
		if date == 'AADT':
			continue
		week = date.isocalendar()[1]
		try:
			by_week[week][date] = count
		except KeyError:
			by_week[week] = {date: count}

	# TODO: Inefficient to go through again - fix 
	if sigma:
		return filter_weekly_traffic_counts(by_week, sigma)
	return by_week, None

# Filter a counter's data - remove data points within a week
# that fall outside of the given standard deviation. Works for
# days and hours. 
def filter_weekly_traffic_counts(weekly_counts, sigma):
	filtered_counts = {}
	total_units = 0
	total_units_kept = 0
	for week, dates in weekly_counts.iteritems():
		# Around 7 or 91, depending on daily/hourly aggregation
		n = float(len(dates))
		# Find the week's mean 
		mean = sum(dates.values()) / n
		# Find the week's variance 
		variance = sum([(x - mean) ** 2 for x in dates.values()]) / n 		# n - 1 ? 
		# 1 std. dev = square root of the variance
		std_dev = math.sqrt(variance)
		# Find the bounds 
		bounds = [mean - (std_dev * sigma), mean + (std_dev * sigma)]
		# Filter dates that are within sigma standard deviations of this mean - inclusive
		filtered_dates = {}
		for unit, val in dates.iteritems():
			if val >= bounds[0] and val <= bounds[1]:
				filtered_dates[unit] = val
		filtered_counts[week] = filtered_dates
		total_units_kept += len(filtered_dates)
		total_units += len(dates)
	# Return the filtered counts and the percentage of the data kept 
	return filtered_counts, (total_units_kept / float(total_units)) * 100

# Estimate AADT for a counter given traffic count data and other 
# counters to compare it against (estimate for each week for each counter)
def estimate_weekly_aadt(counter1, counters, traffic_data, sigma=None, median=False):
	# Sample by week - get the estimated AADT for each day (or hour) of the week 
	# and then take average (sdb * (aadt / db) = estimate)
	weekly_counts, perc_kept = weekly_traffic_counts(traffic_data[counter1], sigma=sigma)
	if perc_kept:
		print counter1, '\t', perc_kept

	estimates = {}
	for week, days in weekly_counts.iteritems():

		if median:
			daily_estimates = defaultdict(list)
		else:
			# Find estimates for each day of the week for each long-term counter
			daily_estimates = defaultdict(int)		
			# Keep track of number of days to get a correct average (there may not be counts for some days)
			daily_tallies = defaultdict(int)

		for day, count in days.iteritems():
			# Use each other counter as a sample long-term counter 
			for longterm in counters:
				db = traffic_data[longterm][day] 		# Note: traffic_data[longterm] is defaultdict, so might increase by size here if day doesn't exist 
				if db == 0:
					continue
				aadt = traffic_data[longterm]['AADT']
				factor = aadt / float(db)
				estimate = count * factor

				if median:
					daily_estimates[longterm].append(estimate)
				else:
					daily_estimates[longterm] += estimate
					daily_tallies[longterm] += 1

		if median: 
			median_estimates = defaultdict(float)
			for longterm, daily_totals in daily_estimates.iteritems():
				n = len(daily_totals)
				if n % 2 == 0:
					dt = sorted(daily_totals)
					median = (dt[n / 2] + dt[(n / 2) - 1]) / 2.0
				else:
					median = float(sorted(daily_totals)[n / 2])

				median_estimates[longterm] = median
			# Save
			estimates[week] = median_estimates

		else:
			# Now find averages 
			for longterm, daily_total in daily_estimates.iteritems():
				#print longterm, daily_total, daily_tallies[longterm]
				average_estimate = daily_total / float(daily_tallies[longterm])
				daily_estimates[longterm] = average_estimate 
			# Save 
			estimates[week] = daily_estimates 
		
	# Also return the actual aadt for this counter 
	actual = traffic_data[counter1]['AADT']
	return estimates, actual

# clusterfile and year should correspond
def cluster_validation(clusterfile, datafile, year, outf, datafiles=None, sigma=None, median=False, hourly=False):
	# Get the counts for this year 
	traffic_data = traffic_counts(datafile, year, hourly=hourly)

	# Merge other count files with the original one
	# TODO: This is kinda hacky+expensive, find better way
	if datafiles:
		for df in datafiles:
			td = traffic_counts(df, year, hourly=hourly)
			for k, v in td.iteritems():
				traffic_data[k] = v

	# Open the cluster file 
	clusters = open(clusterfile).read().splitlines()

	# Get all the weeks we want (May to October)
	may1 = datetime(year, 5, 1).isocalendar()[1]
	oct31 = datetime(year, 10, 31).isocalendar()[1]
	week_range = range(may1, oct31 + 1)

	k = 1
	for line in clusters:
		if not line.startswith('Cluster'):
			if line.startswith('k='):
				print line
				k += 1
			continue

		cluster_name = line.split(':')[0].lower().replace('#', '')
		cluster = line.split(':')[1]
		counters = [c.strip() for c in cluster.split(',')]

		error_matrix = {}

		out = open(outf + '.' + cluster_name + '.csv', 'w')

		for short_term in counters:
			out.write('Short term counter:,' + short_term + '\n')
			out.write('Long term counters:,' + ','.join(counters) + '\n')

			# weekly estimates is of form {week: {longterm: estimate}}
			weekly_aadt_estimates, actual_aadt = estimate_weekly_aadt(short_term, counters, traffic_data, sigma=sigma, median=median)

			# Now find the average absolute error across all the weeks for each long term counter
			errors = defaultdict(list)
			
			# Tally the total absolute error
			for week in week_range:
				week_str = str(week_to_monday(year, week)).split()[0]

				for long_term in counters:
					estimate = weekly_aadt_estimates[week][long_term]
					error = estimate - actual_aadt
					perc_error = error / actual_aadt
					errors[long_term].append((abs(perc_error), error))

					week_str += ',' + str(perc_error)

				out.write(week_str + '\n')
			
			# Find the average error
			avg_abs_errs = defaultdict(dict)
			for location, err_info in errors.iteritems():
				avg_abs_errs[location]['perc-err'] = sum(e[0] for e in err_info) / float(len(weekly_aadt_estimates))
				avg_abs_errs[location]['total-errs'] = [e[1] for e in err_info]
			error_matrix[short_term] = avg_abs_errs

		out.close()

		# error_matrix now contains a counter x counter abs avg error matrix 
		# Save to csv file 
		out_mat = open(outf + '.k' + str(k) + '.' + cluster_name + '.matrix.csv', 'w')
		out_mat.write(','.join([''] + counters) + ',Best guess:\n')

		for counter in counters:
			row = counter
			best_guess = 'NA'
			best_err = 100.0
			for longterm in counters:
				avg_abs_err = error_matrix[counter][longterm]['perc-err'] * 100
				row += ',' + str(avg_abs_err)
				if avg_abs_err < best_err and longterm != counter:
					best_guess = longterm
					best_err = avg_abs_err
			out_mat.write(row + ',' + best_guess + '\n')

		out_mat.close()

# Given two cluster error matrix files, compare their errors
def compare_disaggregation_testing_results(f1, f2, n1, n2, outdir):
	d1 = open(f1).read().splitlines()
	d2 = open(f2).read().splitlines()

	assert len(d1) == len(d2)

	data1 = []
	data2 = []
	longterms = []
	best_guesses1 = []
	best_guesses2 = []
	for line in d1[1:]:
		line = line.split(',')
		data1.append(line[1:-1])
		longterms.append(line[0])
		best_guesses1.append(line[-1])
	for line in d2[1:]:
		line = line.split(',')
		data2.append(line[1:-1])
		best_guesses2.append(line[-1])

	assert len(data1[0]) == len(data2[0])

	# The comparison matrix 
	comparison = []
	n1_wins = 0
	n2_wins = 0
	total = 0.0
	for i, errs in enumerate(data1):
		comp = []
		for j, err in enumerate(errs):
			if float(err) < float(data2[i][j]):
				comp.append(n1)
				n1_wins += 1
			else:
				comp.append(n2)
				n2_wins += 1
			total += 1.0
		comparison.append(comp)

	# Save comparison matrix
	out = open(os.path.join(outdir, n1 + '.vs.' + n2 + '.csv'), 'w')
	out.write(','.join(d1[0].split(',')[:-1]) + ',Best guess ' + n1 + ',Best guess ' + n2 + '\n')
	for i, row in enumerate(comparison):
		s = longterms[i] + ',' + ','.join(row) + ',' + best_guesses1[i] + ',' + best_guesses2[i]
		out.write(s + '\n')
	out.close()

	# Print out some stats 
	print n1, '\t', (n1_wins / total) * 100, '% of estimates were smaller'
	print n2, '\t', (n2_wins / total) * 100, '% of estimates were smaller'
	print 'Best guesses agreed', (len(set(best_guesses1) & set(best_guesses2)) / float(len(best_guesses1))) * 100, '% of the time'

## Redo clustering for each city for each year 
# features, locations = create_feature_set('data/features/mtl_ott_arl_features.csv', 2014)
# cluster(features, locations)

## Now perform validation 
mtl_datafile = 'data/montreal_hour_direction-holiday_err-removed.csv'
ott_datafile = 'data/ottawa_hour_direction-holiday_err-removed.csv'
arl_datafile = 'data/arlington_hour_holiday_reformatted.csv'

# # Montreal
# cluster_validation('disaggregation-testing/mtl/mtl.2011.clusters', mtl_datafile, 2013, 'disaggregation-testing/mtl/mtl.2013.estimations')
# # Ottawa
# cluster_validation('disaggregation-testing/ott/ott.2014.clusters', ott_datafile, 2014, 'disaggregation-testing/ott/ott.2014.estimations')
# # Arlington
# cluster_validation('disaggregation-testing/arl/arl.2014.clusters', arl_datafile, 2014, 'disaggregation-testing/arl/arl.2014.estimations')
# # All
# cluster_validation('disaggregation-testing/all/all.2011.clusters', all_datafile, 2011, 'disaggregation-testing/all/all.2011.estimations')

# missing montreal 2012-2014
# missing arlington 2012, 2013
# missing all 

# Test cases
test1 = 'disaggregation-testing/test1-2014/cluster_test_2014.csv'
test2 = 'disaggregation-testing/test2-2014/cluster_test_2014_2.csv'
test3 = 'disaggregation-testing/test1-2013/cluster_test_2013.csv'
test4 = 'disaggregation-testing/test2-2013/cluster_test_2013_2.csv'

## Cluster validation using hourly aggregation - median 
test1 = 'disaggregation-testing/hourly/median/test1-2014/cluster_test_2014.csv'
test2 = 'disaggregation-testing/hourly/median/test2-2014/cluster_test_2014_2.csv'
test3 = 'disaggregation-testing/hourly/median/test1-2013/cluster_test_2013.csv'
test4 = 'disaggregation-testing/hourly/median/test2-2013/cluster_test_2013_2.csv'

# outname = test1.replace('.csv', '.estimation')
# cluster_validation(test1, mtl_datafile, 2014, outname, datafiles=[ott_datafile, arl_datafile], median=True, hourly=True)

## Cluster validation using hourly aggregation - distrib 
test1 = 'disaggregation-testing/hourly/distrib/test1-2014/cluster_test_2014.csv'
test2 = 'disaggregation-testing/hourly/distrib/test2-2014/cluster_test_2014_2.csv'
test3 = 'disaggregation-testing/hourly/distrib/test1-2013/cluster_test_2013.csv'
test4 = 'disaggregation-testing/hourly/distrib/test2-2013/cluster_test_2013_2.csv'

# outname = test1.replace('.csv', '.s17.estimation')
# cluster_validation(test1, mtl_datafile, 2014, outname, datafiles=[ott_datafile, arl_datafile], sigma=1.7, hourly=True)

## Compare results - hourly median vs. daily median 
# Test 1 - 2014 
f1 = 'disaggregation-testing/hourly/distrib/test1-2014/cluster_test_2014.s2.estimation.k1.cluster0.matrix.csv'
f2 = 'disaggregation-testing/test1-2014/cluster_test_2014.estimations.k1.cluster0.matrix.csv'
n1 = 'hourly-distrib2-cluster0'
n2 = 'daily-regular-cluster0'
#compare_disaggregation_testing_results(f1, f2, n1, n2, 'disaggregation-testing/test1-2014')

# outname = test1.replace('.csv', '.estimations')
# cluster_validation(test1, mtl_datafile, 2014, outname, datafiles=[ott_datafile, arl_datafile])

## Cluster validation using median 
test1 = 'disaggregation-testing/using-median/test1-2014/cluster_test_2014.csv'
test2 = 'disaggregation-testing/using-median/test2-2014/cluster_test_2014_2.csv'
test3 = 'disaggregation-testing/using-median/test1-2013/cluster_test_2013.csv'
test4 = 'disaggregation-testing/using-median/test2-2013/cluster_test_2013_2.csv'

outname = test4.replace('.csv', '.estimations')
cluster_validation(test4, mtl_datafile, 2013, outname, datafiles=[ott_datafile, arl_datafile])

## Cluster validation removing outliers

# test1 = 'disaggregation-testing/outliers-removed/test1-2014/cluster_test_2014.csv'
# test2 = 'disaggregation-testing/outliers-removed/test2-2014/cluster_test_2014_2.csv'
# test3 = 'disaggregation-testing/outliers-removed/test1-2013/cluster_test_2013.csv'
# test4 = 'disaggregation-testing/outliers-removed/test2-2013/cluster_test_2013_2.csv'

# Test cluster validation with std deviations from 0.5 - 2.0
def cluster_val_rm_outliers(test, year):
	# Std dev = 0.5
	outname = test.replace('.csv', '.s05.estimations')
	cluster_validation(test, mtl_datafile, year, outname, datafiles=[ott_datafile, arl_datafile], sigma=0.5)
	# Std dev = 1.0
	outname = test.replace('.csv', '.s1.estimations')
	cluster_validation(test, mtl_datafile, year, outname, datafiles=[ott_datafile, arl_datafile], sigma=1.0)
	# Std dev = 1.5
	outname = test.replace('.csv', '.s15.estimations')
	cluster_validation(test, mtl_datafile, year, outname, datafiles=[ott_datafile, arl_datafile], sigma=1.5)
	# Std dev = 2.0
	outname = test.replace('.csv', '.s2.estimations')
	cluster_validation(test, mtl_datafile, year, outname, datafiles=[ott_datafile, arl_datafile], sigma=2.0)
	# Std dev = 2.1
	outname = test.replace('.csv', '.s21.estimations')
	cluster_validation(test, mtl_datafile, year, outname, datafiles=[ott_datafile, arl_datafile], sigma=2.1)

# cluster_val_rm_outliers(test1, 2014)
# cluster_val_rm_outliers(test2, 2014)
# cluster_val_rm_outliers(test3, 2013)
# cluster_val_rm_outliers(test4, 2013)


# disaggregated_results('Berri1', 2014)
# disaggregated_results('Maisonneuve_2', 2014)
# disaggregated_results('CSC', 2014)
# disaggregated_results('PierDup', 2014)
# disaggregated_results('Totem_Laurier', 2014)
# disaggregated_results('Parc', 2014)
# disaggregated_results('Maisonneuve_1', 2014)

# test_disaggregated('Berri1', 2014)
# test_disaggregated('Maisonneuve_2', 2014)
# test_disaggregated('CSC', 2014)
# test_disaggregated('PierDup', 2014)
# test_disaggregated('Totem_Laurier', 2014)
# test_disaggregated('Parc', 2014)
# test_disaggregated('Maisonneuve_1', 2014)

# disaggregated_results('Maisonneuve_1', 2014, 'Maisonneuve_22014')

# disaggregated_results('Maisonneuve_1', 2011)
# test_disaggregated('Maisonneuve_1', 2011)

# mtl_features, mtl_locations = create_feature_set('data/features/mtl_features_by_year.csv')
# ottawa_features, ottawa_locations = create_feature_set('data/features/ottawa_features_by_year.csv')

# print 'MTL'
# cluster(mtl_features, mtl_locations)

# print 'OTTAWA'
# cluster(ottawa_features, ottawa_locations)

# print 'BOTH'
# cluster(mtl_features+ottawa_features, mtl_locations+ottawa_locations)

# # Run for mtl - expanded counters 
# mtl_data = counter('data/montreal_hour_direction-holiday.csv')
# save(mtl_data, 'data/features/mtl_features_by_year.csv')

# # Run for ottawa - expanded counters 
# ottawa_data = counter('data/ottawa_hour_direction-holiday.csv')
# save(ottawa_data, 'data/features/ottawa_features_by_year.csv')


# remove 2 extra mtl locations 
# extras = ['Totem_Laurier', 'PierDup']
# mtl_features_no_ppi_no2 = []
# mtl_features_ppi_no2 = []
# mtl_features_ppi_2 = []
# mtl_lines = open('data/features/mtl_features.csv').read().splitlines()
# mtl_locations = []
# mtl_locations_no2 = []
# for line in mtl_lines[1:]:
# 	mtl_location = line.split(',')[0]
# 	indexes = [float(v) for v in line.split(',')[1:]]
# 	indexes_no_ppi = indexes[:2]
# 	if line.startswith(extras[0]) or line.startswith(extras[1]):
# 		mtl_features_ppi_2.append(indexes)
# 		mtl_locations.append(mtl_location)
# 	else:
# 		mtl_features_ppi_no2.append(indexes)
# 		mtl_features_no_ppi_no2.append(indexes_no_ppi)
# 		mtl_locations_no2.append(mtl_location)

# 		mtl_features_ppi_2.append(indexes)
# 		mtl_locations.append(mtl_location)


# ott_features_no_ppi = []
# ott_features_ppi = []
# ott_lines = open('data/features/ottawa_features.csv').read().splitlines()
# ottawa_locations = []
# for line in ott_lines[1:]:
# 	ottawa_locations.append(line.split(',')[0])
# 	indexes = [float(v) for v in line.split(',')[1:]]
# 	indexes_no_ppi = indexes[:2]
# 	ott_features_ppi.append(indexes)
# 	ott_features_no_ppi.append(indexes_no_ppi)

#cluster(mtl_features_no_ppi_no2+ott_features_no_ppi, mtl_locations_no2+ottawa_locations)
#cluster(mtl_features_ppi_no2+ott_features_ppi, mtl_locations_no2+ottawa_locations)
#cluster(mtl_features_ppi_2+ott_features_ppi, mtl_locations+ottawa_locations)

# print 'MTL: no PPI, no 2 extra locations'
# cluster(mtl_features_no_ppi_no2, mtl_locations_no2)
# print '\nMTL: using PPI, no 2 extra locations'
# cluster(mtl_features_ppi_no2, mtl_locations_no2)
# print '\nMTL: using PPI and 2 extra locations'
# cluster(mtl_features_ppi_2, mtl_locations)

# print '\nOTTAWA: no PPI'
# cluster(ott_features_no_ppi, ottawa_locations)
# print '\nOTTAWA: using PPI'
# cluster(ott_features_ppi, ottawa_locations)

# # Run for mtl
# mtl_data = counter('data/montreal_hour_direction-holiday.csv')
# save(mtl_data, 'data/features/mtl_features.csv')

# # Run for ottawa
# ottawa_data = counter('data/ottawa_hour_direction-holiday.csv')
# save(ottawa_data, 'data/features/ottawa_features.csv')

# # Save both in one file 
# save(mtl_data, 'data/features/mtl_ott_features.csv', data2=ottawa_data)

# # Now cluster 
# print 'clustering..'
# mtl_features, mtl_locations = create_feature_set('data/features/mtl_features.csv')
# ott_features, ott_locations = create_feature_set('data/features/ottawa_features.csv')
# cluster(mtl_features, mtl_locations)
# cluster(ott_features, ott_locations)

# Run for Montreal - with erroneous data removed and new counters 
# mtl_data_fixed = counter('data/montreal_hour_direction-holiday_err-removed.csv')
# save(mtl_data_fixed, 'data/features/mtl_features_fixed.csv')
# mtl_features_fixed, mtl_locations = create_feature_set('data/features/mtl_features_fixed.csv')
# cluster(mtl_features_fixed, mtl_locations)

# Run for Ottawa - with erroneous data removed and new counters 
# ott_data_fixed = counter('data/ottawa_hour_direction-holiday_err-removed.csv')
# save(ott_data_fixed, 'data/features/ott_features_fixed.csv')
# ott_features_fixed, ott_locations = create_feature_set('data/features/ott_features_fixed.csv')
# cluster(ott_features_fixed, ott_locations)

# Run for Montreal and Ottawa - erroneous data removed/new counters
# mtl_data_fixed = counter('data/montreal_hour_direction-holiday_err-removed.csv')
# ottawa_data = counter('data/ottawa_hour_direction-holiday_err-removed.csv')
# save(mtl_data_fixed, 'data/features/mtl_ott_features_fixed.csv', data2=ottawa_data)
# both_features, both_locations = create_feature_set('data/features/mtl_ott_features_fixed.csv')
# cluster(both_features, both_locations)

# Run for Arlington 
# arl_data = counter('data/arlington_hour_holiday_reformatted.csv')
# save(arl_data, 'data/features/arl_features.csv')
# arl_features, arl_locations = create_feature_set('data/features/arl_features.csv')
# cluster(arl_features, arl_locations) 

# Run for Arlington, Montreal, Ottawa
# arl_data = counter('data/arlington_hour_holiday_reformatted.csv')
# mtl_data = counter('data/montreal_hour_direction-holiday_err-removed.csv')
# ott_data = counter('data/ottawa_hour_direction-holiday_err-removed.csv')
# save(arl_data, 'data/features/mtl_ott_arl_features.csv', extra=[mtl_data, ott_data])

# features, locations = create_feature_set('data/features/mtl_ott_arl_features.csv')
# cluster(features, locations)

# correlate with weather 


#### MEETING NOTES #####

# AADT extrapolation -- find ratio then multiply by total average AADT 
	# daily 
		# sample in 7 day chunks - have AADT estimate for each day and then take average of 7
	# hourly - (12 hours, ex [7AM, 6PM])
		# a) shave off tails - anything outside of x standard deviations from mean - vary x 
		# b) or sort and find median and use that instead to shave off outliers 
	# start with only these Montreal counters (2013): CSC, Maisonneuve2, Parc, Rachel1, Totem Laurier

# way to find erroneous data (high variance compared to means)
# characterize distribution of a week to try to find erroneous data (outliers)
# other methods to find outliers - clustering? 
# confidence intervals 
# be able to input period of time of one counter + set of references 
# testing version -- run for all combinations of periods of time over the season 
# and get average error 



## MEETING - 4/30
# naive iterative clustering removing outliers until convergence (when no cluster has <2 counters)
	# Gare Tremblant 2012
	# re-run without this one 
# detecting outliers 
# redo without PPI - see if PPI is valuable 
# look at API -- figure out structure of code getting data with this API 
# and what might need to be added to it 
# do 4-6 clusters rather than 2-4

# clustering based on time series 


## MEETING - 5/8
# validation by AADT estimation for each datapoint in cluster 
	# for each counter 
		# for each week of that counter 
			# estimate the AADT with the other counters in the cluster 
	# Overall output (for each cluster):
	# average of the absolute error of all the errors across all the weeks 
	# error matrix (symmetric and diagonal)
		# reference counter x short term counter 
		# diagonal should be 0 
		# avg abs error 

# use april-nov for aadt calculation 
# use may-oct for sampling weeks 


## MEETING - 5/22
# Print out % Error (avg of all % errors for each week), min and max 
# May-Oct 
# Error for each week for each counter vs. all the other counters 
	# keep sign to see over vs. underestimation 
	# specifically mtl 2013
# look at Montreal data
# Run the cluster validation on each of the test cluster files

# Read API - figure out if there's anything missing - meeting June 8th 
	
