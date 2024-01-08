import sys
import grpc
import modelserver_pb2, modelserver_pb2_grpc
import threading
import csv
import torch

lock = threading.Lock()
hits = 0
requests = 0
def main(port, coef, files):
    channel = grpc.insecure_channel(f"localhost:{port}")
    stub = modelserver_pb2_grpc.ModelServerStub(channel)
    
    #SetCoefsRequest and SetCoefResponse
    coefs_floats = [float(x) for x in coef.split(",")]
    resp = stub.SetCoefs(modelserver_pb2.SetCoefsRequest(coefs = coefs_floats))
    print(resp.error)

    """
    local helper function which will be the target for our threads, each thread will run this function
    and return the number of hits and number of requests
    """
    def make_predictions(csv_filename):
        # crit section is when reading row and storing data from predict
        global hits, requests
        with open(csv_filename) as file_obj: # https://www.geeksforgeeks.org/reading-rows-from-a-csv-file-in-python/
            reader_obj = csv.reader(file_obj)
            for row in reader_obj:
                float_tensor = torch.FloatTensor([float(x) for x in row]) # is tensor the right input from client to server?
                resp = stub.Predict(modelserver_pb2.PredictRequest(X=float_tensor))
                with lock:
                    requests += 1
                    y, hit, error =  resp.y, resp.hit, resp.error
                    if hit:
                        hits += 1

    #PredictRequest and PredictResponse
    #need to read files and call predicts on 3 threads while keeping track of hits and requests on each thread respectively
    # t1 = threading.Thread(target=make_predictions, args=[f1])
    # t2 = threading.Thread(target=make_predictions, args=[f2])
    # t3 = threading.Thread(target=make_predictions, args=[f3])
    # t1.start()
    # t2.start()
    # t3.start()
    # t1.join()
    # t2.join()
    # t3.join()
    num_files = len(files)
    threads = []
    for idx in range(num_files):
        file = files[idx]
        threads.append(threading.Thread(target=make_predictions, args=[file]))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    overall_hit_rate = hits/requests if requests != 0 else 0
    print(overall_hit_rate)
    return
    #format of predict: resp = stub.Predict(modelserver_pb2.PredictRequest(X=[input from file])
    # should we have three vars for keeping track of each thread/file and the hits/requests?
    # can we run each thread sequentially such that we dont run into errors using t.start and t.join?
    # format of csv is a row of floats which will become X

if __name__ == "__main__":
    print(sys.argv)
    port = sys.argv[1]
    coef = sys.argv[2]
    files = sys.argv[3:]
    
    main(port, coef, files)
