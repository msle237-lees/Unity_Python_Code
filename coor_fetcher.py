import pyautogui
import keyboard
import time

print("Move your mouse to the desired location and press 'K' to save the coordinates.")
print("Press 'ESC' to exit.")

saved_coordinates = []

def save_coordinates():
    """Capture and store the current mouse position when 'K' is pressed."""
    x, y = pyautogui.position()
    saved_coordinates.append((x, y))
    print(f"\nSaved Coordinate: X={x}, Y={y}")

# Register the 'K' key for saving coordinates
keyboard.add_hotkey("k", save_coordinates)

try:
    while True:
        time.sleep(0.1)  # Reduce CPU usage
        if keyboard.is_pressed("esc"):  # Press ESC to exit
            print("\nExiting...")
            break
except KeyboardInterrupt:
    print("\nStopped.")

# Print all saved coordinates before exiting
if saved_coordinates:
    print("\nSaved Coordinates:")
    for i, (x, y) in enumerate(saved_coordinates, start=1):
        print(f"{i}: X={x}, Y={y}")
