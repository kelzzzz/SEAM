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

### 3. Move Template Folder

**Important**: After cookiecutter generates the project, you need to manually move the chosen template folder from `templates/{{cookiecutter.topology_template}}/` to the project root. This step will be automated in the future.

For example, if you selected `swr_basic`:
```bash
mv templates/swr_basic/* ./
rmdir templates/swr_basic
```

### 4. Implement Your Logic

Edit the following files in the `src/` directory with your experiment code:

- **`schema.py`**: Define your data schema class with fields for worker results - this is the data structure you expect to be aggregated at your final destination.
- **`sender_emit.py`**: Implement the `get_packet()` method to generate packets for your workers to compute with
- **`worker_consume.py`**: Implement the `compute()` method to process received data - this should output your schema
- **`receiver_recv.py`**: Right now this prints to a CSV based on the schema, but will soon have different options for sinks.

### 5. Deploy and Run

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

## Dependencies

- Python 3.8+
- FABRIC testbed account and project
- Required Python packages: scapy, pandas, pyyaml, pybinn, fabrictestbed-extensions

## Development Status

This is a work-in-progress project. Current issues:
- Template folder must be moved manually after generation
- Limited topology options - L3VPN will be added
- Overall code quality needs improvement
- slice_manager.py needs to be much more generic

Right now, places where code would be abstracted for framework purposes are holding a test 'Monte Carlo' pi approximation. This will be changed in the future (likely moved to an 'examples' area), but is left there for now for demo purposes.

Planned improvements:
- Automated template handling
- More topology templates
- Error handling & logging
- Enhanced monitoring
- Node heartbeats
- Support for additional data sinks
- Auto-initialize Git repositories for projects
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
