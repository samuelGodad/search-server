"""
Client module for the search server.
"""

import socket
import ssl
import json
from typing import Optional, Tuple
from pathlib import Path
# import os
# import argparse

from config import Config


class SearchClient:
    """Client for the search server."""

    def __init__(
        self,
        port: Optional[int] = None,
        config_path: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Initialize search client.

        Args:
            port: Port number to connect to (overrides config)
            config_path: Path to the configuration file
            timeout: Socket timeout in seconds
        """
        self.config = None
        if config_path:
            try:
                self.config = Config(config_path)
            except FileNotFoundError:
                print(f"Config file not found: {config_path}, using defaults")
                self.config = None

        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None

    def setup_ssl(self) -> None:
        """Set up SSL context if enabled."""
        # Always set up SSL context when this method is called
        # The caller is responsible for determining when to call this

        try:
            cert_path = Path("certs")
            if not cert_path.exists():
                raise FileNotFoundError(
                    "SSL certificates not found. Run `./setup_ssl.sh` "
                    "from the project root directory to generate certificates."
                )

            self.ssl_context = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH)

            # Always verify server certificate and provide client certificate
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.check_hostname = True
            self.ssl_context.load_verify_locations(str(cert_path / "ca.crt"))
            self.ssl_context.load_cert_chain(
                str(cert_path / "client.crt"), str(cert_path / "client.key")
            )

            # Set minimum TLS version to 1.2 for better security
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

            print("SSL created successfully with certificate verification")
        except Exception as e:
            print(f"SSL setup error: {str(e)}")
            raise RuntimeError(f"Failed to set up SSL: {str(e)}")

    def connect(self) -> None:
        """Connect to the server."""
        # Determine port to connect to
        port = self.port
        if port is None:
            port = self.config.port if self.config else 44445

        # Try SSL first if certificates are available
        ssl_attempted = False

        # Check if we should try SSL (either from config or if certs exist)
        should_try_ssl = (
            (self.config and self.config.ssl_enabled) or
            Path("certs").exists()
        )

        if should_try_ssl:
            try:
                # Try SSL connection first
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.timeout:
                    self.socket.settimeout(self.timeout)

                print("Setting up SSL...")
                self.setup_ssl()
                print("SSL context created, wrapping socket...")
                self.socket = self.ssl_context.wrap_socket(
                    self.socket, server_hostname="localhost"
                )
                print("Socket wrapped with SSL")

                print(f"Connecting to localhost:{port}...")
                self.socket.connect(("localhost", port))

                # Verify SSL connection
                cert = self.socket.getpeercert()
                if not cert:
                    raise ssl.SSLError(
                        "Server certificate verification failed")
                print("SSL connection established with verified server")
                ssl_attempted = True
                return

            except Exception as e:
                print(f"SSL connection failed: {str(e)}, trying non-SSL...")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                ssl_attempted = True

        # Try non-SSL connection (either as fallback or primary)
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.timeout:
                self.socket.settimeout(self.timeout)

            print(f"Connecting to localhost:{port}...")
            self.socket.connect(("localhost", port))
            print("Connected successfully (non-SSL)")

        except Exception as e:
            import traceback
            print(f"Connection error: {str(e)}")
            print(traceback.format_exc())
            if ssl_attempted:
                raise ConnectionError(
                    f"Both SSL & non-SSL failed. Last error: {str(e)}"
                    )
            else:
                raise ConnectionError(f"Failed to connect to server: {str(e)}")

    def search(
        self,
        query: str,
        algorithm: str = "linear",
        benchmark: bool = False,
        legacy: bool = False,
    ) -> Tuple[bool, float]:
        """
        Search for a string on the server.

        Args:
            query: String to search for
            algorithm: Search algorithm to use
            benchmark: Whether to run in benchmark mode
            legacy: Use legacy protocol (plain text)

        Returns:
            Tuple of (found, execution_time)
        """
        if not self.socket:
            self.connect()

        try:
            # Create request as JSON
            request = {
                "query": query,
                "algorithm": algorithm,
                "benchmark": benchmark
            }
            request_data = json.dumps(request).encode("utf-8") + b"\n"

            # Send request
            self.socket.sendall(request_data)

            # Receive response
            response = b""
            while not response.endswith(b"\n"):
                chunk = self.socket.recv(1024)
                if not chunk:
                    break
                response += chunk

            if not response:
                raise ConnectionError("Connection closed by server")

            response = response.decode("utf-8").rstrip("\r\n")

            # Parse response
            if response == "STRING EXISTS":
                return True, 0.0
            elif response == "STRING NOT FOUND":
                return False, 0.0
            elif response == "RATE LIMIT EXCEEDED":
                raise RuntimeError("RATE LIMIT EXCEEDED")
            elif response == "INVALID REQUEST":
                raise ValueError("INVALID REQUEST")
            elif response.startswith("Error"):
                raise RuntimeError(response)
            else:
                raise RuntimeError(f"Unexpected response: {response}")

        except socket.timeout:
            raise TimeoutError("Connection timed out")
        except ConnectionResetError:
            raise ConnectionError("Connection reset by peer")
        except Exception as e:
            if isinstance(e, (TimeoutError, ConnectionError, ValueError)):
                raise
            raise RuntimeError(f"Search failed: {str(e)}")
        finally:
            self.close()  # Close connection after each request

    def close(self) -> None:
        """Close the connection."""
        if self.socket:
            self.socket.close()
            self.socket = None


def main() -> None:
    """Main entry point."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Search client")
    parser.add_argument("query", help="String to search for")
    parser.add_argument(
        "--algorithm",
        "-a",
        default="linear",
        choices=["linear", "binary", "boyer_moore", "kmp"],
        help="Search algorithm to use",
    )
    parser.add_argument(
        "--port", "-p", type=int, help="Port number to connect to"
    )
    parser.add_argument(
        "--config", "-c", help="Path to configuration file"
    )
    parser.add_argument(
        "--timeout", "-t", type=float, help="Connection timeout in seconds"
    )

    args = parser.parse_args()

    try:
        client = SearchClient(
            port=args.port,
            config_path=args.config,
            timeout=args.timeout,
        )
        found, _ = client.search(args.query, algorithm=args.algorithm)
        if found:
            print("String found!")
        else:
            print("String not found.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
