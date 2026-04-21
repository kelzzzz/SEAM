# SEAM (Simple Encoded Aggregation Middleware) for FABRIC

**Work in Progress** - This project is under development and literally everything is probably going to change.

SEAM is a framework for deploying and running distributed computing experiments on the FABRIC testbed. It simplifies the process of setting up network topologies, deploying user defined code, and aggregating distributed computation results for experiments via streaming. SEAM was developed for the Spring 2026 CS 451 Parallel and Distributed Computing class @ IIT.

## Quick Start

### 1. Clone the Template

Use cookiecutter to generate your project:

```bash
pip install cookiecutter
cookiecutter https://github.com/kelzzzz/SEAM.git
```

### 2. Configure Your Experiment

Fill out the cookiecutter prompts:
- **project_name**: A descriptive name for your experiment
- **fabric_site**: FABRIC site code (e.g., EDUKY, DALL)
- **project_id**: Your FABRIC project ID
- **topology_template**: Choose from available templates (swr_basic, L3VPN)
- **jupyter_kernel_name**: Python kernel for notebooks (usually python3)

### 3. Implement Your Logic

Edit the following files in the `src/` directory with your experiment code:

- **`schema.py`**: Define your data schema class with fields for worker results - this is the data structure you expect to be aggregated at your final destination.
- **`sender_emit.py`**: Implement the `get_packet()` method to generate packets for your workers to compute with
- **`worker_consume.py`**: Implement the `compute()` method to process received data - this should output your schema
- **`receiver_recv.py`**: Right now this prints to a CSV based on the schema, but will soon have different options for sinks.

### 4. Deploy and Run

Open `deploy.ipynb` in Jupyter and run the cells to:
- Install dependencies
- Create and configure your FABRIC slice
- Deploy your code to nodes
- Execute the experiment

## Templates

Available topology templates:

- **`swr_basic`**: Simple sender-worker-receiver topology with 1 sender, 3 workers, 1 receiver
- **`E2SAR_L3VPN`**: E2SAR topology with L3VPN networking (WIP)

Each template includes pre-defined:
- `config/topology.yaml`: Node specifications, network config, site settings
- `bootstrap/bootstrap.sh`: Node initialization script installing dependencies

## Adding new topology templates

SEAM is designed to allow for creation of new templates that make FABRIC topology configurations reusable. Below are the steps to implementing a custom template:

### 1. Fork this repo

Add your new template on a forked version of this repository.

### 2. Create a template folder

In the `{{cookiecutter.project_slug}}` directory, you will need to add a folder for your template. Choose a folder name that is clear but short. You can copy any other template for the basic file structure, which is as follows:
```
templates/
├─ my_new_template/
|  ├─ bootstrap/
|  |    ├─ bootstrap.sh
│  ├─ config/
│  |    ├─ topology.yaml
```

Define a bootstrap file, which should deploy all the dependencies necessary for an experiment using this template. This could be firewalls, pip, common libraries, etc.

Then, define the topology.yaml. The most basic structure to reference is the `swr_basic` topology file, but implementations of the `abstract_slice_manager` can accomodate as many fields as needed in the YAML, so feel free to add what is necessary to get your template running. The only field that is absolutely necessary to have at the top is `slice_name`.

### 3. Implement the abstract_slice_manager.py

Create a class that extends `abstract_slice_manager.py`. Give it a prefix that is the exact same as your template folder name; in this example, that would be `my_new_template_slice_manager.py`. Place this file in `src/util/managers/`.

Your implementation must override all abstract methods from `abstract_slice_manager`. Here's a breakdown of key methods to implement:

- **`set_yaml_variables()`**: Parse and store variables specific to your template from `self.topology_cfg`. For example, node roles, network settings, or any custom fields you added to `topology.yaml`. This is called during initialization.

- **`validate_sites()`**: Check if sites in your topology exist on FABRIC. Ususually you can use the `self.site_exists_on_FABRIC(site)` helper. Return `True` if valid, `False` otherwise. However, this method exists in case your topology can only choose from a specified subset of sites. The abstract manager will raise an exception if this fails.

- **`validate_image()`**: Verify that any images specified in `node_roles` or globally are available on FABRIC. Use `self.image_exists_on_FABRIC(image)` helper as above, but this method provides flexibility in-case only a limited subset of images should be used. Return `True` if valid.

