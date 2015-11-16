import java.util.HashMap;
import java.util.Map;

import weka.core.Instances;
import weka.core.Attribute;
import weka.core.FastVector;
import weka.core.Instance;
import weka.clusterers.DensityBasedClusterer;
import weka.clusterers.EM;
import weka.clusterers.SimpleKMeans;
import weka.clusterers.ClusterEvaluation;

import java.io.BufferedReader;
import java.io.FileReader;

/*
 * Clustering pipeline - given all of the aggregated data 
 * for a set of counter locations.   
 */
public class EcoCluster {
	
	/* The number of counters being clustered */
	int numClusters = 0;
	
	/* Used for PPI feature ratio */
	static int topMonths = 12;
	
	/* HashMap containing a city's parsed, aggregated data, by counter location */
	HashMap<String, HashMap<String, Integer>> data;
	
	/* HashMap containing a city's data aggregated by each day of the week */
	HashMap<String, HashMap<Integer, Integer>> weekData; 
	
	/* HashMap containing a city's indexes (features) */
	HashMap<String, double[]> features;
	
	/* Array of counter names */
	String[] counters;
	
	/* The resulting cluster assignment - corresponds to indexing of this.counters */
	int[] clusters;
	
	public EcoCluster(HashMap<String, HashMap<String, Integer>> data, HashMap<String, HashMap<Integer, Integer>> weekData) {
		// Might want to deep copy this? 
		this.data = data;
		this.weekData = weekData;
		this.numClusters = data.keySet().size();
		this.counters = new String[this.numClusters];
		
		// Keep the ordering of counters fixed 
		int i = 0;
		for (String location : this.data.keySet()) {
			this.counters[i] = location;
			i++;
		}
	}
	
	/*
	 * For each counter location, calculates the indexes used as 
	 * features in the clustering analysis. 
	 */
	public void getFeatures() {
		// Keep track of locations that don't have data ?
		//ArrayList<String> no_data = new ArrayList<String>();
		for (String location : this.data.keySet()) {
			HashMap<String, Integer> values = this.data.get(location);
		    double num_days = (double) (values.get("num_weekends") + values.get("num_weekdays"));
		    
		    if (num_days == 0) {
		    	System.out.println(location + " has no AADT");
		    	//no_data.add(location);
		    	continue;
		    }
		    
		    // WWI (ratio of average daily weekend traffic to average daily weekday traffic)
		    double avg_daily_weekend_traffic = values.get("weekend_traffic") / (double) values.get("num_weekends");
		    double avg_daily_weekday_traffic = values.get("weekday_traffic") / (double) values.get("num_weekdays");
		    double WWI = avg_daily_weekend_traffic / avg_daily_weekday_traffic;
		    
		    // AMI (ratio of average morning to midday traffic)
		    double avg_morning_traffic = values.get("morning_traffic") / num_days;
		    double avg_midday_traffic = values.get("midday_traffic") / num_days;
		    double AMI = avg_morning_traffic / avg_midday_traffic;
		    
		    // PPI (avg of top 12 weeks / avg of following 20)
		    Map<Integer, Integer> sorted = EcoUtils.sortByValue(this.weekData.get("location"));
		    int top = 0;
		    int bottom = 0;
		    int counter = 0;
		    for (Integer week : sorted.keySet()) {
		    	if (counter < topMonths) top += sorted.get(week);
		    	else bottom += sorted.get(week);
		    	counter++;
		    }
		    double top_average = top / (double) topMonths;
		    double bottom_average = bottom / (double) (counter - topMonths);
		    double PPI = top_average / bottom_average;
		    
		    // Add features for this location 
		    double[] indexes = {WWI, AMI, PPI};
		    this.features.put(location, indexes);
		}
	}
	
	/*
	 * Parse into Weka-compatible feature format. This is 
	 * done separately/after the above method since multiple
	 * clustering methods from different libraries were tested. 
	 */
	public Instances getWekaFeatures() {
		
		// Define the Weka features 
		Attribute WWI = new Attribute("WWI");
		Attribute AMI = new Attribute("AMI");
		Attribute PPI = new Attribute("PPI");
		
		// Create the Weka feature vector prototype
		FastVector featureVector = new FastVector(3);
		featureVector.addElement(WWI);
		featureVector.addElement(AMI);
		featureVector.addElement(PPI);
		
		// Initialize the Weka training set 
		Instances trainingSet = new Instances("train", featureVector, this.numClusters);
		
		for (String location : this.counters) {
			double[] indexes = this.features.get(location);
			
			// Create the instance
			Instance instance = new Instance(3);
			instance.setValue((Attribute) featureVector.elementAt(0), indexes[0]);
			instance.setValue((Attribute) featureVector.elementAt(1), indexes[1]);
			instance.setValue((Attribute) featureVector.elementAt(2), indexes[2]);
			
			// Add the instance
			trainingSet.add(instance);
		}
		 
		return trainingSet;
	}
	
	/*
	 * Use Weka's Kmeans clustering to cluster the counters. 
	 * 
	 * TODO: Kmeans exception handling
	 */
	public void cluster(Instances trainingSet) throws Exception {
		SimpleKMeans kmeans = new SimpleKMeans();
		
		// CONFIGURE THIS
		kmeans.setSeed(10);
		
		// Set training parameters
		kmeans.setPreserveInstancesOrder(true);
		kmeans.setNumClusters(4);
		
		// Cluster
		kmeans.buildClusterer(trainingSet);
		
		// Get the cluster assignments 
		this.clusters = kmeans.getAssignments();
	}
	
	public void printClusterAssignments() {
		for (int i = 0; i < this.clusters.length; i++) {
			System.out.println(this.counters[i] + ": " + this.clusters[i]);
		}
	}


}
