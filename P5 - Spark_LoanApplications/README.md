# Spark Loan Applications

In this project we analyzed laon applications in Wisconsin. Data was loading into a Hive warehouse in order to easily query data from tables and views. Technologies used:

  - Spark
  - SparkSQL, pyspark
  - HDFS
  - Hive
  - Docker
  - Docker Compose

Docker compose was for deploying a cluster of containers. one container we will run our notebook in, one for our namenode and one for our datanode as our data will be stored in HDFS. In addition to these containers, we will have one for the spark boss, and two spark worker nodes.
Data is loaded into HDFS initially. From there we pull the data into Hive views and tables for analysis with Spark. 
