import java.net.HttpURLConnection;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.net.URL;
import java.util.Calendar;
import java.util.HashMap;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/*
 * Java interface for the Eco-Counter REST API. 
 */
public class EcoRest {
	
	private String authToken;
	private String baseStr = "https://api.eco-counter-tools.com/v1/";
	
	/* Requires authentication token */
	public EcoRest(String authToken) {
		this.authToken = authToken;
		this.baseStr += authToken + "/";
	}
	
	/* 
	 * Base method for any HTTP GET request. 
	 */
	private JSONObject httpGet(String urlString) throws IOException, JSONException {
		// Attempt to access the given url 
		URL url = new URL(urlString);
		HttpURLConnection connection = (HttpURLConnection) url.openConnection();
		
		// Make sure page is found 
		if (connection.getResponseCode() != 200) {
			throw new IOException(connection.getResponseMessage());
		}
		
		// Buffer in the response 
		BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream()));
		StringBuilder sb = new StringBuilder();
		String line;
		while ((line = br.readLine()) != null) {
			sb.append(line);
		}
		br.close();
		
		// Add a start key so json decoder can read the string in 
		String resultStr = "{data: " + sb.toString() + "}";
		
		// Disconnect 
		connection.disconnect();
		
		// Return what we read in JSON format
		JSONObject results;
		try {
			results = new JSONObject(resultStr);
		} catch (JSONException e) {
			//e.printStackTrace();
			throw new JSONException("Incorrect JSON.");
		}
		
		return results;
	}
	
	/* Factory method for passing along any string to the get method */
	private JSONObject get(String queryString) {
		try 
		{
			return this.httpGet(this.baseStr + queryString);
		} 
		catch (JSONException e) 
		{
			System.out.println("Could not parse JSON.");
			return new JSONObject();
		} 
		catch (IOException e) 
		{
			System.out.println("IOError.");
			return new JSONObject();
		}
	}
	
	/* 
	 * Get a list of counters.
	 * Ex: https://api.eco-counter-tools.com/v1/<token>/counting_site/share 
	 */
	public JSONObject countingSites() {
		return this.get("counting_site/share");
	}
	
	/*
	 * Get a counting site's individual channel. 
	 * Ex: https://api.eco-counter-tools.com/v1/<token>/counting_site/channels/100011746
	 */
	public JSONObject channel(String cid) {
		return this.get("counting_site/channels/" + cid);
	}
	
	/*
	 * Get data for a given counter id and time step.
	 * (2, 3, 4, 5, 6, 7) => (15m, 1h, day, week, month, year)
	 * Ex: https://api.eco-counter-tools.com/v1/<token>/data/all/100011746?step=2
	 */
	public JSONObject counterData(String cid, String step) {
		return this.get("data/all/" + cid + "?step=" + step);
	}
	
	/*
	 * Get counting site data for a given counting site and step, for one period. 
	 * Ex: https://api.eco-counter-tools.com/v1/<token>/data/all/100011746?begin=20130401&end=20131031&step=2
	 */
	public JSONObject counterDataByPeriod(String cid, String start, String end, String step) {
		return this.get("data/all/" + cid + "?begin=" + start + "&end=" + end + "&step=" + step);
	}

	public static void main(String[] args) throws JSONException {
//		EcoRest er = new EcoRest("zh468c8b");
//		JSONObject obj = er.channel("100011746");
//		System.out.println(obj);
//		System.out.println(((JSONArray)obj.get("data")).length());
		
//		Calendar cal = Calendar.getInstance();
//		System.out.println(cal.getTime());
//		System.out.println(cal.get(Calendar.DAY_OF_WEEK));
//		cal.add(Calendar.DAY_OF_MONTH, 1);
//		System.out.println(cal.get(Calendar.DAY_OF_WEEK));
//		cal.add(Calendar.DAY_OF_MONTH, 1);
//		System.out.println(cal.get(Calendar.DAY_OF_WEEK));
//		cal.add(Calendar.DAY_OF_MONTH, 1);
//		System.out.println(cal.get(Calendar.DAY_OF_WEEK));
		
		
		
	}

}
