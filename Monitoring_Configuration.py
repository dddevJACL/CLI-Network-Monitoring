import os
import socket
import struct
import zlib
import random
import string
import requests
import ntplib
import dns.resolver
import dns.exception
import threading
import time
import datetime
from socket import gaierror
from time import ctime


class MonitoringConfiguration:
    """A parent class that holds data members and functions relevant to all child monitoring configuration classes"""
    def __init__(self, name, time_in_seconds):
        """Create an instance of MonitoringConfiguration with given parameters"""
        self._name = name
        self._time_interval = time_in_seconds
        self._service = None
        self._function = None
        self._stop_event = threading.Event()
        self._monitor_thread = None

    def __str__(self):
        """Specify how this class should be printed to the CLI"""
        return f"Service: {self._service}\nMonitoring: {self._name} at a time interval of {self._time_interval} seconds."

    def get_time_interval(self):
        """Returns the time interval for this monitoring configuration"""
        return self._time_interval

    def set_time_interval(self, new_time_in_seconds):
        """Sets the _time_interval with the given new_time"""
        self._time_interval = new_time_in_seconds
        return None

    def get_name(self):
        """Returns the name of this monitoring configuration"""
        return self._name

    def get_service(self):
        """Returns the service that is being monitored"""
        return self._service

    def set_function(self, new_func):
        """Set a new function for the Monitoring Configuration"""
        self._function = new_func

    def monitor(self):
        """The Monitor method is the principal method of the MonitoringConfiguration class. It is responsible
        for calling the method that monitors the given service, and prints out a time stamped result. It uses
        threading so that multiple classes can call monitor at the same time."""
        while not self._stop_event.is_set():
            print("")
            function_response = self._function()
            print(f"{self.timestamped_print()}\nService: {self._service}\nMonitoring: {self._name} at a time"
                  f" interval of {self._time_interval} seconds.\n{function_response}")
            print("")
            time.sleep(self._time_interval)
        return None

    def activate(self):
        """When the activate method is called, the _monitor_thread private data member is updated to be a
        thread that uses the monitor method. The monitor thread is then started."""
        self._monitor_thread: threading.Thread = threading.Thread(target=self.monitor)
        self._monitor_thread.start()

    def deactivate(self):
        """The deactivate method sets the stop event, and thus stops the monitor method."""
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join()
        return

    def calculate_icmp_checksum(self, data: bytes) -> int:
        """
        Calculate the checksum for the ICMP packet.
        """

        s: int = 0
        for i in range(0, len(data), 2):

            w: int = (data[i] << 8) + (data[i + 1])
            s += w

        s = (s >> 16) + (s & 0xffff)

        s = ~s & 0xffff

        return s

    def create_icmp_packet(self, icmp_type: int = 8, icmp_code: int = 0, sequence_number: int = 1,
                           data_size: int = 192) -> bytes:
        """
        Creates an ICMP packet with specified parameters.
        """

        thread_id = threading.get_ident()
        process_id = os.getpid()

        icmp_id = zlib.crc32(f"{thread_id}{process_id}".encode()) & 0xffff

        header: bytes = struct.pack('bbHHh', icmp_type, icmp_code, 0, icmp_id, sequence_number)

        random_char: str = random.choice(string.ascii_letters + string.digits)
        data: bytes = (random_char * data_size).encode()

        chksum: int = self.calculate_icmp_checksum(header + data)

        header = struct.pack('bbHHh', icmp_type, icmp_code, socket.htons(chksum), icmp_id, sequence_number)

        return header + data

    def ping(self, host=None, ttl: int = 64, timeout: int = 1, sequence_number: int = 1):
        """
        Send an ICMP Echo Request to a specified host and measure the round-trip time.
        """
        if not host:
            host = self._name

        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:

            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

            sock.settimeout(timeout)

            packet: bytes = self.create_icmp_packet(icmp_type=8, icmp_code=0, sequence_number=sequence_number)

            sock.sendto(packet, (host, 1))

            start: float = time.time()

            try:

                data, addr = sock.recvfrom(1024)

                end: float = time.time()

                total_ping_time = (end - start) * 1000

                if addr[0] == self._name:
                    return f"Successfully pinged {addr[0]}, with a time of {total_ping_time}ms"
                else:
                    return f"Successfully pinged {self._name} at {addr[0]}, with a time of {total_ping_time}ms"
            except socket.timeout:
                return f"Failed to ping {self._name}"

    def timestamped_print(self):
        """
        Custom print function that adds a timestamp to the beginning of the message.
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. These are passed to the built-in print function.
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"[{timestamp}]:"


class MonitorHTTP(MonitoringConfiguration):
    """
    MonitorHTTP is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorHTTP
    has a child class specific method of check_server_http, for monitoring http servers.
    """
    def __init__(self, name, time_in_seconds):
        """
        Initialize an instance of the class with super, set _service and _function private data members to be
        MonitorHTTP class specific
        """
        super().__init__(name, time_in_seconds)
        self._service = "HTTP"
        self._function = self.check_server_http

    def check_server_http(self, url=None):
        """
        Check if an HTTP server is up by making a request to the provided URL.
        """
        if url is None:
            url = self._name
        try:

            response: requests.Response = requests.get(url)

            is_up: bool = response.status_code < 400

            return f"{self._name} is active. Response code: {response.status_code}"

        except requests.RequestException:
            return f"Failed to connect to {self._name}"


class MonitorHTTPS(MonitoringConfiguration):
    """
    MonitorHTTPS is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorHTTPS
    has a child class specific method of check_server_https, for monitoring https servers.
    """
    def __init__(self, name, time_in_seconds):
        """
        Initialize an instance of the class with super, set _service and _function private data members to be
        MonitorHTTPS class specific
        """
        super().__init__(name, time_in_seconds)
        self._service = "HTTPS"
        self._function = self.check_server_https

    def check_server_https(self, url=None, timeout: int = 5):
        """
        Check if an HTTPS server is up by making a request to the provided URL.
        """
        if url is None:
            url = self._name
        try:
            headers: dict = {'User-Agent': 'Mozilla/5.0'}

            response: requests.Response = requests.get(url, headers=headers, timeout=timeout)

            is_up: bool = response.status_code < 400

            return f"{self._name} is active. Server is up. Response code: {response.status_code}"

        except requests.ConnectionError:
            return f"Failed to connect to {self._name}. Connection error"

        except requests.Timeout:
            return f"Failed to connect to {self._name}. Timeout occurred"

        except requests.RequestException as e:
            return f"Failed to connect to {self._name}. Error during request: {e}"


class MonitorICMP(MonitoringConfiguration):
    """
    MonitorICMP is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorICMP
    only sets a unique service type, but otherwise uses only parent methods.
    """
    def __init__(self, name, time_in_seconds):
        """
        Initialize an instance of the class with super, set _service and _function private data members to be
        MonitorICMP class specific. In this case, _function is set to be the ping method of the parent class.
        """
        super().__init__(name, time_in_seconds)
        self._service = "ICMP"
        self._function = super().ping


class MonitorDNS(MonitoringConfiguration):
    """
    MonitorDNS is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorDNS
    has a child class specific method of check_dns_server_status, for monitoring DNS servers.
    """
    def __init__(self, name, time_in_seconds, query, record_type):
        """
        Initialize an instance of the class with super, set _service, _query, _record_type, and _function
        private data members to be MonitorDNS class specific
        """
        super().__init__(name, time_in_seconds)
        self._service = "DNS"
        self._query = query
        self._record_type = record_type
        self._function = self.check_dns_server_status

    def check_dns_server_status(self, server=None, query=None, record_type=None):
        """
        Check if a DNS server is up and return the DNS query results for a specified domain and record type.

        """
        if server is None:
            server = self._name
        if query is None:
            query = self._query
        if record_type is None:
            record_type = self._record_type
        try:

            resolver = dns.resolver.Resolver()
            resolver.nameservers = [socket.gethostbyname(server)]

            query_results = resolver.resolve(query, record_type)
            results = [str(rdata) for rdata in query_results]
            result_str = ' '.join(results)
            return f"Server at server: {server}\nquery: {query} is up.\n" \
                   f"Query results of record type {record_type} returned {result_str}"

        except (dns.exception.Timeout, dns.resolver.NoNameservers, dns.resolver.NoAnswer, socket.gaierror) as e:
            return f"DNS server status check to server: {server}\nquery: {query}\nrecord_type: {record_type}\n" \
                   f"FAILED!\n{str(e)}"

    def get_query(self):
        """Returns query being monitored"""
        return self._query

    def get_record_type(self):
        """Returns DNS record type"""
        return self._record_type


class MonitorNTP(MonitoringConfiguration):
    """
    MonitorNTP is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorNTP
    has a child class specific method of check_ntp_server, for monitoring ntp servers.
    """
    def __init__(self, name, time_in_seconds):
        """
        Initialize an instance of the class with super, set _service and _function private data members to be
        MonitorNTP class specific
        """
        super().__init__(name, time_in_seconds)
        self._service = "NTP"
        self._function = self.check_ntp_server

    def check_ntp_server(self, server=None):
        """
        Checks if an NTP server is up and returns its status and time.

        """
        if server is None:
            server = self._name
        client = ntplib.NTPClient()

        try:
            response = client.request(server, version=3)

            return f"Server at {server} is up. Response time: {ctime(response.tx_time)}"
        except (ntplib.NTPException, gaierror):
            return f"Couldn't reach server at {server}"


class MonitorTCP(MonitoringConfiguration):
    """
    MonitorTCP is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorTCP
    has a child class specific method of check_tcp_port, for monitoring TCP servers. It also has class specific
    set and get methods
    """
    def __init__(self, name, time_in_seconds, port):
        """
        Initialize an instance of the class with super, set _service, _port, and _function
        private data members to be MonitorTCP class specific. Initialize _message to be None, this private
        data member will be used if testing echo server.
        """
        super().__init__(name, time_in_seconds)
        self._service = "TCP"
        self._port = port
        self._function = self.check_tcp_port
        self._message = None

    def get_port(self):
        """Returns the port number"""
        return self._port

    def get_message(self):
        """Return the echo message for use by TCP client and server (same message sent back and forth)"""
        return self._message

    def set_message(self, new_message):
        """Set an echo message for use by TCP client and server (same message sent back and forth)"""
        self._message = new_message
        return None

    def check_tcp_port(self, ip_address=None, port=None) -> (bool, str):
        """
        This function attempts to establish a TCP connection to the specified port on the given IP address.
        """
        if ip_address is None:
            ip_address = self._name
        if port is None:
            port = self._port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)

                s.connect((ip_address, port))
                return f"Port {port} on {ip_address} is open."

        except socket.timeout:
            return f"Port {port} on {ip_address} timed out."

        except socket.error:
            return f"Port {port} on {ip_address} is closed or not reachable."

        except Exception as e:
            return f"Failed to check port {port} on {ip_address} due to an error: {e}"

    def switch_to_client(self):
        """Changes the classes default function to tcp_client"""
        self._function = self.tcp_client
        return None

    def tcp_client(self):
        """Basic TCP client method for testing an echo server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = self._name
        server_port = self._port
        response = None
        try:
            sock.connect((server_address, server_port))

            message = self._message
            print(f"TCP Client: Sending: {message}")
            sock.sendall(message.encode())

            response = sock.recv(1024)
            print(f"TCP Client: Received: {response.decode()}")

        finally:
            sock.close()
            return f"TCP client sent {self._message} to {server_address} at port {server_port}, and received " \
                   f"the following response: {response}"


