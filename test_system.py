#!/usr/bin/env python3
"""
Test script for the API-based Pub/Sub system
Demonstrates the complete workflow
"""

import time
import subprocess
import sys
import os
import requests
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def wait_for_api_service():
    """Wait for the API service to be ready"""
    api_url = os.getenv('API_URL', 'http://localhost:5000')
    print("⏳ Waiting for API service to start...")
    print(f"   Checking: {api_url}")
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(f"{api_url}/health", timeout=1)
            if response.status_code == 200:
                print("✅ API service is ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(f"   Attempt {i+1}/{max_attempts}")
    
    print("❌ API service failed to start")
    return False

def test_api_endpoints():
    """Test the API endpoints"""
    api_url = os.getenv('API_URL', 'http://localhost:5000')
    print("\n🧪 Testing API endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{api_url}/health")
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test topic registration
    try:
        # Register a publisher
        pub_data = {"topic": "weather", "address": "localhost", "port": 5556}
        response = requests.post(f"{api_url}/register/publisher", json=pub_data)
        print(f"✅ Publisher registration: {response.json()['status']}")
        
        # Register a subscriber
        sub_data = {"topic": "weather", "address": "localhost", "port": 5557}
        response = requests.post(f"{api_url}/register/subscriber", json=sub_data)
        print(f"✅ Subscriber registration: {response.json()['status']}")
        
        # Get topic stats
        response = requests.get(f"{api_url}/topics/weather")
        stats = response.json()
        print(f"✅ Topic stats: {stats['publisher_count']} publishers, {stats['subscriber_count']} subscribers")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def run_publisher():
    """Run the API publisher"""
    print("\n📡 Starting API Publisher...")
    try:
        subprocess.run([sys.executable, "api_publisher.py", "weather"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Publisher failed: {e}")
    except KeyboardInterrupt:
        print("\n👋 Publisher stopped")

def run_subscriber():
    """Run the API subscriber"""
    print("\n👂 Starting API Subscriber...")
    try:
        subprocess.run([sys.executable, "api_subscriber.py", "weather", "5"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Subscriber failed: {e}")
    except KeyboardInterrupt:
        print("\n👋 Subscriber stopped")

def main():
    print("🚀 API-based Pub/Sub System Test")
    print("=" * 50)
    
    # Check if API service is running
    if not wait_for_api_service():
        print("\n💡 To start the API service, run:")
        print("   uv run api_service.py")
        return
    
    # Test API endpoints
    if not test_api_endpoints():
        print("❌ API tests failed")
        return
    
    print("\n🎯 System is ready! You can now:")
    print("   1. Run 'uv run api_publisher.py weather' in one terminal")
    print("   2. Run 'uv run api_subscriber.py weather 10' in another terminal")
    print("   3. Watch the messages flow!")
    
    api_url = os.getenv('API_URL', 'http://localhost:5000')
    print("\n📋 Available topics:")
    try:
        response = requests.get(f"{api_url}/topics")
        topics = response.json()["topics"]
        for topic in topics:
            print(f"   - {topic}")
    except:
        print("   - No topics registered yet")

if __name__ == "__main__":
    main()
