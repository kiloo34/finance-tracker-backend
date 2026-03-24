import requests

BASE_URL = "http://localhost:8001"

print("1. Registering User...")
reg_res = requests.post(f"{BASE_URL}/auth/register", json={"username": "admin", "password": "password"})
if reg_res.status_code == 200:
    print("Registered Successfully!")
elif reg_res.status_code == 400 and "Username already registered" in reg_res.text:
    print("User already exists, continuing...")
else:
    print(f"Failed to register: {reg_res.text}")

print("\n2. Logging in...")
login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "password"})
if login_res.status_code == 200:
    token = login_res.json()["access_token"]
    print("Logged in Successfully! Token received.")
else:
    print(f"Failed to login: {login_res.text}")
    exit(1)

print("\n3. Testing /evaluate Endpoint...")
eval_res = requests.get(f"{BASE_URL}/evaluate", headers={"Authorization": f"Bearer {token}"})
if eval_res.status_code == 200:
    eval_data = eval_res.json()
    print("Evaluate Result:")
    for key, value in eval_data.items():
        print(f"  {key}: {value}")
else:
    print(f"Failed to evaluate: {eval_res.text}")
