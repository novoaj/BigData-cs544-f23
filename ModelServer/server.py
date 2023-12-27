import torch
from collections import deque
import threading
import grpc
import modelserver_pb2, modelserver_pb2_grpc
from concurrent import futures

class ModelServer(modelserver_pb2_grpc.ModelServerServicer):
    def __init__(self):
        self.pred_cache = PredictionCache()
    def SetCoefs(self, request, context):
        print("ModelServer: SetCoefs method")
        nums =[]
        for num in request.coefs:
            nums.append(num)
        nums_tensor = torch.FloatTensor(nums) # this format needs to be 1 col at some point
        
        self.pred_cache.SetCoefs(nums_tensor)
        return modelserver_pb2.SetCoefsResponse(error = "") #important
    def Predict(self, request, context):
        print("ModelServer: Predict method")
        nums = []
        for num in request.X:
            nums.append(num)
        nums_tensor = torch.FloatTensor(nums)
        result = self.pred_cache.Predict(nums_tensor)
        return modelserver_pb2.PredictResponse(y=result[0],hit = result[1], error ="")  #important



lock = threading.Lock()
class PredictionCache():
    def __init__(self):
        self.coefs = torch.empty((1,1), dtype=torch.float32)
        self.lru_cache = {} # max capacity 10
        self.evict_order = deque([])
    def SetCoefs(self,coefs):
        with lock:
            self.coefs = coefs
            self.lru_cache = {}
            self.evict_order = deque([])
    def Predict(self,X):
        rounded = torch.round(X, decimals=4)

        hit = False
        key = tuple(rounded.flatten().tolist())
        cache_size = 10
        with lock:
        # begin LRU cache
            if key in self.lru_cache:    #if it is a hit, move to the right (end of the list)
                hit = True
                self.evict_order.remove(key)
                self.evict_order.append(key)
                y = self.lru_cache[key]
            else:                       #if it is a miss,(1) check if cache is full (2)if it is full, evict
                hit = False
                y = X @ self.coefs

                self.lru_cache[key] = y
                self.evict_order.append(key)

            # check if cache is full
                if len(self.lru_cache) > cache_size:
                    # evict
                    evicted = self.evict_order.popleft()
                    self.lru_cache.pop(evicted)



        return y, hit

server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options=(('grpc.so_reuseport', 0),))
modelserver_pb2_grpc.add_ModelServerServicer_to_server(ModelServer(), server)
server.add_insecure_port("[::]:5440", )
server.start()
server.wait_for_termination()
