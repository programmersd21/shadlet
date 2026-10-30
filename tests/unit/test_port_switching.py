import socket

from shadlet.web.server import find_available_port


def test_find_available_port_free():
    """Verify that a free port is returned as-is."""
    # Find a port that is free
    port = find_available_port("127.0.0.1", 9100)
    assert 9100 <= port < 9200


def test_find_available_port_auto_switch():
    """Verify that if the requested port is bound, the smart resolver automatically finds the next free port."""
    # Bind a temporary socket to port 9250
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupied.bind(("127.0.0.1", 9250))
        occupied.listen(1)

        # Asking for 9250 should automatically switch to a subsequent available port (e.g. 9251)
        next_port = find_available_port("127.0.0.1", start_port=9250)
        assert next_port > 9250
        assert next_port < 9350
