#!/usr/bin/env python3
"""
API-based Subscriber
Uses external API service for ZeroMQ orchestration
"""

import requests
import json
import time
import sys
import threading
import os
import zmq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APISubscriber:
    def __init__(self, api_base_url=None):
        self.api_base_url = api_base_url or os.getenv('API_URL', 'http://localhost:5000')
        self.topic = None
        self.address = None
        self.port = None
        self.context = zmq.Context()
        self.socket = None
        self.running = False
        self.message_count = 0
        self.total_temp = 0
    
    def register(self, topic: str, address: str = "localhost", port: int = 5557):
        """Register this subscriber with the API service"""
        self.topic = topic
        self.address = address
        self.port = port
        
        payload = {
            "topic": topic,
            "address": address,
            "port": port
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/register/subscriber", json=payload)
            result = response.json()
            
            if result["status"] == "success":
                print(f"✅ Subscriber registered successfully for topic '{topic}'")
                print(f"   Address: {address}:{port}")
                
                # Get publisher information to connect directly
                stats_response = requests.get(f"{self.api_base_url}/topics/{topic}")
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    if stats["publishers"]:
                        publisher = stats["publishers"][0]  # Connect to first publisher
                        self._connect_to_publisher(publisher["address"], publisher["port"])
                
                return True
            else:
                print(f"❌ Failed to register subscriber: {result['message']}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to API service. Make sure it's running on {self.api_base_url}")
            return False
        except Exception as e:
            print(f"❌ Error registering subscriber: {e}")
            return False
    
    def _connect_to_publisher(self, publisher_address: str, publisher_port: int):
        """Connect directly to publisher using ZeroMQ"""
        try:
            self.socket = self.context.socket(zmq.SUB)
            connect_str = f"tcp://{publisher_address}:{publisher_port}"
            self.socket.connect(connect_str)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)
            
            print(f"🔗 Connected to publisher at {connect_str}")
            print(f"   Subscribed to topic: {self.topic}")
            
        except Exception as e:
            print(f"❌ Error connecting to publisher: {e}")
    
    def start_listening(self, max_messages: int = 10):
        """Start listening for messages"""
        if not self.socket:
            print("❌ Not connected to any publisher. Call register() first.")
            return
        
        print(f"👂 Listening for messages on topic '{self.topic}'...")
        print(f"   Will process up to {max_messages} messages")
        print("   Press Ctrl+C to stop")
        print()
        
        self.running = True
        self.message_count = 0
        self.total_temp = 0
        
        try:
            while self.running and self.message_count < max_messages:
                try:
                    # Set timeout to avoid blocking indefinitely
                    if self.socket.poll(1000):  # 1 second timeout
                        message = self.socket.recv_string()
                        self._process_message(message)
                    else:
                        # No message received, continue
                        continue
                        
                except zmq.Again:
                    # Timeout occurred, continue
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            if self.message_count > 0:
                avg_temp = self.total_temp / self.message_count
                print(f"\n📊 Average temperature for topic '{self.topic}': {avg_temp:.1f}°F")
                print(f"   Processed {self.message_count} messages")
            
        except KeyboardInterrupt:
            print("\n👋 Subscriber stopped by user")
        finally:
            self.running = False
    
    def _process_message(self, message: str):
        """Process received message"""
        try:
            parts = message.split()
            if len(parts) >= 3:
                topic = parts[0]
                zipcode = parts[1]
                temperature = int(parts[2])
                relhumidity = parts[3] if len(parts) > 3 else "N/A"
                
                self.message_count += 1
                self.total_temp += temperature
                
                print(f"📨 [{self.message_count:2d}] {topic}: Zip {zipcode}, Temp {temperature}°F, Humidity {relhumidity}%")
                
        except (ValueError, IndexError) as e:
            print(f"❌ Error parsing message '{message}': {e}")
    
    def stop(self):
        """Stop the subscriber"""
        self.running = False
        if self.socket:
            self.socket.close()
        self.context.term()

def main():
    # Get topic from command line or use default
    topic = sys.argv[1] if len(sys.argv) > 1 else "weather"
    max_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    subscriber = APISubscriber()
    api_url = subscriber.api_base_url
    
    print(f"🌤️  Starting API-based Weather Subscriber")
    print(f"   Topic: {topic}")
    print(f"   Max messages: {max_messages}")
    print(f"   API Service: {api_url}")
    print()
    
    # Register the subscriber
    if not subscriber.register(topic):
        print("Failed to register subscriber. Exiting.")
        return
    
    # Start listening for messages
    subscriber.start_listening(max_messages)
    
    # Cleanup
    subscriber.stop()

if __name__ == "__main__":
    main()