class MonitorUDP(MonitoringConfiguration):
    """
    MonitorUDP is a child class of MonitoringConfiguration, and as such inherits its methods. MonitorUDP
    has a child class specific method of check_udp_port, for monitoring UDP servers. It also has class specific
    set and get methods
    """
    def __init__(self, name, time_in_seconds, port):
        """
        Initialize an instance of the class with super, set _service, _port, and _function
        private data members to be MonitorUDP class specific. Initialize _message to be None.
        """
        super().__init__(name, time_in_seconds)
        self._service = "UDP"
        self._port = port
        self._function = self.check_udp_port
        self._message = None

    def get_port(self):
        """Returns the port number"""
        return self._port

    def get_message(self):
        """Return the echo message for use by UDP client and server (same message sent back and forth)"""
        return self._message

    def set_message(self, new_message):
        """Set an echo message for use by UDP client and server (same message sent back and forth)"""
        self._message = new_message
        return None

    def switch_to_client(self):
        """Changes the classes default function to udp_client"""
        self._function = self.udp_client
        return None

    def check_udp_port(self, ip_address=None, port=None, timeout: int = 3) -> (bool, str):
        """
        This function attempts to send a UDP packet to the specified port on the given IP address.
        """
        if ip_address is None:
            ip_address = self._name
        if port is None:
            port = self._port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(timeout)

                s.sendto(b'', (ip_address, port))

                try:

                    s.recvfrom(1024)

                    return f"Port {port} on {ip_address} is closed."

                except socket.timeout:

                    return f"Port {port} on {ip_address} is open or no response received."
        except Exception as e:

            return f"Failed to check UDP port {port} on {ip_address} due to an error: {e}"

    def udp_client(self):
        """Basic UDP client method for testing local server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = self._name
        server_port = self._port
        response = None

        try:
            sock.connect((server_address, server_port))

            message = self._message
            print(f"UDP client:\nSending: {message}")
            sock.sendto(message.encode(), (server_address, server_port))

            response, server = sock.recvfrom(1024)
            print(f"UDP Client: Received: {response.decode()} from {server}")

        finally:
            sock.close()
            return f"UDP client sent {self._message} to {server_address} at port {server_port}, and received " \
                   f"the following response: {response}"


class Server:
    """
    The Server class is a parent class to TCP and UDP servers, and holds all mutually necessary data members and methods
    """
    def __init__(self, name, port):
        """Initialize and instance of the Server class with the given name and port"""
        self._name = name
        self._server = "127.0.0.1"
        self._port = port
        self._service = None
        self._function = None
        self._stop_event = threading.Event()
        self._run_thread = None
        self._timeout = 10

    def activate(self):
        """
        When the activate method is called, the _run_thread private data member is updated to be a
        thread that uses the run method of the child class. The run thread is then started.
        """
        self._run_thread: threading.Thread = threading.Thread(target=self._function)
        self._run_thread.start()

    def deactivate(self):
        """The deactivate method sets the stop event, and thus stops the run method of the child class"""
        if self._run_thread is not None:
            self._stop_event.set()
            self._run_thread.join()
        return

    def get_name(self):
        """Returns the custom name of the server"""
        return self._name

    def get_port(self):
        """Returns the port of the server"""
        return self._port

    def get_service(self):
        """Returns the service of server"""
        return self._service


class TCPServer(Server):
    """
    TCPServer is a child class of Server, and as such inherits its methods. TCPServer
    has a child class specific method of run_tcp_server, for running TCP servers. It also has class specific
    _service and _function data members.
    """
    def __init__(self, name, port):
        """
        Initialize and instance of the TCPServer class with the given name and port. Set _service to be 'TCP Server'
        and _function to be run_tcp_server
        """
        super().__init__(name, port)
        self._service = "TCP Server"
        self._function = self.run_tcp_server

    def run_tcp_server(self):
        """
        The method run_tcp_server is the principal method of the TCPServer class. It creates a new TCP server
        at local host with the user inputted port number. It then uses threading to remain active and accept
        incoming messages, and echoes back the same message as a response. The method sets a timeout for the socket
        to enable the server to shut down when asked to.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.settimeout(self._timeout)
        server_address = self._server
        server_port = self._port
        server_sock.bind((server_address, server_port))

        server_sock.listen(5)

        print(f"TCP server {self._name}: Listening for incoming connections!")

        try:
            while not self._stop_event.is_set():

                try:
                    client_sock, client_address = server_sock.accept()
                    print(f"TCP server {self._name}: Connection from {client_address}")
                    message = client_sock.recv(1024)
                    print(f"TCP server {self._name}: Received message {message.decode()}")

                    response = message.decode()
                    client_sock.sendall(response.encode())

                except socket.timeout:
                    if self._stop_event.is_set():
                        if client_sock:
                            client_sock.close()
                            print(f"TCP server {self._name}: Connection with {client_address} closed")
                        break
                    pass

                finally:
                    client_sock.close()
                    print(f"TCP server {self._name}: Connection with {client_address} closed")

        except KeyboardInterrupt:
            print(f"TCP server {self._name}: Server is shutting down")

        finally:
            print(f"TCP server {self._name}: Server is shutting down")
            server_sock.close()
            print(f"TCP server {self._name}: Server socket closed")


