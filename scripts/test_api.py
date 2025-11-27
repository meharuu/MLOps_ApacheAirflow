"""
Test FastAPI endpoints
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check"""
    print("\n1️⃣ Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_model_info():
    """Test model info endpoint"""
    print("\n2️⃣ Testing model info...")
    response = requests.get(f"{BASE_URL}/model-info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_single_prediction():
    """Test single prediction"""
    print("\n3️⃣ Testing single prediction...")
    payload = {
        "features": {
            "age": 30,
            "salary": 50000,
            "country": "US"
        }
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_batch_prediction():
    """Test batch prediction"""
    print("\n4️⃣ Testing batch prediction...")
    payload = {
        "features_list": [
            {"age": 30, "salary": 50000, "country": "US"},
            {"age": 35, "salary": 60000, "country": "UK"},
            {"age": 40, "salary": 70000, "country": "DE"}
        ]
    }
    response = requests.post(f"{BASE_URL}/predict-batch", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")


def test_past_predictions():
    """Test past predictions"""
    print("\n5️⃣ Testing past predictions...")
    payload = {
        "start_date": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "source": "all",
        "limit": 10
    }
    response = requests.post(f"{BASE_URL}/past-predictions", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ML API")
    print("=" * 60)
    
    try:
        test_health_check()
        test_model_info()
        test_single_prediction()
        test_batch_prediction()
        test_past_predictions()
        
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"❌ Error: {e}")