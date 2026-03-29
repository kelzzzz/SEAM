from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import yaml

with open('{{ cookiecutter.topology_template}}/config/topology.yaml', 'r') as f:
    topology_cfg = yaml.full_load(f)

class SliceManager:
    def __init__(self, topology_cfg):
        self.topology_cfg = topology_cfg
        self.slice = None

    def create_slice(self, fablib_manager):
        #TODO only create if not exists
        slice_name = self.topology_cfg.get('slice_name')
        self.slice = fablib_manager.new_slice(name=slice_name)
        print(f"Created slice: {slice_name}")
        self.add_nodes(fablib_manager)

    def add_nodes(self, fablib_manager):
        for node in self.topology_cfg['nodes']:
            for i in range(node['count']):
                n = self.slice.add_node(name=f"{node['name']}_{i}", site=self.topology_cfg['site'], cores=node['cores'], ram=node['ram'])
                #TODO Move constants
                n_iface = n.add_component(model = "NIC_Basic", name = f"{node['name']}_nic").get_interfaces()[0]

    def deploy(self):
        print("Deploying slice...")
        self.slice.submit()
        print("Slice deployed successfully.")



