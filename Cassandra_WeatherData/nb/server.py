import grpc
import station_pb2
import station_pb2_grpc
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra import ConsistencyLevel, Unavailable
from concurrent import futures
#https://docs.datastax.com/en/drivers/java/2.0/com/datastax/driver/core/exceptions/NoHostAvailableException.html
#https://docs.datastax.com/en/drivers/java/2.0/com/datastax/driver/core/exceptions/UnavailableException.html

class Server(station_pb2_grpc.StationServicer):
    def __init__(self):
        self.cluster = Cluster(['p6-db-1', 'p6-db-2', 'p6-db-3'])
        self.cass = self.cluster.connect()
    def RecordTemps(self, request, context):
        #will insert new temperature highs/lows to weather.stations'
        # access args from request => request.[param]
        try: 
            insert_statement = self.cass.prepare("""
                INSERT INTO weather.stations (id, date, record)
                VALUES (?, ?, { tmin: ?, tmax: ? })
                """)
            insert_statement.consistency_level = ConsistencyLevel.ONE
            self.cass.execute(insert_statement, (request.station, request.date, request.tmin, request.tmax))
            return station_pb2.RecordTempsReply(error="")
        except Unavailable as e:
            error_msg = f"need {e.required_replicas} replicas, but only have {e.alive_replicas}"
            return station_pb2.RecordTempsReply(error=error_msg)
        except NoHostAvailable as e: # NoHostAvailable returns a hashmap
            for addr, error in e.errors.items():
                # https://www.programiz.com/python-programming/methods/built-in/isinstance
                if isinstance(error, Unavailable):
                    error_msg = f"need {error.required_replicas} replicas, but only have {error.alive_replicas}"
                    return station_pb2.RecordTempsReply(error=error_msg)
            return station_pb2.RecordTempsReply(error=f"NoHostAvailable: {str(e)}")
        except Exception as e:
            error_msg = f"error while inserting: {str(e)}"
            return station_pb2.RecordTempsReply(error=error_msg)
            

    def StationMax(self, request, context):
        # StationMax will return the maximum tmax ever seen for the given station
        try: 
            max_statement = self.cass.prepare("""
                SELECT MAX(record.tmax) FROM weather.stations WHERE id = ?
            """)
            max_statement.consistency_level = ConsistencyLevel.THREE
            res = self.cass.execute(max_statement, (request.station,)).one()[0] # extra comma makes second param into tuple which is expected type
            return station_pb2.StationMaxReply(error="", tmax = res)
        except Unavailable as e:
            error_msg = f"need {e.required_replicas} replicas, but only have {e.alive_replicas}"
            return station_pb2.StationMaxReply(error=error_msg)
        except NoHostAvailable as e: # NoHostAvailable returns a hashmap
            for addr, error in e.errors.items():
                # https://www.programiz.com/python-programming/methods/built-in/isinstance
                if isinstance(error, Unavailable):
                    error_msg = f"need {error.required_replicas} replicas, but only have {error.alive_replicas}"
                    return station_pb2.StationMaxReply(error=error_msg)
            return station_pb2.StationMaxReply(error=f"NoHostAvailable: {str(e)}")
        except Exception as e:
            error_msg = f"error while querying: {str(e)}"
            return station_pb2.StationMaxReply(error=error_msg)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options=(('grpc.so_reuseport', 0),))
station_pb2_grpc.add_StationServicer_to_server(Server(), server)
server.add_insecure_port("[::]:5440", )
server.start()
server.wait_for_termination()
