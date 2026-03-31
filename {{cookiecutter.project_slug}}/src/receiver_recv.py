import socket
import csv
import os
from schema import Schema
from util.binn_helper import BinnHelper

class Receiver:
    #TODO Multiple choices for sinks (not just CSVs by default)
    def __init__(self, schema_cls, sink_path="sink.csv"):
        self.sink_path = sink_path
        self.schema_cls = schema_cls
        self.fields = list(self.schema_cls.__annotations__.keys())

        if not os.path.exists(self.sink_path):
            with open(self.sink_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.fields)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', 7000))
            s.listen(10)
            
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        recv = BinnHelper.unpack(data, self.schema_cls)
                        row = [getattr(recv, field) for field in self.fields]
                        
                        with open(self.sink_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(row)

if __name__ == "__main__":
    receiver = Receiver(Schema)
    receiver.start()