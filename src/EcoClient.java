
/*
 * Sample class to show how to use the clustering pipeline. 
 * 
 * NOTE: These values won't work because the API doesn't seem to be 
 * returning any data. 
 */
public class EcoClient {

	public static void main(String args) throws Exception {
		// The long-term counter ids 
		String[] longTermIds = {"100025495", "100025498", "100025494", "100011603", "100025307", "100025306", "100025305" ,"100025304", "100025303"};
		
		// The query parameters
		String authToken = "zh468c8b";
		String start = "20130401";
		String end = "20131031";
		String step = "2";
		
		// Cluster the long-term counters
		EcoCluster ec = new EcoCluster(authToken, longTermIds, start, end, step);
		ec.createTrainingFeatures();
		ec.cluster();
		
		// Look at the cluster assignments 
		ec.printClusterAssignments();
		
		// The short-term counter id
		String shortTermId = "100026912";
		
		// Classify the counter into a cluster 
		ec.classify(shortTermId);
		
		// Extrapolate the AADB
		ec.extrapolate();
		
		// Get the results
		System.out.println(ec.getAADBEstimate());
		System.out.println(ec.getCorrelation());
		System.out.println(ec.getConfidenceInterval());
		
	}
}
