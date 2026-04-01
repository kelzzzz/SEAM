from scapy.all import sniff, IP, UDP, Raw
import json
import random
import socket
import sys
import socket
from schema import Schema
from util.binn_helper import BinnHelper

class Worker:
    def __init__(self, receiver_ip, interface="enp7s0"):
        self.receiver_ip = receiver_ip
        self.interface = interface

    def compute(self, data):
        #This is the user defined logic, using my test case for now
        hits = 0 
        samples = data.get('samples', 0)
        seed = data.get('seed', 0)
        
        random.seed(seed)
        
        for _ in range(samples):
            if random.random()**2 + random.random()**2 <= 1.0:
                hits += 1
        
        result = Schema(worker_id=data.get('task_id'), hits=hits, total=samples)
        return result
    
    def decode_packet(self, pkt):
            if pkt.haslayer(Raw):
                try:
                    return json.loads(pkt[Raw].load.decode())
                except Exception:
                    return None
            return None
    
    def packet_callback(self, pkt):
        if pkt.haslayer(Raw):
            try:
                payload = self.decode_packet(pkt)
                if not payload: return
                
                result = self.compute(payload)
                binary_payload = BinnHelper.pack(result)
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rs:
                    rs.settimeout(5)
                    rs.connect((self.receiver_ip, 7000))
                    rs.sendall(binary_payload)
                    print(f"Result sent to {self.receiver_ip}")
            except Exception as e:
                print(f"Error processing packet: {e}")

    def start(self):
        dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dummy_sock.bind(('0.0.0.0', 5000)) 
        
        print(f"Sniffing for messages on {self.interface}...")
        sniff(iface=self.interface, filter="udp port 5000", prn=self.packet_callback)

if __name__ == "__main__":
    worker = Worker(receiver_ip=sys.argv[1] if len(sys.argv) > 1 else sys.exit("Usage: python worker_consume.py <receiver_ip>"))
    worker.start()