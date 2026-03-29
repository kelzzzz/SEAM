from scapy.all import sniff, IP, UDP
import json
import random
import socket
from schema import Schema
from util.binn_helper import BinnHelper

class Worker:
    def __init__(self, receiver_ip, interface="eth1"):
        self.receiver_ip = receiver_ip
        self.interface = interface

    def compute(self, data):
        #This is the user defined logic, using my test case for now
        
        result = Schema(worker_id=data.get('task_id'), hits=0, total=data.get('samples', 0))
        samples = data.get('samples', 0)
        random.seed(data.get('seed', 0))
        
        for _ in range(samples):
            if random.random()**2 + random.random()**2 <= 1.0:
                hits += 1
                
        result.hits = hits
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
                result = self.compute(payload)
                binary_payload = BinnHelper.pack(result)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rs:
                    rs.connect((self.receiver_ip, 6000))
                    rs.sendall(binary_payload)
            except Exception as e:
                print(f"Error processing packet: {e}")

    def start(self):
        print(f"Sniffing for messages on {self.interface}...")
        sniff(iface=self.interface, filter="udp port 5000", prn=self.packet_callback)