# {{cookiecutter.project_slug}}

This project was generated with [SEAM](https://github.com/kelzzzz/SEAM), a framework for deploying distributed computing & streaming network topologies on FABRIC.

### 1. Implement Your Logic

Edit the following files in the src/ directory with your experiment code:

- schema.py: Define your data schema class with fields for worker results - this is the data structure you expect to be aggregated at your final destination.
- sender_emit.py: Implement the get_packet() method to generate packets for your workers to compute with
- worker_consume.py: Implement the compute() method to process received data - this should output your schema
- receiver_recv.py: Right now this prints to a CSV based on the schema, but will soon have different options for sinks.

### 2. Deploy and Run

Open deploy.ipynb in Jupyter and run the cells to:

- Install dependencies
- Create and configure your FABRIC slice
- Deploy your code to nodes
- Execute the experiment

Edit this readme with more specific details about your project!