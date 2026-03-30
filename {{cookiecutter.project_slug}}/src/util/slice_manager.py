from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import yaml
from pathlib import Path
from ipaddress import ip_address, IPv4Address, IPv6Address, IPv4Network, IPv6Network
import ipaddress
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "{{ cookiecutter.topology_template }}" / "config" / "topology.yaml"

with open(CONFIG_PATH, 'r') as f:
    topology_cfg = yaml.full_load(f)

COMPONENT_PREFIX = "{{ cookiecutter.project_slug }}"
SUBNET_PREFIX = topology_cfg['network'][0]['subnet'].split('/')[0][:-1]
SUBNET = topology_cfg['network'][0]['subnet']
SLICE_NAME = topology_cfg['slice_name']
NODES = []

class SliceManager:
    def __init__(self, topology_cfg):
        self.topology_cfg = topology_cfg
        self.slice = None

    def create_slice(self, fablib_manager):
        if fablib_manager.get_slice(name=SLICE_NAME):
            print(f"Slice {SLICE_NAME} already exists. Using existing slice.")
            self.slice = fablib_manager.get_slice(name=SLICE_NAME)
            return
        self.slice = fablib_manager.new_slice(name=SLICE_NAME)
        print(f"Created slice: {SLICE_NAME}")

    def add_nodes(self, fablib_manager):
        #TODO Add switch case to accomodate other network types (not just L2Bridge)
        net = self.slice.add_l2network(name=f"l2net_{COMPONENT_PREFIX}", subnet=SUBNET)
        
        for node in self.topology_cfg['nodes']:
            for i in range(node['count']):
                NODES.append(
                    self.slice.add_node(name=f"{node['name']}_{i}", site=self.topology_cfg['site'], cores=node['cores'], ram=node['ram'])
                )
                n_iface = NODES[i].add_component(
                    model = self.topology_cfg['network'][0]['NIC_model'], name = f"{node['name']}_nic"
                    ).get_interfaces()[0]
                n_iface.set_network(net)
                
    def set_subnet_ips(self):
        for i, n in enumerate(NODES):
            node = slice.get_node(name=n['name'])
            iface = node.get_interfaces()[0]
            iface.ip_link_up()
            
            target_ip = SUBNET_PREFIX + str(i+2)
            target_subnet = ipaddress.IPv4Network(SUBNET)
            
            print(f"Configuring {node.get_name()} on {iface.get_device_name()} with {target_ip}...")
            
            iface.ip_addr_add(addr=target_ip, subnet=target_subnet)
            
            stdout, stderr = node.execute(f"ip addr show {iface.get_device_name()}")
            print(f"Validation: {stdout}")
            
    def run_subnet_ping_test(self):
        worker_ips = [SUBNET_PREFIX + str(i+2) for i in range(3,13)]
        results = []

        try:
            sender_node = slice.get_node(name=topology_cfg['nodes'][0]['name'] + "_0")
            
            for ip in worker_ips:
                stdout, stderr = sender_node.execute(f"ping -c 3 -W 2 {ip}", quiet=True)
                if "3 received" in stdout:
                    status = "✅"
                else:
                    status = "❌"

                results.append({"Target IP": ip, "Status": status})
            
            df = pd.DataFrame(results)
            print(df.to_string(index=False))

        except Exception as e:
            print(f"Error during ping test {e}")
            
    def deploy(self, fablib_manager):
        print("Creating slice...")
        self.create_slice(fablib_manager)
        print("Adding nodes and network components...")
        self.add_nodes(fablib_manager)
        print("Deploying slice...")
        self.slice.submit()
        print("Setting subnet IPs...")
        self.set_subnet_ips()
        print("Slice deployed successfully.")



