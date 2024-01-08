from kafka import KafkaConsumer
from report_pb2 import *
import threading

broker = "localhost:9092"


def consume_reports():
    consumer = KafkaConsumer(bootstrap_servers=[broker])
    consumer.subscribe(["temperatures"])
    _ = consumer.poll(1000)
    # print(consumer.assignment())

    while True:
        batch = consumer.poll(1000)
        for topic_partition, messages in batch.items():
            for msg in messages:
                #print dictionaries corresponding to each message
                #unsure what format of msg is
                final_dict = {}
                final_dict['partition'] = msg.partition
                final_dict['key'] = msg.key.decode("utf-8")
                decoded_value = Report.FromString(msg.value)
                final_dict['date'] = decoded_value.date
                final_dict['degrees'] = decoded_value.degrees
                print(final_dict)
threading.Thread(target=consume_reports).start()
