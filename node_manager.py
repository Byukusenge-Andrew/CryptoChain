import requests
import time
from urllib.parse import urljoin
import socket
import threading
from datetime import datetime
import json

class NodeManager:
    def __init__(self, base_ports=range(5000, 5010)):
        self.nodes = set()
        self.base_ports = base_ports
        self.health_data = {}
        self.monitoring = False

    def discover_nodes(self):
        """Automatically discover nodes running on local ports"""
        print("Discovering nodes...")
        
        for port in self.base_ports:
            url = f"http://localhost:{port}"
            try:
                response = requests.get(
                    urljoin(url, "chain"),
                    timeout=2
                )
                if response.status_code == 200:
                    self.nodes.add(url)
                    print(f"✅ Discovered node at {url}")
            except requests.exceptions.RequestException:
                pass
        
        return list(self.nodes)

    def connect_nodes(self):
        """Connect all discovered nodes to each other"""
        print("\nConnecting nodes...")
        
        for node in self.nodes:
            try:
                other_nodes = [n for n in self.nodes if n != node]
                response = requests.post(
                    urljoin(node, "nodes/register"),
                    json={"nodes": other_nodes},
                    timeout=5
                )
                
                if response.status_code == 201:
                    print(f"✅ Connected {node} to peer nodes")
                else:
                    print(f"❌ Failed to connect {node}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error connecting {node}: {str(e)}")

    def verify_chain_consistency(self):
        """Verify that all nodes have consistent blockchain data"""
        print("\nVerifying chain consistency...")
        
        chains = {}
        for node in self.nodes:
            try:
                response = requests.get(urljoin(node, "chain"), timeout=5)
                if response.status_code == 200:
                    chains[node] = response.json()
            except requests.exceptions.RequestException:
                print(f"❌ Could not get chain from {node}")
                continue

        # Compare chain lengths and content
        if not chains:
            print("No chains available for verification")
            return

        lengths = {node: data['length'] for node, data in chains.items()}
        max_length = max(lengths.values())
        
        print("\nChain lengths:")
        for node, length in lengths.items():
            status = "✅" if length == max_length else "❌"
            print(f"{status} {node}: {length} blocks")

        # Verify block hashes match across nodes
        reference_chain = next(iter(chains.values()))['chain']
        for node, data in chains.items():
            if node == next(iter(chains.keys())):
                continue
                
            chain = data['chain']
            for i, (ref_block, node_block) in enumerate(zip(reference_chain, chain)):
                if ref_block['previous_hash'] != node_block['previous_hash']:
                    print(f"❌ Hash mismatch at block {i} on {node}")

    def monitor_node_health(self):
        """Monitor node health metrics"""
        self.monitoring = True
        
        def monitor():
            while self.monitoring:
                for node in self.nodes:
                    try:
                        # Get chain info
                        chain_response = requests.get(
                            urljoin(node, "chain"),
                            timeout=2
                        )
                        
                        # Get pending transactions
                        tx_response = requests.get(
                            urljoin(node, "transactions/pending"),
                            timeout=2
                        )
                        
                        self.health_data[node] = {
                            'status': 'online',
                            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'chain_length': chain_response.json()['length'],
                            'pending_tx': len(tx_response.json() if tx_response.status_code == 200 else []),
                            'response_time': chain_response.elapsed.total_seconds()
                        }
                    except requests.exceptions.RequestException:
                        self.health_data[node] = {
                            'status': 'offline',
                            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                
                time.sleep(10)  # Check every 10 seconds

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def synchronize_chains(self):
        """Force chain synchronization across all nodes"""
        print("\nSynchronizing chains...")
        
        for node in self.nodes:
            try:
                response = requests.get(
                    urljoin(node, "nodes/resolve"),
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('message') == 'Our chain was replaced':
                        print(f"✅ {node} synchronized with network")
                    else:
                        print(f"ℹ️ {node} already up to date")
                else:
                    print(f"❌ Failed to synchronize {node}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error synchronizing {node}: {str(e)}")

    def print_health_report(self):
        """Print a health report for all nodes"""
        print("\nNode Health Report")
        print("=" * 50)
        
        for node, health in self.health_data.items():
            print(f"\nNode: {node}")
            print("-" * 30)
            for key, value in health.items():
                print(f"{key}: {value}")

def main():
    manager = NodeManager()
    
    print("Blockchain Node Manager")
    print("======================")
    
    # Discover and connect nodes
    nodes = manager.discover_nodes()
    if not nodes:
        print("No nodes discovered. Please start some nodes first.")
        return
    
    manager.connect_nodes()
    
    # Start health monitoring
    manager.monitor_node_health()
    
    # Main management loop
    while True:
        print("\nNode Management Options:")
        print("1. Verify chain consistency")
        print("2. Synchronize chains")
        print("3. View health report")
        print("4. Discover new nodes")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ")
        
        if choice == '1':
            manager.verify_chain_consistency()
        elif choice == '2':
            manager.synchronize_chains()
        elif choice == '3':
            manager.print_health_report()
        elif choice == '4':
            manager.discover_nodes()
        elif choice == '5':
            manager.monitoring = False
            break
        else:
            print("Invalid choice")
        
        time.sleep(1)

if __name__ == "__main__":
    main() 