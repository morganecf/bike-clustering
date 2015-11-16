import java.io.File;
import java.io.FileNotFoundException;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Scanner;

/*
 * Parses CSV files containing the biking data. 
 * Contains methods for aggregating the data and
 * assessing its quality. This class is substitutable 
 * in the general clustering pipeline with a class
 * that gets the data from the API rather than 
 * textfiles. 
 */
public class EcoParser {
	
	/* File containing a city's raw data */
	String filePath;
	
	/* HashMap containing a city's parsed, aggregated data, by counter location */
	HashMap<String, HashMap<String, Integer>> data;
	
	/* HashMap containing a city's data aggregated by each day of the week */
	HashMap<String, HashMap<Integer, Integer>> weekData; 
	
	/* Variables indicating inclusive start and end periods */
	static int seasonStart = 4;
	static int seasonEnd = 11;
	static int AMStart = 7;
	static int AMEnd = 9;
	static int midStart = 11;
	static int midEnd = 13;
	
	/* Date formatter */
	static DateFormat dformat = new SimpleDateFormat("dd/MM/yyyy");
	
	public EcoParser(String filePath) {
		this.filePath = filePath;
		this.data = new HashMap<String, HashMap<String, Integer>>();
		this.weekData = new HashMap<String, HashMap<Integer, Integer>>();
	}
	
	/* Determines if a counter name is a location we're concerned with */
	public boolean isLocation(String location) {
		return !(location.endsWith("IN") || location.endsWith("OUT"));
	}
	
	/* Determines if a data point falls in the season boundaries */
	public boolean inSeason(Calendar date) {
		int month = date.get(Calendar.MONTH);
		return month >= seasonStart && month <= seasonEnd;
	}
	
	/* Determines if the date is a weekday or weekend/holiday */
	public boolean isWeekday(Calendar date, boolean holiday) {
		int day = date.get(Calendar.DAY_OF_WEEK);
		return !holiday && (day == 7 || day == 1);
	}
	
	/* Determines if the hour is during the morning */
	public boolean isMorning(int hour) {
		return hour >= AMStart && hour <= AMEnd;
	}
	
	/* Determines if the hour is during midday */
	public boolean isMidday(int hour) {
		return hour >= midStart && hour <= midEnd;
	}
	
	/*
	 * Parses a csv file and returns the data in a 
	 * hashmap, indexed by location. 
	 */
	public void parse() throws FileNotFoundException, ParseException {
		File file = new File(this.filePath);
		Scanner input = new Scanner(file);
		
		// Grab the locations and their indices from the metadata
		String[] metadata = input.nextLine().split(",");
		ArrayList<Integer> locationIndices = new ArrayList<Integer>();
		
		// Read the rest of the lines in 
		ArrayList<String> lines = new ArrayList<String>();
		while(input.hasNext()) {
		    lines.add(input.nextLine());
		}
		input.close();
		
		// Now initialize the data hashmap by location
		for (int i = 3; i < metadata.length; i++) {
			String location = metadata[i];
			
			if (isLocation(location)) {
				
				// Each location keeps track of the following values
				HashMap<String, Integer> values = new HashMap<String, Integer>();
				values.put("weekend_traffic", 0);
				values.put("weekday_traffic", 0);
				values.put("num_weekends", 0);
				values.put("num_weekdays", 0);
				values.put("morning_traffic", 0);
				values.put("midday_traffic", 0);
				
				this.data.put(location, values);
				
				// Each location also keeps track of the weekly counts
				HashMap<Integer, Integer> weeklyCounts = new HashMap<Integer, Integer>();
				this.weekData.put(location, weeklyCounts);
				
				// Keep track of which indices we should be looking at
				locationIndices.add(i);
			}
		}
		
		// Finally parse the data and populate the hashmap
		for (String line : lines) {
			String[] info = line.split(",");
			
			// Skip any blank lines
			if (line == "") continue;
			
			// Get the date 
			Calendar date = Calendar.getInstance();
			date.setTime(dformat.parse(info[0]));
			
			// Only include within-season information
			if (!inSeason(date)) continue;
			
			// If this datapoint is during a holiday
			int holiday_int = Integer.parseInt(info[1]);
			boolean holiday = holiday_int == 1 ? true : false;
			
			// The time snapshot 
			String time = info[2];
			
			// The week number 
			int week = date.get(Calendar.WEEK_OF_YEAR);
			
			// The hour 
			int hour = Integer.parseInt(time.split(":")[0]);
			
			// Aggregate the counts
			for (int i = 3; i < info.length; i++) {
				// Ignore datapoints with blank aadt or from locations we don't care about
				if (!locationIndices.contains(i)) continue;
				if (info[i] == "") continue;
				
				// Get the aadt and location 
				int aadt = Integer.parseInt(info[i]);
				String location = metadata[i];
				
				// Get this location's value table
				HashMap<String, Integer> values = this.data.get(location);
				
				// Get this location's weekly values table
				HashMap<Integer, Integer> weeklyValues = this.weekData.get(location);
				
				// Days start at 0:00 (midnight)
				if (time == "0:00" || time == "00:00") {
					if (isWeekday(date, holiday)) EcoUtils.inc(values, "num_weekdays", 1);
					else EcoUtils.inc(values, "num_weekends", 1);
				}
				
				// Aggregate the AADT counts
				if (isWeekday(date, holiday)) EcoUtils.inc(values, "weekday_traffic", aadt);
				else EcoUtils.inc(values, "weekend_traffic", aadt);
				
				// Aggregate the AADT counts by week. A new week starts at weekday #1
				weeklyValues.put(week, weeklyValues.get(week) + aadt);
				
				// Increment the morning/midday data if possible
				if (isMorning(hour)) EcoUtils.inc(values, "morning_traffic", aadt);
				else if (isMidday(hour)) EcoUtils.inc(values, "midday_traffic", aadt);
				
			}
		}
		
		// Done - the data has been aggregated. 
	}
	
	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

}
