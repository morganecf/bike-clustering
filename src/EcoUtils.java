import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

public class EcoUtils {
	
	/* Helper function to sort a hashmap by value (decreasing) */
	public static <K, V extends Comparable<? super V>> Map<K, V> sortByValue(Map<K, V> map) {
	    List<Map.Entry<K, V>> list = new LinkedList<Map.Entry<K, V>>(map.entrySet());
	    Collections.sort(list, new Comparator<Map.Entry<K, V>>() {
	        public int compare(Map.Entry<K, V> o1, Map.Entry<K, V> o2) {
	            return (o2.getValue()).compareTo(o1.getValue());
	        }
	    } );
	    Map<K, V> result = new LinkedHashMap<K, V>();
	    for (Map.Entry<K, V> entry : list) {
	        result.put(entry.getKey(), entry.getValue());
	    }
	    return result;
	}
	
	/* Helper function to increment a hashmap value */
	public static void inc(HashMap<String, Integer> hashmap, String key, int val) {
		hashmap.put(key, hashmap.get(key) + val);
	}
	
	public static void main(String[] args) {
		HashMap<String, Integer> map = new HashMap<String, Integer>();
		map.put("morgane", 5);
		map.put("gaetan", 10);
		map.put("thierry", 21);
		map.put("brigitte", 6);
		
		Map<String, Integer> result = sortByValue(map);
		for (String s : result.keySet()) {
			System.out.println(s);
			System.out.println(result.get(s));
			System.out.println();
		}
	}
	
}