class UDPServer(Server):
    """
    UDPServer is a child class of Server, and as such inherits its methods. UDPServer
    has a child class specific method of run_udp_server, for running UDP servers. It also has class specific
    _service and _function data members.
    """
    def __init__(self, name, port):
        """
        Initialize and instance of the UDPServer class with the given name and port. Set _service to be 'UDP Server'
        and _function to be run_udp_server
        """
        super().__init__(name, port)
        self._service = "TCP Server"
        self._function = self.run_udp_server

    def run_udp_server(self):
        """
        The method run_udp_server is the principal method of the UDPServer class. It creates a new UDP server
        at local host with the user inputted port number. It then uses threading to remain active and accept
        incoming messages. The method sets a timeout for the socket
        to enable the server to shut down when asked to.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_sock.settimeout(self._timeout)
        server_address = self._server
        server_port = self._port
        server_sock.bind((server_address, server_port))

        print("UDP Server is ready to receive messages...")

        try:
            while not self._stop_event.is_set():

                try:
                    message, client_address = server_sock.recvfrom(1024)
                    print(f"Received message: {message.decode()} from {client_address}")
                    response = "Message received"
                    server_sock.sendto(response.encode(), client_address)
                except socket.timeout:
                    if self._stop_event.is_set():
                        break
                    pass

        except KeyboardInterrupt:
            print("Server is shutting down")

        finally:
            server_sock.close()
            print("Server socket closed")




















