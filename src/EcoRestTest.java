import static org.junit.Assert.*;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.junit.Test;

public class EcoRestTest {
	
	EcoRest er = new EcoRest("zh468c8b");

	@Test
	public void testCountingSites() throws JSONException {
		JSONObject data = er.countingSites();
		
		// Sites should be returned in an array
		assert(data.get("data") instanceof JSONArray);
		
		// There should be at least one site 
		assert(((JSONArray)data.get("data")).length() > 0);
	}
	
	@Test
	public void testChannel() throws JSONException {
		String counter_id = "100011746";
		JSONArray data = (JSONArray) er.channel(counter_id).get("data");
		
		// There are two results here (as of August) 
		assert(data.length() == 2);
		
		// One of them has this id 101011746
		assert(((JSONObject)data.get(0)).get("id") == "101011746");
		
		// The other has this id 102011746
		assert(((JSONObject)data.get(1)).get("id") == "101011746");
	}
	
	@Test
	public void testCounterData() {
		// (2, 3, 4, 5, 6, 7) => (15m, 1h, day, week, month, year)
		
		// Test 15 minute increments
		// Test 1 hour increments
		// Test 1 day increments
		// Test 1 week increments
		// Test 1 month increments
		// Test 1 year increments
		
		// TODO
	}
	
	@Test
	public void testCounterDataByPeriod() {
		// TODO
	}
	

}
