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
 * 
 * TODO: everything should be private, client should only 
 * be able to access final aadb estiamte, confidence interval, 
 * and correlation. 
 */
public class EcoCluster {
	
	/* API token */
	String authToken;
	
	/* Used for PPI feature ratio */
	static int topMonths = 12;
	
	/* Long-term aggregated data */
	HashMap<String, HashMap<String, Integer>> longTermData;
	HashMap<String, HashMap<Integer, Integer>> longTermWeekData;
	
	/* Short-term aggregated data */
	HashMap<String, HashMap<String, Integer>> shortTermData;
	HashMap<String, HashMap<Integer, Integer>> shortTermWeekData;
	
	/* The long-term features (indexes) */
	HashMap<String, double[]> longTermFeatures;
	
	/* The short-term features (indexes) */
	HashMap<String, double[]> shortTermFeatures;
	
	/* Array of counter names */
	String[] counters;
	
	/* Short-term counter */
	String counter;
	
	/* The resulting cluster assignment - corresponds to indexing of this.counters */
	int[] clusters;
	
	/* Step size */
	String step;
	
	/* Feature prototypes */
	Attribute WWI;
	Attribute AMI;
	Attribute PPI;
	FastVector featureVector;
	
	/* Training featureset */
	Instances trainingSet;
	
	/* The result elements */
	int AADBEstimate;
	double[] confidenceInterval;
	double correlation;
	
	/* 
	 * @param shortTermId the short-term counter id
	 * @param longTermIds a list of long-term counter ids
	 * @param start the start date for the long-term data
	 * @param end the end date for the long-term data
	 * @param step the step size (hour, day, week, etc)
	 */
	public EcoCluster(String authToken, String[] longTermIds, String start, String end, String step) {
		this.authToken = authToken;
		this.step = step;
		this.counters = longTermIds;
		this.longTermFeatures = new HashMap<String, double[]>();
		
		// Fetch the data
		EcoParser longEP = new EcoParser(longTermIds, start, end, step);
		longEP.getData(authToken);
		this.longTermData = longEP.data;
		this.longTermWeekData = longEP.weekData;
		
		// Define the Weka features 
		this.WWI = new Attribute("WWI");
		this.AMI = new Attribute("AMI");
		this.PPI = new Attribute("PPI");
				
		// Create the Weka feature vector prototype
		this.featureVector = new FastVector(3);
		featureVector.addElement(WWI);
		featureVector.addElement(AMI);
		featureVector.addElement(PPI);
		
		this.clusters = null;
	}
	
	/*
	 * For each counter location, calculates the indexes used as 
	 * features in the clustering analysis. 
	 */
	public void getFeatures(HashMap<String, HashMap<String, Integer>> data, HashMap<String, HashMap<Integer, Integer>> weekData, HashMap<String, double[]> features) {
		// Keep track of locations that don't have data ?
		//ArrayList<String> no_data = new ArrayList<String>();
		for (String location : data.keySet()) {
			HashMap<String, Integer> values = data.get(location);
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
		    Map<Integer, Integer> sorted = EcoUtils.sortByValue(weekData.get("location"));
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
		    features.put(location, indexes);
		}
	}
	
	/*
	 * Create the training feature set - parse into Weka-compatible features.
	 * This is decoupled from this.getFeatures() so that the latter can be 
	 * used for both short- and long-term counters. 
	 */
	public void createTrainingFeatures() {
		getFeatures(this.longTermData, this.longTermWeekData, this.longTermFeatures);
		
		// Initialize the Weka training set 
		this.trainingSet = new Instances("train", this.featureVector, this.counters.length);
				
		for (String location : this.counters) {
			double[] indexes = this.longTermFeatures.get(location);
			
			// Create the instance
			Instance instance = new Instance(3);
			instance.setValue((Attribute) this.featureVector.elementAt(0), indexes[0]);
			instance.setValue((Attribute) this.featureVector.elementAt(1), indexes[1]);
			instance.setValue((Attribute) this.featureVector.elementAt(2), indexes[2]);
			
			// Add the instance
			trainingSet.add(instance);
		}
	}
	
	
	/*
	 * Use Weka's Kmeans clustering to cluster the counters. 
	 * 
	 * TODO: Kmeans exception handling
	 */
	public void cluster() throws Exception {
		SimpleKMeans kmeans = new SimpleKMeans();
		
		// CONFIGURE THIS
		kmeans.setSeed(10);
		
		// Set training parameters
		kmeans.setPreserveInstancesOrder(true);
		kmeans.setNumClusters(4);
		
		// Cluster
		kmeans.buildClusterer(this.trainingSet);
		
		// Get the cluster assignments 
		this.clusters = kmeans.getAssignments();
	}
	
	public void printClusterAssignments() {
		for (int i = 0; i < this.clusters.length; i++) {
			System.out.println(this.counters[i] + ": " + this.clusters[i]);
		}
	}
	
	/*
	 * Classify a given short-term counter id. 
	 */
	public void classify(String shortTermId) {
		// TODO: Error handling -- cannot call this unless the
		// clustering has already been performed. 
		if (this.clusters == null) {
			System.out.println("Cluster first.");
			return;
		}
		
		// Get the data associated with this counter 
		EcoParser shortEP = new EcoParser(shortTermId, this.step);
		shortEP.getData(this.authToken);
		this.shortTermData = shortEP.data;
		this.shortTermWeekData = shortEP.weekData;
		
		// Initialize features
		this.shortTermFeatures = new HashMap<String, double[]>();
		
		// Calculate features 
		this.getFeatures(this.shortTermData, this.shortTermWeekData, this.shortTermFeatures);
		
		// Create the Weka instance 
		double[] indexes = this.shortTermFeatures.get(shortTermId);
		Instance instance = new Instance(3);
		instance.setValue((Attribute) this.featureVector.elementAt(0), indexes[0]);
		instance.setValue((Attribute) this.featureVector.elementAt(1), indexes[1]);
		instance.setValue((Attribute) this.featureVector.elementAt(2), indexes[2]);
		
		// Find the cluster with the highest correlation
		
	}

	/*
	 * Extrapolate AADB based on closest long-term counter.
	 * Calculate the confidence interval. 
	 */
	public void extrapolate() {
	}
	
	
	/*
	 * Getter methods for classification results. 
	 */
	
	public int getAADBEstimate() {
		return this.AADBEstimate;
	}
	
	public double getCorrelation() {
		return this.correlation;
	}
	
	public double[] getConfidenceInterval() {
		return this.confidenceInterval;
	}

}
