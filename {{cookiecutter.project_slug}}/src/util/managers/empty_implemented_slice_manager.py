from .abstract_slice_manager import AbstractSliceManager

#This class provides an empty implementation of the AbstractSliceManager.
#It can be used as a template for creating new slice managers.

#When you implement a slice manager, make sure its class name is exactly the same as its template name

class empty_slice_manager(AbstractSliceManager):
    def set_yaml_variables(self):
        pass
        
    def select_sites(self):
        return self.topology_cfg['site']
    
    def validate_sites(self):
        return self.site_exists_on_FABRIC(self.topology_cfg['site'])
    
    def validate_image(self):
        return self.image_exists_on_FABRIC(self.topology_cfg['image'])
    
    def add_nodes_and_interfaces(self):
        pass

    def run_internal_methods(self):
        pass

    def setup_network(self):
        pass
    
    def run_connectivity_test(self):
        pass