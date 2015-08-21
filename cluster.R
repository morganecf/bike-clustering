cluster<-function(data, k) {
  copy<-data
  copy$location<-NULL
  km<-kmeans(copy, k)
  plot(copy, col=km$cluster)
 # points(km$centers, pch=8, cex=2)
}

# try standardizing variables? using scale(data)

mtl_data<-read.csv(file='~/ecovis/data/features/mtl_features.csv', header=TRUE)
ottawa_data<-read.csv(file='~/ecovis/data/features/ottawa_features.csv', header=TRUE)
data<-read.csv(file='~/ecovis/data/features/mtl_ott_features.csv', header=TRUE)

cluster(mtl_data, 2)
cluster(mtl_data, 3)
cluster(mtl_data, 4)
