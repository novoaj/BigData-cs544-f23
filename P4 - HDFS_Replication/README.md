# HDFS Replication

This project was for exploring HDFS as a storage solution. Specifically, exploring fault tolerance as well as data storage/retrieval. Technologies used:
   
  - Python
  - Docker
  - Docker Compose
  - HDFS
  - PyArrow

Deployed a small HDFS cluster using Docker and Docker Compose on a GCP virtual machine. Wrote python code to interact with HDFS via the webHDFS  API to upload and read files and PyArrow is used for reading and analyzing HDFS files. Challenges include managing replication setting to balance space efficiency and fault tolerance. 
