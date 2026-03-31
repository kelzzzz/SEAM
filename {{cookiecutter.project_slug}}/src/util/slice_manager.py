from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import yaml
from pathlib import Path
from ipaddress import ip_address, IPv4Address, IPv6Address, IPv4Network, IPv6Network
import ipaddress
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "{{ cookiecutter.topology_template }}" / "config" / "topology.yaml"
BOOTSTRAP_PATH = BASE_DIR / "{{ cookiecutter.topology_template }}" / "bootstrap" / "bootstrap.sh"


class SliceManager:

    def __init__(self, fablib_manager):
        with open(CONFIG_PATH, 'r') as f:
            self.topology_cfg = yaml.full_load(f)
        self.fablib = fablib_manager
        self.nodes = []
        self.slice = None
        self.slice_name = self.topology_cfg['slice_name']
        self.component_prefix = "my_seam_network_test"
        self.subnet_prefix = self.topology_cfg['network'][0]['subnet'].split('/')[0][:-1]
        self.subnet = self.topology_cfg['network'][0]['subnet']

    def add_nodes(self):
        #TODO Add switch case to accomodate other network types (not just L2Bridge)
        net = self.slice.add_l2network(
            name=f"l2net_{self.component_prefix}",
            subnet=self.subnet
        )
        
        for node in self.topology_cfg['nodes']:
            for i in range(node['count']):
                n = self.slice.add_node(
                    name=f"{node['name']}_{i}",
                    image=self.topology_cfg['image'],
                    site=self.topology_cfg['site'],
                    cores=node['cores'],
                    ram=node['ram']
                )
                self.nodes.append(n)
                n_iface = n.add_component(
                    model=self.topology_cfg['network'][0]['NIC_model'],
                    name=f"{node['name']}_nic"
                ).get_interfaces()[0]
                n_iface.set_network(net)

    def collect_nodes(self):
        if(not self.slice):
            self.deploy()
        self.nodes = self.slice.get_nodes()
        
    def _ensure_slice_and_nodes(self):
        if not self.slice:
            self.deploy()
        if not self.nodes:
            self.collect_nodes()
        
    def set_subnet_ips(self):
        for i, node in enumerate(self.nodes):
            iface = node.get_interfaces()[0]
            iface.ip_link_up()
            
            target_ip = self.subnet_prefix + str(i+1)
            target_subnet = ipaddress.IPv4Network(self.subnet)
            
            print(f"Configuring {node.get_name()} on {iface.get_device_name()} with {target_ip}...")
            
            iface.ip_addr_add(addr=target_ip, subnet=target_subnet)
            
            stdout, stderr = node.execute(f"ip addr show {iface.get_device_name()}")
            print(f"Validation: {stdout}")
        print("Subnet configuration complete.")

    def get_ips(self):
        self._ensure_slice_and_nodes()
        ip_dict = {}
        for i, node in enumerate(self.nodes):
            ip = self.subnet_prefix + str(i+1)
            node_name = node.get_name()
            if "receiver" in node_name:
                ip_dict['recv'] = ip
            elif "sender" in node_name:
                ip_dict['sndr'] = ip
            elif "worker" in node_name:
                ip_dict[f'w{i}'] = ip
        return ip_dict

    def get_worker_ips(self):
        self._ensure_slice_and_nodes()
            
        ips = []
        for i, node in enumerate(self.nodes):
            ip = self.subnet_prefix + str(i+1)
            if("worker" in node.get_name()):
                ips.append(ip)
        return ips
    

    def get_all_ips_list(self):
        self._ensure_slice_and_nodes()
            
        ips = []
        for i, node in enumerate(self.nodes):
            ips.append(self.subnet_prefix + str(i+1))
        return ips
    
    
    def run_subnet_ping_test(self):
        self._ensure_slice_and_nodes()
        worker_ips = self.get_all_ips_list()
        results = []
        print("Running ping test... please wait...")
        try:
            sender_node = self.slice.get_node(name=self.topology_cfg['nodes'][0]['name'] + "_0")
            
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

    def execute_single_node(self, node, commands, quiet):
        for command in commands:
            print(f'\tExecuting "{command}" on node {node.get_name()}')
            stdout, stderr = node.execute(command, quiet=quiet, output_file=f"{node.get_name()}.log")
            if stderr:
                print(f'Error encountered with "{command}": {stderr}')
        
    def execute_commands(self, node, commands, quiet):
        self._ensure_slice_and_nodes()
        if isinstance(node, list):
            for n in node:
                self.execute_single_node(n, commands, quiet=quiet)
        else:
            self.execute_single_node(node, commands, quiet)

    def upload_src_files_to_nodes(self):
        self._ensure_slice_and_nodes()
        print(str(SRC_DIR))
        print(str(BOOTSTRAP_PATH))
        for i, node in enumerate(self.nodes):
            node.upload_directory(local_directory_path=str(SRC_DIR), remote_directory_path=f"/home/{node.get_username()}")
            node.upload_file(local_file_path=str(BOOTSTRAP_PATH), remote_file_path=f"/home/{node.get_username()}/bootstrap.sh")
        print("Files uploaded.")

    def bootstrap_nodes(self):
        #TODO The bootstrap process is really slow and should be executed on threads soon
        for i, node in enumerate(self.nodes):
            if("worker" in node.get_name()):
                self.execute_commands(node, [f'chmod +x bootstrap.sh', f'./bootstrap.sh', f'python3 src/worker_consume.py {recv_ip}'], quiet=True)
                
        for i, node in enumerate(self.nodes):
            if("sender" in node.get_name()):
                self.execute_commands(node, [f'chmod +x bootstrap.sh', f'./bootstrap.sh', f'python3 src/sender_emit.py {self.get_worker_ips()}'], quiet=True)
                
            if("receiver" in node.get_name()):
                self.execute_commands(node, [f'chmod +x bootstrap.sh', f'./bootstrap.sh', f'python3 src/receiver_recv.py'], quiet=True)
    
    def run_send_work_recv_code(self):
        recv_ip = self.get_ips()['recv']
        
        for i, node in enumerate(self.nodes):
            if("worker" in node.get_name()):
                self.execute_commands(node, [f'python3 src/worker_consume.py  {recv_ip} > worker.log 2>&1 &'], quiet=False)
                
        for i, node in enumerate(self.nodes):
            if("receiver" in node.get_name()):
                self.execute_commands(node, [f'python3 src/receiver_recv.py > recv.log 2>&1 &'], quiet=False)
                
        for i, node in enumerate(self.nodes):
             if("sender" in node.get_name()):
                self.execute_commands(node, [f'sudo python3 src/sender_emit.py "{self.get_worker_ips()}" > sender.log 2>&1 & '], quiet=False)
    
    def stop_on_nodes(self):
        for i, node in enumerate(self.nodes):
            self.execute_commands(node, [f'kill -15 -1'], quiet=False)
            
    def deploy(self):
        print("Creating slice...")
        try: 
            self.fablib.get_slice(name=self.slice_name)
            print(f"Slice {self.slice_name} already exists. Using existing slice.")
            self.slice = self.fablib.get_slice(name=self.slice_name)
            return
        except Exception as e:
            self.slice = self.fablib.new_slice(name=self.slice_name)
            print(f"Created slice: {self.slice_name}")
            print("Adding nodes and network components...")
            self.add_nodes()
            print("Deploying slice...")
            self.slice.submit()

    def setup_nodes(self):
        print("Waiting for slice to be active...")
        self.slice.wait_ssh()
        print("Setting subnet IPs...")
        self.set_subnet_ips()
        print("Uploading source files...")
        self.upload_src_files_to_nodes()
        print("Executing workload on nodes...")
        self.bootstrap_nodes()
        
    def run(self):
        print("Running ping test to validate connectivity...")
        self.run_subnet_ping_test()
        print("Running experiment...")
        self.run_send_work_recv_code()