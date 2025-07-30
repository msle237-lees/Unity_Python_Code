import requests
import time


def main():
    """
    Main function to combine agent actions and sensor data into expert paths
    and store them in the expert_path table via POST requests.
    """
    base_url = "http://localhost:5000"
    get_action_url = f"{base_url}/get_action"
    get_sensor_url = f"{base_url}/get_sensor_data"
    post_expert_url = f"{base_url}/post_expert_path"

    while True:
        # Step 1: Get latest action
        action_response = requests.get(get_action_url)
        if action_response.status_code != 200:
            print("Failed to retrieve action:", action_response.text)
            time.sleep(1)
            continue
        action_data = action_response.json()

        # Step 2: Get latest sensor reading
        sensor_response = requests.get(get_sensor_url)
        if sensor_response.status_code != 200:
            print("Failed to retrieve sensor data:", sensor_response.text)
            time.sleep(1)
            continue
        sensor_data = sensor_response.json()

        # Step 3: Combine into expert path format
        expert_record = {
            "step_index": action_data["step_index"],
            "direction": action_data["direction"],
            "force_level": action_data["force_level"],
            "arm": action_data["arm"],
            "X": sensor_data["X"],
            "Y": sensor_data["Y"],
            "Z": sensor_data["Z"],
            "Roll": sensor_data["Roll"],
            "Pitch": sensor_data["Pitch"],
            "Yaw": sensor_data["Yaw"]
        }

        # Step 4: Send to expert path table
        post_response = requests.post(post_expert_url, json=expert_record)
        if post_response.status_code == 200:
            print(f"Successfully posted step_index {expert_record['step_index']}")
        else:
            print("Failed to post expert record:", post_response.text)

        # Optional: Slow down polling
        time.sleep(0.1)


if __name__ == "__main__":
    main()
