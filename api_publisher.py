#!/usr/bin/env python3
"""
API-based Publisher
Uses external API service for ZeroMQ orchestration
"""

import requests
import json
import time
import sys
import os
from random import randrange
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIPublisher:
    def __init__(self, api_base_url=None):
        self.api_base_url = api_base_url or os.getenv('API_URL', 'http://localhost:5000')
        self.topic = None
        self.address = None
        self.port = None
    
    def register(self, topic: str, address: str = "localhost", port: int = 5556):
        """Register this publisher with the API service"""
        self.topic = topic
        self.address = address
        self.port = port
        
        payload = {
            "topic": topic,
            "address": address,
            "port": port
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/register/publisher", json=payload)
            result = response.json()
            
            if result["status"] == "success":
                print(f"✅ Publisher registered successfully for topic '{topic}'")
                print(f"   Address: {address}:{port}")
                return True
            else:
                print(f"❌ Failed to register publisher: {result['message']}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to API service. Make sure it's running on {self.api_base_url}")
            return False
        except Exception as e:
            print(f"❌ Error registering publisher: {e}")
            return False
    
    def publish_message(self, message: str):
        """Publish a message to the registered topic"""
        if not self.topic:
            print("❌ Publisher not registered. Call register() first.")
            return False
        
        payload = {
            "topic": self.topic,
            "message": message
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/publish", json=payload)
            result = response.json()
            
            if result["status"] == "success":
                print(f"📤 Published to '{self.topic}': {message}")
                print(f"   Sent to {result['subscriber_count']} subscribers")
                return True
            else:
                print(f"❌ Failed to publish: {result['message']}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to API service")
            return False
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            return False
    
    def publish_weather_data(self):
        """Publish random weather data (like the original publisher)"""
        zipcode = randrange(1, 100000)
        temperature = randrange(-80, 135)
        relhumidity = randrange(10, 60)
        
        message = f"{zipcode} {temperature} {relhumidity}"
        return self.publish_message(message)

def main():
    # Get topic from command line or use default
    topic = sys.argv[1] if len(sys.argv) > 1 else "weather"
    
    publisher = APIPublisher()
    api_url = publisher.api_base_url
    
    print(f"🌤️  Starting API-based Weather Publisher")
    print(f"   Topic: {topic}")
    print(f"   API Service: {api_url}")
    print()
    
    # Register the publisher
    if not publisher.register(topic):
        print("Failed to register publisher. Exiting.")
        return
    
    print(f"📡 Publisher ready! Publishing weather updates...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        # Keep publishing weather data
        while True:
            publisher.publish_weather_data()
            time.sleep(1)  # Publish every second
            
    except KeyboardInterrupt:
        print("\n👋 Publisher stopped by user")

if __name__ == "__main__":
    main()
