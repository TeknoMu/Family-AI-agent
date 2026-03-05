# Quick test: python scripts/test_api.py "Ho mal di stomaco"
import sys
import httpx


def test_chat(msg):
    print(f"Sending: {msg}")
    print("Waiting for response (can take 15-30 seconds)...")
    r = httpx.post(
        "http://localhost:8000/chat",
        json={"user_id": "test", "message": msg},
        timeout=60.0,
    )
    if r.status_code == 200:
        data = r.json()
        print(f"\nDomain: {data['domain']}\n")
        print(data["response"])
    else:
        print(f"Error {r.status_code}: {r.text}")


if __name__ == "__main__":
    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Ciao, come stai?"
    test_chat(message)
