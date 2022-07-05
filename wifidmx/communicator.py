import socket
import socketserver
import threading

beat_ip = "192.168.0.255"
beat_port = 1103
_beat_detected = False


class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    allow_reuse_address = True
    def handle(self):
        data = self.request[0].strip()
        print("{} wrote:".format(self.client_address[0]))
        print(data)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    allow_reuse_address = True


class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    allow_reuse_address = True

    def handle(self):
        global _beat_detected
        data = self.request[0].strip()
        socket = self.request[1]
        _beat_detected = True


class reuseServer(socketserver.UDPServer):
    allow_reuse_address = True


def beat_detected():
    global _beat_detected
    result = False
    if _beat_detected:
        result = True
        _beat_detected = False
    return result


def spawn_udp_server():
    server = ThreadedUDPServer(('', 1103), MyUDPHandler)
    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    return server
