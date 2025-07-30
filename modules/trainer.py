import requests
import time


def main():
    """
    Combine the latest action and sensor data into expert path entries,
    and post them to the expert_path endpoint, avoiding duplicates.
    """
    base_url = "http://localhost:5000"
    get_action_url = f"{base_url}/get_action"
    get_sensor_url = f"{base_url}/get_sensor_data"
    post_expert_url = f"{base_url}/post_expert_path"

    last_step_index = -1  # Initialize to an invalid index

    while True:
        # Step 1: Get latest action
        try:
            action_response = requests.get(get_action_url)
            if action_response.status_code != 200:
                print("Failed to retrieve action:", action_response.text)
                time.sleep(1)
                continue
            action_data = action_response.json()
        except Exception as e:
            print(f"Exception getting action: {e}")
            time.sleep(1)
            continue

        # Deduplication check
        current_step_index = action_data.get("step_index")
        if current_step_index == last_step_index:
            time.sleep(0.1)
            continue

        # Step 2: Get latest sensor reading
        try:
            sensor_response = requests.get(get_sensor_url)
            if sensor_response.status_code != 200:
                print("Failed to retrieve sensor data:", sensor_response.text)
                time.sleep(1)
                continue
            sensor_data = sensor_response.json()
        except Exception as e:
            print(f"Exception getting sensor data: {e}")
            time.sleep(1)
            continue

        # Step 3: Combine data
        expert_record = {
            "step_index": current_step_index,
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

        # Step 4: Post to expert path
        try:
            post_response = requests.post(post_expert_url, json=expert_record)
            if post_response.status_code == 200:
                print(f"✅ Posted step_index {current_step_index}")
                last_step_index = current_step_index
            else:
                print(f"❌ Failed to post: {post_response.status_code} {post_response.text}")
        except Exception as e:
            print(f"Exception posting expert path: {e}")

        time.sleep(0.1)


if __name__ == "__main__":
    main()

