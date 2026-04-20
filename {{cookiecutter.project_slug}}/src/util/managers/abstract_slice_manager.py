from abc import abstractmethod
from platform import node

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "{{ cookiecutter.topology_template }}" / "config" / "topology.yaml"
BOOTSTRAP_PATH = BASE_DIR / "{{ cookiecutter.topology_template }}" / "bootstrap" / "bootstrap.sh"


class abstract_slice_manager:

    def __init__(self, fablib_manager):
        with open(CONFIG_PATH, 'r') as f:
            self.topology_cfg = yaml.full_load(f)
        self.fablib = fablib_manager
        self.nodes = []
        self.slice = None
        self.slice_name = self.topology_cfg['slice_name']
        self.set_yaml_variables()
        
        if(not self.validate_sites()):
            raise Exception(f"Invalid site selection. Please select a valid site in the topology.yaml file.")
        
        if(not self.validate_image()):
            raise Exception(f"Invalid image selection. Please select a valid image in the topology.yaml file.")
    
    @abstractmethod
    def validate_sites(self):
        pass
    
    @abstractmethod
    def validate_image(self):
        pass
    
    @abstractmethod
    def set_yaml_variables(self):
        pass

    @abstractmethod
    def add_nodes_and_interfaces(self):
        pass
    
    @abstractmethod
    def run_internal_methods(self):
        pass
    
    @abstractmethod
    def setup_network():
        pass
    
    @abstractmethod
    def run_connectivity_test():
        pass
    
    @abstractmethod
    def select_sites():
        pass
    
    def image_exists_on_FABRIC(self, image):
        try:
            if image in self.fablib.get_image_names():
                return True
        except Exception as e:
            return False
        
    def site_exists_on_FABRIC(self, site):
        try:
            if site in self.fablib.get_site_names():
                return True
        except Exception as e:
            return False
    
    def collect_nodes(self):
        if(not self.slice):
            self.deploy()
        self.nodes = self.slice.get_nodes()
        
    def _ensure_slice_and_nodes(self):
        if not self.slice:
            self.deploy()
        if not self.nodes:
            self.collect_nodes()
    
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
            self.execute_single_node(node, commands, quiet=quiet)
            
    def execute_single_node_on_thread(self,node, commands):
        allcommands = ';'.join(commands)
        node.execute_thread(allcommands, output_file=node.get_name() + '_thread.log')

    def execute_commands_on_threads(self, node, commands):
        if isinstance(node, list):
            for n in node:
                self.execute_single_node_on_thread(n, commands)
        else:
            self.execute_single_node_on_thread(node, commands)
            
    def upload_src_files_to_nodes(self):
        self._ensure_slice_and_nodes()
        print(str(SRC_DIR))
        print(str(BOOTSTRAP_PATH))
        for i, node in enumerate(self.nodes):
            node.upload_directory(local_directory_path=str(SRC_DIR), remote_directory_path=f"/home/{node.get_username()}")
            node.upload_file(local_file_path=str(BOOTSTRAP_PATH), remote_file_path=f"/home/{node.get_username()}/bootstrap.sh")
        print("Files uploaded.")
    
    def download_sink_from_receiver(self, local_path="sink.csv"):
        self._ensure_slice_and_nodes()
        for i, node in enumerate(self.nodes):
            if("receiver" in node.get_name()):
                node.download_file(remote_file_path=f"/home/{node.get_username()}/sink.csv", local_file_path=local_path)
                return
    
    def bootstrap_nodes(self):
        if not self.nodes:
            self.collect_nodes()

        for node in self.nodes:
            self.execute_commands_on_threads(node, [f'chmod +x bootstrap.sh', f'./bootstrap.sh'])
    
    def stop_on_nodes(self):
        for i, node in enumerate(self.nodes):
            self.execute_commands(node, [f'kill -15 -1'], quiet=False)
            
    def deploy(self):
        print("Creating slice...")
        self.select_sites()
        try: 
            self.fablib.get_slice(name=self.slice_name)
            print(f"Slice {self.slice_name} already exists. Using existing slice.")
            self.slice = self.fablib.get_slice(name=self.slice_name)
            self.nodes = self.collect_nodes()
            return
        except Exception as e:
            self.slice = self.fablib.new_slice(name=self.slice_name)
            print(f"Created slice: {self.slice_name}")
            print("Adding nodes and network components...")
            try:
                self.add_nodes_and_interfaces()
            except Exception as e:
                print(f"Error occurred while adding nodes and interfaces: {e}")
                exit(1)
            print("Deploying slice...")
            self.slice.submit()

    def setup_nodes(self):
        print("Waiting for slice to be active...")
        self.slice.wait_ssh()
        print("Uploading source files...")
        self.upload_src_files_to_nodes()
        print("Configuring network...")
        self.setup_network()
        print("Executing workload on nodes...")
        self.bootstrap_nodes()
        
    def run(self):
        print("Running connectivity test...")
        self.run_connectivity_test()
        print("Running experiment...")
        self.run_internal_methods()