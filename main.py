import pynput
from sync import *


# Flag for a while loop
is_on = True


# Key listener
def on_press(key):
    global is_on

    if key == pynput.keyboard.Key.esc:
        is_on = False


listener = pynput.keyboard.Listener(on_press=on_press)
listener.start()

print("Welcome to the Synchronizer App!\nPress Esc key to stop the program.")

try:
    manager = SyncManager()

    while is_on:
        manager.sync()
except (FileNotFoundError, PermissionError, TypeError, ValueError) as error:
    print(str(error))
    is_on = False
