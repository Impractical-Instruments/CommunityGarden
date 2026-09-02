"""Tests for LocationSender — Garden State out to the ESP32-S3 controllers (ADR-0020). No hardware."""
import pytest

from coordinator import _load_locations
from displays import GardenState, ShowMode
from location_sender import LocationSender, LocationTarget


class _FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class _FakeClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sent: list[tuple[str, object]] = []
        self.fail = False

    def send_message(self, address, value):
        if self.fail:
            raise OSError("network unreachable")
        self.sent.append((address, value))


def _sender(targets=None, heartbeat_interval_s=5.0, change_epsilon=0.01):
    clients: list[_FakeClient] = []
    clock = _FakeClock()

    def factory(ip, port):
        client = _FakeClient(ip, port)
        clients.append(client)
        return client

    sender = LocationSender(
        targets if targets is not None else [LocationTarget("jess", "192.168.1.62", 9000)],
        heartbeat_interval_s=heartbeat_interval_s,
        change_epsilon=change_epsilon,
        clock=clock,
        client_factory=factory,
    )
    sender.connect()
    return sender, clients, clock


def _addresses(client: _FakeClient) -> list[str]:
    return [address for address, _ in client.sent]


def test_first_send_puts_every_field_on_the_wire():
    sender, clients, _ = _sender()
    sender.send(GardenState())

    assert set(_addresses(clients[0])) == {
        "/flowerbeds/activity",
        "/captcha/intensity",
        "/pipes/activity",
        "/treehouse/brightness",
        "/treehouse/mode",
    }


def test_unchanged_values_are_not_resent_before_the_heartbeat():
    sender, clients, clock = _sender(heartbeat_interval_s=5.0)
    sender.send(GardenState())
    clients[0].sent.clear()

    clock.advance(1.0)
    assert sender.send(GardenState()) == 0
    assert clients[0].sent == []


def test_heartbeat_repeats_values_that_have_not_moved():
    sender, clients, clock = _sender(heartbeat_interval_s=5.0)
    sender.send(GardenState())
    clients[0].sent.clear()

    clock.advance(5.0)
    sender.send(GardenState())
    assert "/flowerbeds/activity" in _addresses(clients[0])
    assert "/treehouse/mode" in _addresses(clients[0])


def test_change_beyond_epsilon_is_sent_immediately():
    sender, clients, clock = _sender(change_epsilon=0.01)
    sender.send(GardenState(flowerbeds_activity=0.5))
    clients[0].sent.clear()

    clock.advance(0.1)
    sender.send(GardenState(flowerbeds_activity=0.505))  # inside epsilon
    assert "/flowerbeds/activity" not in _addresses(clients[0])

    sender.send(GardenState(flowerbeds_activity=0.6))
    assert ("/flowerbeds/activity", pytest.approx(0.6)) in clients[0].sent


def test_mode_change_is_sent_as_a_string():
    sender, clients, clock = _sender()
    sender.send(GardenState())
    clients[0].sent.clear()

    clock.advance(0.1)
    sender.send(GardenState(show_mode=ShowMode.DIM))
    assert ("/treehouse/mode", "dim") in clients[0].sent


# A Blow-Up is a one-shot event; rate limiting it would mean dropping it.
def test_blowup_is_never_rate_limited():
    sender, clients, clock = _sender()
    sender.send(GardenState())
    clients[0].sent.clear()

    clock.advance(0.01)
    sender.send(GardenState(captcha_blowup=True))
    assert ("/captcha/blowup", []) in clients[0].sent

    clients[0].sent.clear()
    sender.send(GardenState(captcha_blowup=False))
    assert "/captcha/blowup" not in _addresses(clients[0])


def test_every_target_gets_every_message():
    targets = [
        LocationTarget("swannatopia", "192.168.1.60", 9000),
        LocationTarget("julia", "192.168.1.61", 9000),
    ]
    sender, clients, _ = _sender(targets)
    sent = sender.send(GardenState())

    assert len(clients) == 2
    assert sent == 10  # five addresses × two controllers
    assert _addresses(clients[0]) == _addresses(clients[1])


# One controller unplugged must not take the other three down with it.
def test_a_failing_controller_does_not_stop_the_others():
    targets = [
        LocationTarget("swannatopia", "192.168.1.60", 9000),
        LocationTarget("julia", "192.168.1.61", 9000),
    ]
    sender, clients, _ = _sender(targets)
    clients[0].fail = True

    assert sender.send(GardenState()) == 5
    assert len(_addresses(clients[1])) == 5


def test_send_without_controllers_is_a_no_op():
    sender = LocationSender([])
    assert sender.send(GardenState()) == 0


def test_brightness_carries_the_folded_master_level():
    sender, clients, _ = _sender()
    sender.send(GardenState(show_mode=ShowMode.DIM, brightness=0.25))
    assert ("/treehouse/brightness", pytest.approx(0.25)) in clients[0].sent


# --- config resolution -----------------------------------------------------

_NETWORK = {
    "heartbeat_interval_s": 5,
    "change_epsilon": 0.02,
    "firmware": {
        "treehouse_jess": {"ip": "192.168.1.62", "mac": None, "osc_port": 9000},
        "treehouse_branch": {"ip": None, "mac": None, "osc_port": None},
    },
}


def test_controllers_resolve_against_network_json():
    config = _load_locations({"controllers": ["treehouse_jess"], "send_hz": 15}, _NETWORK)

    assert config.targets == [LocationTarget("treehouse_jess", "192.168.1.62", 9000)]
    assert config.send_hz == 15
    assert config.heartbeat_interval_s == 5.0
    assert config.change_epsilon == 0.02


def test_controller_without_an_address_is_skipped_not_fatal():
    config = _load_locations(
        {"controllers": ["treehouse_jess", "treehouse_branch", "treehouse_nowhere"]}, _NETWORK
    )
    assert [t.name for t in config.targets] == ["treehouse_jess"]
