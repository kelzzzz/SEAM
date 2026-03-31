import sys

from scapy.all import IP, UDP, Send, Raw
import json

class Sender:
    def __init__(self, worker_ips):
        self.worker_ips = worker_ips
        self.port = 5000

    def get_packet(self, worker_id):
        #This is the user defined logic, using my test case for now
        data = {
            "task_id": worker_id,
            "samples": 10**5,
            "seed": worker_id * 123
        }
        return json.dumps(data)

    def emit(self):
        for i, ip in enumerate(self.worker_ips):
            payload = self.get_packet(i)
            
            pkt = IP(dst=ip) / UDP(dport=self.port) / Raw(load=payload)
            
            print(f" Sending packet to {ip}...")
            send(pkt, verbose=False)
            
if __name__ == "__main__":
    worker_ips = sys.argv[1].replace(" ", "").replace("[", "").replace("]", "").replace("'","").split(",") if len(sys.argv) > 1 else sys.exit("Usage: python sender_emit.py <worker_ips_comma_separated>")
    sender = Sender(worker_ips=worker_ips)
    sender.emit()