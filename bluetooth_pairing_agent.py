import asyncio
import json
import signal
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next.service import ServiceInterface, method


BLUEZ = "org.bluez"
ADAPTER = "/org/bluez/hci0"
AGENT_PATH = "/com/student/pairing_agent"
CAPABILITY = "NoInputNoOutput"
CONFIG_PATH = BASE_DIR / "config.json"


def load_device_name() -> str:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fp:
            config = json.load(fp)
        return config.get("bluetooth", {}).get("name") or config.get("device", {}).get("device_id")
    except Exception:
        return "student-rk3506js-001"


class PairingAgent(ServiceInterface):
    def __init__(self, bus: MessageBus):
        super().__init__("org.bluez.Agent1")
        self.bus = bus

    async def trust_device(self, device_path: str) -> None:
        try:
            introspection = await self.bus.introspect(BLUEZ, device_path)
            obj = self.bus.get_proxy_object(BLUEZ, device_path, introspection)
            props = obj.get_interface("org.freedesktop.DBus.Properties")
            await props.call_set("org.bluez.Device1", "Trusted", Variant("b", True))
            print(f"trusted bluetooth device {device_path}", flush=True)
        except Exception as exc:
            print(f"failed to trust bluetooth device {device_path}: {exc}", flush=True)

    def trust_later(self, device_path: str) -> None:
        asyncio.get_running_loop().create_task(self.trust_device(device_path))

    @method()
    def Release(self) -> None:
        print("bluetooth pairing agent released", flush=True)

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        print(f"bluetooth pairing pincode requested by {device}", flush=True)
        self.trust_later(device)
        return "0000"

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s") -> None:
        print(f"bluetooth pairing pincode for {device}: {pincode}", flush=True)

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        print(f"bluetooth passkey requested by {device}", flush=True)
        self.trust_later(device)
        return 0

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q") -> None:
        print(f"bluetooth display passkey for {device}: {passkey:06d}, entered={entered}", flush=True)

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u") -> None:
        print(f"bluetooth auto-confirm passkey for {device}: {passkey:06d}", flush=True)
        self.trust_later(device)

    @method()
    def RequestAuthorization(self, device: "o") -> None:
        print(f"bluetooth auto-authorize device {device}", flush=True)
        self.trust_later(device)

    @method()
    def AuthorizeService(self, device: "o", uuid: "s") -> None:
        print(f"bluetooth auto-authorize service {uuid} for {device}", flush=True)
        self.trust_later(device)

    @method()
    def Cancel(self) -> None:
        print("bluetooth pairing request canceled", flush=True)


async def set_property(bus: MessageBus, path: str, interface: str, name: str, value: Variant) -> None:
    introspection = await bus.introspect(BLUEZ, path)
    obj = bus.get_proxy_object(BLUEZ, path, introspection)
    props = obj.get_interface("org.freedesktop.DBus.Properties")
    await props.call_set(interface, name, value)


async def configure_adapter(bus: MessageBus) -> None:
    alias = load_device_name()
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "Powered", Variant("b", True))
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "Alias", Variant("s", alias))
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "DiscoverableTimeout", Variant("u", 0))
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "Discoverable", Variant("b", True))
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "PairableTimeout", Variant("u", 0))
    await set_property(bus, ADAPTER, "org.bluez.Adapter1", "Pairable", Variant("b", True))
    print(f"bluetooth adapter ready for pairing as {alias}", flush=True)


async def main() -> int:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    agent = PairingAgent(bus)
    bus.export(AGENT_PATH, agent)

    await configure_adapter(bus)

    introspection = await bus.introspect(BLUEZ, "/org/bluez")
    obj = bus.get_proxy_object(BLUEZ, "/org/bluez", introspection)
    manager = obj.get_interface("org.bluez.AgentManager1")

    try:
        await manager.call_register_agent(AGENT_PATH, CAPABILITY)
    except Exception as exc:
        print(f"register agent warning: {exc}", flush=True)
    await manager.call_request_default_agent(AGENT_PATH)
    print(f"bluetooth pairing agent registered: {CAPABILITY}", flush=True)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
