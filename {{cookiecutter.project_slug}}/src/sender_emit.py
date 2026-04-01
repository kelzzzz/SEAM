import sys
from scapy.all import IP, UDP, send, Raw
import json
import random
import time

class Sender:
    def __init__(self, worker_ips):
        self.worker_ips = worker_ips
        self.port = 5000

    def get_packet(self, worker_id):
        #This is the user defined logic, using my test case for now
        data = {
            "task_id": worker_id,
            "samples": 10**5,
            "seed": worker_id * random.randint(1, 1000)
        }
        return json.dumps(data)

    def emit(self):
        for i, ip in enumerate(self.worker_ips):
            payload = self.get_packet(i)
            
            pkt = IP(dst=ip) / UDP(sport=5001, dport=self.port) / Raw(load=payload)
            
            print(f" Sending packet to {ip}...")
            send(pkt, verbose=False)
            
if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
        clean_input = raw_input.translate(str.maketrans('', '', "[]'\" "))
        worker_ips = [ip for ip in clean_input.split(",") if ip]
    else:
        sys.exit("Usage: python3 sender_emit.py <worker_ips>")
        
    sender = Sender(worker_ips=worker_ips)
    
    while(True):
        time.sleep(1)
        sender.emit()