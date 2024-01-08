from kafka import KafkaAdminClient, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import UnknownTopicOrPartitionError
from report_pb2 import *
import weather
import time

broker = 'localhost:9092'
admin_client = KafkaAdminClient(bootstrap_servers=[broker])

try:
    admin_client.delete_topics(["temperatures"])
    print("Deleted topics successfully")
except UnknownTopicOrPartitionError:
    print("Cannot delete topic/s (may not exist yet)")

time.sleep(3) # Deletion sometimes takes a while to reflect

# TODO: Create topic 'temperatures' with 4 partitions and replication factor = 1
admin_client.create_topics([NewTopic("temperatures", 4, 1)])

print("Topics:", admin_client.list_topics())
# https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html
producer = KafkaProducer(bootstrap_servers=[broker], retries=10, acks="all")
def getMonth(date):
    """
    date is string in YYYY-MM-DD format
    """
    MM_month = {"01": "January", "02": "February", "03": "March", "04": "April", "05":"May", "06": "June", "07": "July", "08": "August", "09":"September", "10": "October", "11":"November", "12": "December"}
    return MM_month[date[5:7]]
for date, degrees in weather.get_next_weather(delay_sec=0.1):
    key = getMonth(date)
    value = Report(date=date, degrees=degrees).SerializeToString()
    producer.send("temperatures", value, bytes(key, "utf-8"))
    # print(key, value)
