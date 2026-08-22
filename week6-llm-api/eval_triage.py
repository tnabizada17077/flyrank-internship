import json
import time
import requests

def run_eval():
    with open("evals/cases.json", "r") as f:
        cases = json.load(f)

    passed = 0
    total = len(cases)

    print("=== Running LLM Triage Eval Set ===")
    for case in cases:
        try:
            resp = requests.post("http://127.0.0.1:8000/triage", json={"text": case["input"]})
            if resp.status_code == 200:
                data = resp.json()
                if data["category"] == case["expected_category"]:
                    passed += 1
                    print(f"[PASS] '{case['input']}' -> {data['category']}")
                else:
                    print(f"[FAIL] '{case['input']}' -> Got: {data['category']}, Expected: {case['expected_category']}")
            else:
                print(f"[FAIL] Status {resp.status_code} for input: '{case['input']}'")
        except Exception as e:
            print(f"[ERROR] Could not reach server: {e}")
            return
        
        # Pause to stay within free-tier Rate Limits (RPM)
        time.sleep(1.5)

    print(f"\nEval Score: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")

if __name__ == "__main__":
    run_eval()