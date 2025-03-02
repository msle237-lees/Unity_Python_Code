import argparse
import time




if __name__ == "__main__":
    time.sleep(5)
    parser = argparse.ArgumentParser(description="AI Package")
    parser.add_argument("--host", type=str, help="Host address")
    parser.add_argument("--port", type=int, help="Port number")
    args = parser.parse_args()

    print(f"Model: {args.model}")
    print(f"Data: {args.data}")





