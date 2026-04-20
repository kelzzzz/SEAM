from .abstract_slice_manager import AbstractSliceManager
import ipaddress
import pandas as pd

class swr_basic_slice_manager(AbstractSliceManager):
    def set_yaml_variables(self):
        self.slice_name = self.topology_cfg['slice_name']
        self.component_prefix = "my_seam_network_test"
        self.subnet_prefix = self.topology_cfg['network'][0]['subnet'].split('/')[0][:-1]
        self.subnet = self.topology_cfg['network'][0]['subnet']
        
    def select_sites(self):
        return self.topology_cfg['site']
    
    def validate_sites(self):
        return self.site_exists_on_FABRIC(self.topology_cfg['site'])
    
    def validate_image(self):
        return self.image_exists_on_FABRIC(self.topology_cfg['image'])
    
    def add_nodes_and_interfaces(self):
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

    def run_internal_methods(self):
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

    def setup_network(self):
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

    def run_connectivity_test(self):
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