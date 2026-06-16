from datetime import datetime


def _log(kind: str, value) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [{kind}] {value}", flush=True)


def show_status(status) -> None:
    _log("status", status)


def show_task(task) -> None:
    _log("task", task)


def show_result(result) -> None:
    _log("result", result)


def show_error(error) -> None:
    _log("error", error)