- **`validate_components()`**: Ensure NIC models and service types in `network` configs are supported. Use `self.component_exists_on_FABRIC(component)` or query FABRIC directly. Return `True` if valid.

- **`select_sites()`**: Implement site selection logic based on your topology needs. This could use a subset of sites, fall back to random selection, use the site given in the cookiecutter config, or apply custom filters (e.g., based on available resources).

- **`add_nodes_and_interfaces()`**: Create nodes and networks using FABRIC APIs. This is the most open method; use fablib to add nodes and interfaces to the class' `self.slice`.

- **`setup_network()`**: Configure IP addresses, routes, firewalls, and any network tuning (e.g., MTU, buffers)

- **`run_connectivity_test()`**: Perform tests to verify network connectivity (e.g., ping between nodes). Log results and handle failures gracefully.

- **`run_internal_methods()`**: Execute your experiment logic, such as running user code on nodes, collecting results, or triggering data flows.

**Important Notes**:
- The abstract manager's `__init__` calls validations immediately after `set_yaml_variables()`. If any validation fails, an exception is raised with a clear message.
- Use the provided helper methods (e.g., `execute_commands`, `upload_src_files_to_nodes`) for common operations.
- For error handling, catch FABRIC API exceptions in `deploy()` and log informative messages.
- Test your implementation by generating a project with your template and running `deploy.ipynb`.
- The post-generation hook (`hooks/post_gen_project.py`) will automatically keep only your manager file and `abstract_slice_manager.py`, removing others.

Example skeleton for your class:

```python
from src.util.managers.abstract_slice_manager import abstract_slice_manager

class my_new_template_slice_manager(abstract_slice_manager):
    def set_yaml_variables(self):
        # Parse custom YAML fields
        self.my_custom_var = self.topology_cfg.get('my_custom_field', 'default')
        self.site_whitelist = ["DALL", "EDUKY"]
    
    def validate_sites(self):
        # Check sites
        return all(self.site_exists_on_FABRIC(site) for site in self.site_whitelist)
    
    def validate_image(self):
        # Check images
        return self.image_exists_on_FABRIC(self.topology_cfg['image'])
    
    def validate_components(self):
        # Check NICs, etc.
        return True  # Implement as needed
    
    def select_sites(self):
        # Site selection logic
        pass
    
    def add_nodes_and_interfaces(self):
        # Add nodes and networks
        pass
    
    def run_internal_methods(self):
        # Experiment logic
        pass
    
    def setup_network(self):
        # Network setup
        pass
    
    def run_connectivity_test(self):
        # Connectivity tests
        pass
```


### 4. Add the option to the cookiecutter.json

Under the `topology_template` option in the `cookiecutter.json`, add the name of your template. Ensure it matches both the directory name and the slice_manager name.

Test your template in JupyterHub and see if your deployment works! If so, you're done.

### 5. Make a PR to submit your template

If you've added a SEAM template and would like to share it in the master repository, feel free to create a PR from your forked version.

## Dependencies

- Python 3.8+
- FABRIC testbed account and project
- Required Python packages: scapy, pandas, pyyaml, pybinn, fabrictestbed-extensions

## Development Status

This is a work-in-progress project. Current issues:

- ~~Template folder must be moved manually after generation~~
- Limited topology options - L3VPN will be added
- Overall code quality needs improvement
- ~~slice_manager.py needs to be much more generic~~

Right now, places where code would be abstracted for framework purposes are holding a test 'Monte Carlo' pi approximation. This will be changed in the future (likely moved to an 'examples' area), but is left there for now for demo purposes.

Planned improvements:
- ~~Automated template handling~~
- More topology templates
- Error handling & logging
- Enhanced monitoring
- Node heartbeats
- Support for additional data sinks
- ~~Auto-initialize Git repositories for projects~~
- Support for running C source code/better optimiziations (without Python overhead)

## AI Usage & Transparency Notice

SEAM leveraged the free version of Copilot for the following:
- Proofreading of this README.md
- Inferred auto-completion of function call signatures while typing in VS Code
- Performing web searches on specific errors
- Bulk renaming of variables
- Code clean-up suggestions that I selectively applied myself

## License

SEAM is licensed under the MIT license.