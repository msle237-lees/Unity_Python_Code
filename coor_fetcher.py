import pyautogui
import time

def print_mouse_coordinates():
    print("Move your mouse. Coordinates will print every 0.5 seconds. Press Ctrl+C to stop.")
    try:
        while True:
            x, y = pyautogui.position()
            print(f"Mouse Position: X={x}, Y={y}", end="\r")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == '__main__':
    print_mouse_coordinates()
