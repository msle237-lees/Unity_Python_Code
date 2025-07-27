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

    # Step 2: Save expert paths to a JSON file
    with open("expert_paths.json", "w") as json_file:
        json.dump(expert_paths, json_file, indent=4)

    print("Expert paths saved to expert_paths.json")


if __name__ == "__main__":
    main()