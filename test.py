from threading import Thread
import time
import threading

quit_event = threading.Event()
signal.signal(signal.SIGTERM, lambda *_args: quit_event.set())

def f():
    print("f")
    time.sleep(10)
    print("ff")

def d():
    print("d")
    time.sleep(10)
    print("d")


if __name__ == '__main__':
    a = Thread(target = f)
    b = Thread(target = d)
    a.start()
    b.start()
