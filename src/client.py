"""
Simple test client for the search server.
"""
import socket
import sys


def main():
    """Main entry point."""
    # Create socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to server
        client.connect(('localhost', 44445))
        
        # Get search string from command line or user input
        if len(sys.argv) > 1:
            search_string = sys.argv[1]
        else:
            search_string = input("Enter string to search: ")
        
        # Send search string
        client.sendall(f"{search_string}\n".encode('utf-8'))
        
        # Receive response
        response = client.recv(1024).decode('utf-8')
        print(f"Server response: {response.strip()}")
        
    except ConnectionRefusedError:
        print("Error: Could not connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    main() 