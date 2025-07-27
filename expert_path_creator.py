import requests
import json


def main():
    """
    Main function to record expert paths from the database and save them to a JSON file.
    """
    # Step 1: Retrieve expert paths from the API
    response = requests.get("http://localhost:5000/expert_path")
    if response.status_code != 200:
        print("Error retrieving expert paths")
        return

    expert_paths = response.json()

    # Step 2: Make a post request to the expert_path endpoint to save the paths
    for path in expert_paths:
        post_response = requests.post("http://localhost:5000/expert_path", json=path)
        if post_response.status_code != 200:
            print(f"Error saving expert path: {post_response.text}")
            continue


if __name__ == "__main__":
    main()