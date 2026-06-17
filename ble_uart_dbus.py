import asyncio
import signal
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType, PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property, method

from bluetooth_protocol import (
    NUS_RX_UUID,
    NUS_SERVICE_UUID,
    NUS_TX_UUID,
    append_ble_rx,
    append_ble_task,
    hex_bytes,
    json_line,
    parse_incoming_bytes,
)


BLUEZ = "org.bluez"
ADAPTER = "/org/bluez/hci0"
APP_PATH = "/com/student/bleuart"
SERVICE_PATH = APP_PATH + "/service0"
RX_PATH = SERVICE_PATH + "/rx"
TX_PATH = SERVICE_PATH + "/tx"
ADV_PATH = APP_PATH + "/advertisement0"

DEVICE_NAME = "student-rk3506js-001"


class ObjectManager(ServiceInterface):
    def __init__(self, objects):
        super().__init__("org.freedesktop.DBus.ObjectManager")
        self.objects = objects

    @method()
    def GetManagedObjects(self) -> "a{oa{sa{sv}}}":
        return {path: obj.get_managed_properties() for path, obj in self.objects.items()}


class GattService(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.GattService1")

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return NUS_SERVICE_UUID

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def Characteristics(self) -> "ao":
        return [RX_PATH, TX_PATH]

    def get_managed_properties(self):
        return {
            self.name: {
                "UUID": Variant("s", self.UUID),
                "Primary": Variant("b", self.Primary),
                "Characteristics": Variant("ao", self.Characteristics),
            }
        }


class GattCharacteristic(ServiceInterface):
    def __init__(self, uuid: str, path: str, flags: list[str], on_write=None):
        super().__init__("org.bluez.GattCharacteristic1")
        self.uuid = uuid
        self.path = path
        self.flags = flags
        self.on_write = on_write
        self.value = bytearray()
        self.notifying = False

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":
        return SERVICE_PATH

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return self.flags

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":
        return bytes(self.value)

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":
        return self.notifying

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":
        return bytes(self.value)

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}") -> None:
        self.value = bytearray(value)
        text = bytes(value).decode("utf-8", errors="replace").strip()
        print(f"BLE RX: {hex_bytes(bytes(value))} {text!r}", flush=True)
        if self.on_write:
            self.on_write(bytes(value))

    @method()
    def StartNotify(self) -> None:
        if not self.notifying:
            self.notifying = True
            self.emit_properties_changed({"Notifying": self.notifying})
        print("BLE TX notify started", flush=True)

    @method()
    def StopNotify(self) -> None:
        if self.notifying:
            self.notifying = False
            self.emit_properties_changed({"Notifying": self.notifying})
        print("BLE TX notify stopped", flush=True)

    def notify(self, data: bytes) -> None:
        self.value = bytearray(data)
        sent = self.notifying
        if sent:
            self.emit_properties_changed({"Value": bytes(self.value)})
        tag = "sent" if sent else "skipped, no subscriber"
        print(f"BLE TX ({tag}): {hex_bytes(data)} {data.decode('utf-8', errors='replace')!r}", flush=True)

    def get_managed_properties(self):
        return {
            self.name: {
                "UUID": Variant("s", self.UUID),
                "Service": Variant("o", self.Service),
                "Flags": Variant("as", self.Flags),
                "Value": Variant("ay", bytes(self.value)),
                "Notifying": Variant("b", self.Notifying),
            }
        }


class Advertisement(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.LEAdvertisement1")

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":
        return "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":
        return [NUS_SERVICE_UUID]

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> "s":
        return DEVICE_NAME

    @dbus_property(access=PropertyAccess.READ)
    def Discoverable(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def Includes(self) -> "as":
        return []

    @dbus_property(access=PropertyAccess.READ)
    def TxPower(self) -> "n":
        return 0

    @method()
    def Release(self) -> None:
        print("BLE advertisement released", flush=True)


async def main() -> int:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    tx = GattCharacteristic(NUS_TX_UUID, TX_PATH, ["notify", "read"])

    def on_rx(data: bytes) -> None:
        text = data.decode("utf-8", errors="replace").strip()
        message = parse_incoming_bytes(data)
        append_ble_rx(text)
        if message:
            append_ble_task(message)
        tx.notify(json_line({"type": "ack", "received": message or text}))

    service = GattService()
    rx = GattCharacteristic(NUS_RX_UUID, RX_PATH, ["write", "write-without-response"], on_write=on_rx)
    objects = {SERVICE_PATH: service, RX_PATH: rx, TX_PATH: tx}
    manager = ObjectManager(objects)
    advertisement = Advertisement()

    bus.export(APP_PATH, manager)
    bus.export(SERVICE_PATH, service)
    bus.export(RX_PATH, rx)
    bus.export(TX_PATH, tx)
    bus.export(ADV_PATH, advertisement)

    introspection = await bus.introspect(BLUEZ, ADAPTER)
    adapter_obj = bus.get_proxy_object(BLUEZ, ADAPTER, introspection)
    gatt_manager = adapter_obj.get_interface("org.bluez.GattManager1")
    adv_manager = adapter_obj.get_interface("org.bluez.LEAdvertisingManager1")

    await gatt_manager.call_register_application(APP_PATH, {})
    print("BLE GATT application registered", flush=True)
    await adv_manager.call_register_advertisement(ADV_PATH, {})
    print("BLE advertisement registered", flush=True)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await stop_event.wait()
    try:
        await adv_manager.call_unregister_advertisement(ADV_PATH)
    except Exception as exc:
        print(f"unregister advertisement failed: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
