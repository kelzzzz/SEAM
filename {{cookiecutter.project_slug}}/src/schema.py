#This is user defined
#For now just using the schema I will be testing with
class Schema:
    worker_id: int
    hits: int
    total: int
    
    def __init__(self, worker_id, hits, total):
        self.worker_id = worker_id
        self.hits = hits
        self.total = total