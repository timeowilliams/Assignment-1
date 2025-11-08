#!/usr/bin/env python3
"""
External API Service for Pub/Sub System
Handles ZeroMQ orchestration and routing
"""

import zmq
import json
import threading
import time
import os
from typing import Dict, List
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from discovery_service import discovery_service

# Load environment variables
load_dotenv()

app = Flask(__name__)

class ZeroMQOrchestrator:
    def __init__(self):
        self.context = zmq.Context()
        self.publisher_sockets: Dict[str, zmq.Socket] = {}  # topic -> socket
        self.subscriber_sockets: Dict[str, List[zmq.Socket]] = {}  # topic -> list of sockets
        self.lock = threading.RLock()
    
    def create_publisher_socket(self, topic: str, port: int) -> zmq.Socket:
        """Create a publisher socket for a topic"""
        with self.lock:
            if topic not in self.publisher_sockets:
                socket = self.context.socket(zmq.PUB)
                socket.bind(f"tcp://*:{port}")
                self.publisher_sockets[topic] = socket
                print(f"Created publisher socket for topic '{topic}' on port {port}")
            return self.publisher_sockets[topic]
    
    def create_subscriber_socket(self, topic: str, publisher_address: str, publisher_port: int) -> zmq.Socket:
        """Create a subscriber socket for a topic"""
        with self.lock:
            socket = self.context.socket(zmq.SUB)
            connect_str = f"tcp://{publisher_address}:{publisher_port}"
            socket.connect(connect_str)
            socket.setsockopt_string(zmq.SUBSCRIBE, topic)
            
            if topic not in self.subscriber_sockets:
                self.subscriber_sockets[topic] = []
            self.subscriber_sockets[topic].append(socket)
            
            print(f"Created subscriber socket for topic '{topic}' connecting to {connect_str}")
            return socket
    
    def publish_message(self, topic: str, message: str) -> dict:
        """Publish a message to all subscribers of a topic"""
        with self.lock:
            if topic not in self.publisher_sockets:
                return {"status": "error", "message": f"No publisher socket found for topic '{topic}'"}
            
            socket = self.publisher_sockets[topic]
            socket.send_string(f"{topic} {message}")
            
            # Get subscriber count for response
            subscribers = discovery_service.get_subscribers_for_topic(topic)
            
            return {
                "status": "success",
                "message": f"Message published to topic '{topic}'",
                "subscriber_count": len(subscribers),
                "published_message": message
            }

# Global orchestrator instance
orchestrator = ZeroMQOrchestrator()

@app.route('/register/publisher', methods=['POST'])
def register_publisher():
    """Register a new publisher"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        address = data.get('address', 'localhost')
        port = data.get('port', 5556)
        
        if not topic:
            return jsonify({"status": "error", "message": "Topic is required"}), 400
        
        # Register with discovery service
        result = discovery_service.register_publisher(topic, address, port)
        
        # Create ZeroMQ publisher socket
        orchestrator.create_publisher_socket(topic, port)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/register/subscriber', methods=['POST'])
def register_subscriber():
    """Register a new subscriber"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        address = data.get('address', 'localhost')
        port = data.get('port', 5557)
        
        if not topic:
            return jsonify({"status": "error", "message": "Topic is required"}), 400
        
        # Check if there are publishers for this topic
        publishers = discovery_service.get_publishers_for_topic(topic)
        if not publishers:
            return jsonify({"status": "error", "message": f"No publishers found for topic '{topic}'"}), 404
        
        # Register with discovery service
        result = discovery_service.register_subscriber(topic, address, port)
        
        # Create ZeroMQ subscriber socket for each publisher
        for publisher in publishers:
            orchestrator.create_subscriber_socket(topic, publisher.address, publisher.port)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/publish', methods=['POST'])
def publish_message():
    """Publish a message to a topic"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        message = data.get('message')
        
        if not topic or not message:
            return jsonify({"status": "error", "message": "Topic and message are required"}), 400
        
        result = orchestrator.publish_message(topic, message)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/topics', methods=['GET'])
def get_topics():
    """Get all registered topics"""
    topics = discovery_service.get_all_topics()
    return jsonify({"topics": list(topics)})

@app.route('/topics/<topic>', methods=['GET'])
def get_topic_stats(topic):
    """Get statistics for a specific topic"""
    stats = discovery_service.get_topic_stats(topic)
    return jsonify(stats)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ZeroMQ API Service"})

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print("Starting ZeroMQ API Service...")
    print(f"Listening on {host}:{port}")
    print("Available endpoints:")
    print("  POST /register/publisher - Register a publisher")
    print("  POST /register/subscriber - Register a subscriber")
    print("  POST /publish - Publish a message")
    print("  GET /topics - Get all topics")
    print("  GET /topics/<topic> - Get topic statistics")
    print("  GET /health - Health check")
    
    app.run(host=host, port=port, debug=True)
