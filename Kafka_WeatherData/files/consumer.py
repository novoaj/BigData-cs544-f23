from kafka import KafkaConsumer, TopicPartition
from report_pb2 import *
import threading
import sys
import os
import json

broker = "localhost:9092"
"""
consumer should be manually assigned to topic partitions depending on what the input is
"""
def consume_messages(partitions):
    consumer = KafkaConsumer(bootstrap_servers=[broker])
    topic_partitions = [] # list of TopicPartition objects
    partition_data_dict = {} # maps partition_num : partition-N.json in dict format
    partition_num_tp = {}
    for partition in partitions:
        filename = f"/files/partition-{partition}.json"
        if not os.path.isfile(filename): # https://www.python-engineer.com/posts/check-if-file-exists/
            with open(filename, "w") as f:
                print("writing to file, partition: ", partition)
                json.dump({"partition":partition, "offset":0}, f) # check if partition-N.json exists, if not init {"partition":N, "offset":0}
        # load file as dict and store in partitions_data_dict
        with open(filename) as f:
            partition_data_dict[partition] = json.load(f)
        # append to topic_partitions for when we assign consumer
        topic_part = TopicPartition("temperatures", partition)
        print(topic_part)
        topic_partitions.append(topic_part)
        partition_num_tp[partition] = topic_part
    
    print("topic_partitions list: ", topic_partitions)
    consumer.assign(topic_partitions)
    print(consumer.assignment())
    # use offset to "seek" to offset to start consuming messages - https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html
    # grab batches and after each batch, update offsets in dictionaries and write to json files
    for partition in partitions:
        # offset is going to be at aprtition_data_dict[0]["offset"]
        offset = partition_data_dict[0]["offset"]
        consumer.seek(partition_num_tp[partition], offset)
    def date_is_greater(d1, d2):
        # returns true if d1 is greater than d2
        # dates in YYYY-MM-DD format (assumer year and month is the same so just compare date)
        return int(d1[-2:]) > int(d2[-2:])

        pass
    while True:
        # print("getting batch...")
        batch = consumer.poll(1000)
        for tp, messages in batch.items():
            curr_offset = None
            curr_partition = None
            for msg in messages:
                curr_offset = consumer.position(tp) #  msg.offset
                curr_key = msg.key.decode("utf-8")
                curr_value = Report.FromString(msg.value)
                curr_partition = msg.partition
                curr_date = curr_value.date
                curr_degrees = curr_value.degrees
                if (curr_degrees > 500.0): # dataset has some 1,000,000 in it
                    continue
                partition_data_dict[curr_partition]["offset"] = curr_offset
                # partition_data_dict[curr_partition] have we seen this month before? this year? update count,sum,avg, check if end or start
                if not curr_key in partition_data_dict[curr_partition]:
                    partition_data_dict[curr_partition][curr_key] = {}   # init empty dict at partition:month
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]] = {}
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["count"] = 1
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["sum"] = curr_degrees
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["avg"] = curr_degrees / 1
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["end"] = curr_date
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["start"] = curr_date
                elif curr_key in partition_data_dict[curr_partition] and not curr_date[:4] in partition_data_dict[curr_partition][curr_key]:
                    # this year not yet init in this month
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]] = {} # init dict at partition:month:year
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["count"] = 1
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["sum"] = curr_degrees
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["avg"] = curr_degrees / 1
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["end"] = curr_date
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["start"] = curr_date
                else:
                    # is curr_date <= end skip it (?)
                    if date_is_greater(partition_data_dict[curr_partition][curr_key][curr_date[:4]]["end"], curr_date):
                        continue
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["count"] += 1 # updating partition:month:year dictionary
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["sum"] += curr_degrees
                    sum_degrees = partition_data_dict[curr_partition][curr_key][curr_date[:4]]["sum"]
                    count =  partition_data_dict[curr_partition][curr_key][curr_date[:4]]["count"]
                    partition_data_dict[curr_partition][curr_key][curr_date[:4]]["avg"] = sum_degrees / count
                    end_date = partition_data_dict[curr_partition][curr_key][curr_date[:4]]["end"]
                    start_date = partition_data_dict[curr_partition][curr_key][curr_date[:4]]["start"]
                    # is curr_date a start or end date?
                    # we expect the dates to be given in order [1,2,3,...,31], with the exception of duplicate, if dupe, skip
                    if date_is_greater(curr_date, end_date):
                        # curr_date is our new end_date
                        partition_data_dict[curr_partition][curr_key][curr_date[:4]]["end"] = curr_date
                    # elif date_is_greater(start_date, curr_date):
                        # curr_date is new start_date
                        # partition_data_dict[curr_partition][curr_key][curr_date[:4]]["start"] = curr_date
                    else:
                        pass # do nothing

            # write partition_data_dict[curr_partition] to partition-{partition}.json file
            path = f"/files/partition-{curr_partition}.json"
            path2 = path + ".tmp"
            with open(path2, "w") as f:
                print(f"writing partition {curr_partition} data")
                json.dump(partition_data_dict[curr_partition], f)
                os.rename(path2, path)
if __name__ == "__main__":
    args = sys.argv # args is list of ints representing partitions this consumer should be assigned to
    partitions = list(map(int, args[1:]))
    # experiment with threads and splitting up partitions
    t1 = threading.Thread(target=consume_messages, args=(partitions,)) #https://docs.python.org/3/library/threading.html
    print("starting thread...")
    t1.start()
