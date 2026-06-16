class Button:
    """Placeholder button interface for RK3506JS.

    Replace this with GPIO/libgpiod/evdev support after the physical button is
    confirmed.
    """

    def is_pressed(self) -> bool:
        return False

    def poll_event(self):
        return None


def main() -> None:
    button = Button()
    print({"pressed": button.is_pressed(), "event": button.poll_event()})


if __name__ == "__main__":
    main()
