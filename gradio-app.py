# Install required apps: pip install -U pyvis gradio networkx
# Run with: gradio gradio-app.py

import os
import pandas as pd
from pyvis.network import Network
import gradio as gr
import networkx as nx

# Set Debug mode
debug = False

# JavaScript function to force Light Mode
js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
}
"""

# Custom CSS
custom_css = """
#dropdown {
    font-size: 11px;
}
#table table {
    font-size: 11px !important;
}
#header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin-bottom: 10px;
}
#logo img {
    height: auto;
    margin: 0;
}
#title {
    color: #333; /* Dark text for contrast */
    margin: 0;
    line-height: 1; /* Vertical alignment */
}
.show-api {
    display: none !important;
}
.built-with {
    display: none !important;
}
"""

# Generate sample data
def generate_sample_data():
    # Generate a random directed graph
    G = nx.gnm_random_graph(50, 100, directed=True)
    
    # Prepare data to store the full chain of connections for each node
    data = []
    for node in G.nodes:
        # Compute the full connection chain starting from the current node
        connection_chain = []
        current_node = node
        while True:
            connection_chain.append(current_node)
            successors = list(G.successors(current_node))
            if not successors:
                break
            current_node = successors[0]  # Follow the first successor
        
        # Format the connection chain as a string
        chain_str = " -> ".join(map(str, connection_chain))
        data.append({"Node": node, "Connections": chain_str})
    
    # Create a DataFrame with the results
    df = pd.DataFrame(data)
    return G, df

# Store the PyVis graph object globally
net = Network(notebook=False, directed=True, height="380px")

# Function to initialize the PyVis graph
def initialize_pyvis_graph(G):
    if debug: print("Initializing PyVis graph...")
    for node in G.nodes:
        net.add_node(node, label=str(node))  # Add all nodes
    for edge in G.edges:
        net.add_edge(edge[0], edge[1])  # Add all edges

# Function to update the highlights in the PyVis graph
def update_pyvis_highlights(selected_node):
    if debug: print(f"Updating highlights for node: {selected_node}")
    # Clear existing highlights
    for node in net.nodes:
        node["color"] = None
        node["size"] = None
    for edge in net.edges:
        edge["color"] = None

    # Highlight the chain if a node is selected
    if selected_node is not None:
        highlight_nodes = set()
        current_node = selected_node
        while True:
            highlight_nodes.add(current_node)
            successors = list(G.successors(current_node))
            if not successors:
                break
            current_node = successors[0]

        # Update node and edge attributes
        for node in net.nodes:
            if node["id"] in highlight_nodes:
                node["color"] = "red"
                node["size"] = 20

        for edge in net.edges:
            if edge["from"] in highlight_nodes:
                edge["color"] = "red"

# Update the update_graph function
def update_graph(selected_node):
    if debug: print(f"Graph update requested for node: {selected_node}")
    if selected_node is None or selected_node == "":
        return create_pyvis_html()

    selected_node = int(selected_node)
    update_pyvis_highlights(selected_node)
    return create_pyvis_html()

# Function to create the graph HTML
def create_pyvis_html():
    if debug: print("Generating PyVis HTML...")
    html = net.generate_html()
    html = html.replace("'", "`")  # Replace single quotes in the HTML
    return f"""<iframe style="width: 100%; height: 400px; border: 0; margin: 0 auto;" name="result" allow="midi; geolocation; microphone; camera; 
    display-capture; encrypted-media;" sandbox="allow-modals allow-forms 
    allow-scripts allow-same-origin allow-popups 
    allow-top-navigation-by-user-activation allow-downloads" allowfullscreen="" 
    allowpaymentrequest="" srcdoc='{html}'></iframe>"""

# Main program
G, data_df = generate_sample_data()
initialize_pyvis_graph(G)

# Set up static paths for serving files
static_dir = os.path.abspath(".")  # Current directory
gr.set_static_paths({"static": static_dir})  # Serve the current directory as "static"

# Create Gradio interface
with gr.Blocks(js=js_func, css=custom_css) as demo:
    # Header with logo and title
    with gr.Row(elem_id="header"):
        with gr.Column(scale=1):  # Logo occupies less space
            logo = gr.Image(
                value="static/gradio_logo.svg", elem_id="logo",
                label=None, show_label=False, container=False, interactive=False,
                show_download_button=False, show_fullscreen_button=False
            )
        with gr.Column(scale=8):  # Title occupies more space
            gr.Markdown("## Interactive Data Table and PyVis Graph", elem_id="title")

    # Dropdown for Node Selection
    node_selector = gr.Dropdown(
        choices=[str(node) for node in data_df["Node"]],
        label="Select Node", value="", show_label=True, container=True, allow_custom_value=True,
        elem_id="dropdown"
    )

    # Data Table (Static View)
    table = gr.Dataframe(data_df, label="Data Table", max_height=200, interactive=False, elem_id="table")

    # Iframe for graph
    graph_output = gr.HTML(label="Graph Visualization")

    # Link dropdown change to the graph update function
    node_selector.change(fn=update_graph, inputs=[node_selector], outputs=[graph_output])

    # Initial graph render
    graph_output.value = create_pyvis_html()
    if debug: print("Initial graph rendered.")

# Launch the interface
demo.launch(share=False, show_api=False)
