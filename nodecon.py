import requests
import time
from urllib.parse import urljoin

def connect_nodes(nodes):
    """Connect multiple blockchain nodes together"""
    print("Starting node connection process...")
    
    successful_connections = []
    failed_connections = []
    
    for node in nodes:
        try:
            # Register other nodes with this node
            other_nodes = [n for n in nodes if n != node]
            payload = {"nodes": other_nodes}
            
            print(f"\nRegistering nodes with {node}:")
            print(f"Payload: {payload}")
            
            response = requests.post(
                urljoin(node, "nodes/register"),
                json=payload,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Successfully registered nodes with {node}")
                print(f"Response: {response.json()}")
                successful_connections.append(node)
            else:
                print(f"❌ Failed to register nodes with {node}")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                failed_connections.append((node, response.text))
                
        except Exception as e:
            print(f"❌ Error connecting to {node}: {str(e)}")
            failed_connections.append((node, str(e)))
    
    print("\nConnection Summary:")
    print(f"Successful connections: {len(successful_connections)}")
    print(f"Failed connections: {len(failed_connections)}")
    
    if failed_connections:
        print("\nFailed Connections Details:")
        for node, error in failed_connections:
            print(f"Node: {node}")
            print(f"Error: {error}\n")

def verify_connections(nodes):
    """Verify that nodes are connected by checking their registered nodes"""
    print("\nVerifying node connections...")
    
    for node in nodes:
        try:
            # Get the chain from each node
            response = requests.get(
                urljoin(node, "chain"),
                timeout=5
            )
            
            if response.status_code == 200:
                chain_data = response.json()
                print(f"\n✅ Node {node} is active")
                print(f"Chain length: {chain_data.get('length', 0)}")
            else:
                print(f"❌ Node {node} returned status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not verify {node}: {str(e)}")

def main():
    # Define the nodes we want to connect
    nodes = [
        "http://localhost:5002",  # First node
        "http://localhost:5003",  # Second node
        "http://localhost:5000"   # Third node
    ]
    
    print("Blockchain Node Connection Utility")
    print("=================================")
    print(f"Connecting {len(nodes)} nodes:")
    for node in nodes:
        print(f"  - {node}")
    print()
    
    # Try to connect the nodes
    connect_nodes(nodes)
    
    # Verify the connections
    verify_connections(nodes)
    
    print("\nNode connection process completed.")

if __name__ == "__main__":
    main()