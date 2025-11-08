#!/usr/bin/env python3
"""
Discovery Service for Pub/Sub System
Manages topic registration and subscriber routing
"""

import json
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
import threading
import time

@dataclass
class Publisher:
    topic: str
    address: str
    port: int
    registered_at: float

@dataclass
class Subscriber:
    topic: str
    address: str
    port: int
    registered_at: float

class DiscoveryService:
    def __init__(self):
        self.publishers: Dict[str, List[Publisher]] = {}  # topic -> list of publishers
        self.subscribers: Dict[str, List[Subscriber]] = {}  # topic -> list of subscribers
        self.lock = threading.RLock()
    
    def register_publisher(self, topic: str, address: str, port: int) -> dict:
        """Register a new publisher for a topic"""
        with self.lock:
            publisher = Publisher(topic=topic, address=address, port=port, registered_at=time.time())
            
            if topic not in self.publishers:
                self.publishers[topic] = []
            
            self.publishers[topic].append(publisher)
            
            return {
                "status": "success",
                "message": f"Publisher registered for topic '{topic}'",
                "publisher": asdict(publisher)
            }
    
    def register_subscriber(self, topic: str, address: str, port: int) -> dict:
        """Register a new subscriber for a topic"""
        with self.lock:
            subscriber = Subscriber(topic=topic, address=address, port=port, registered_at=time.time())
            
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            
            self.subscribers[topic].append(subscriber)
            
            return {
                "status": "success",
                "message": f"Subscriber registered for topic '{topic}'",
                "subscriber": asdict(subscriber)
            }
    
    def get_publishers_for_topic(self, topic: str) -> List[Publisher]:
        """Get all publishers for a specific topic"""
        with self.lock:
            return self.publishers.get(topic, [])
    
    def get_subscribers_for_topic(self, topic: str) -> List[Subscriber]:
        """Get all subscribers for a specific topic"""
        with self.lock:
            return self.subscribers.get(topic, [])
    
    def get_all_topics(self) -> Set[str]:
        """Get all registered topics"""
        with self.lock:
            topics = set(self.publishers.keys())
            topics.update(self.subscribers.keys())
            return topics
    
    def get_topic_stats(self, topic: str) -> dict:
        """Get statistics for a topic"""
        with self.lock:
            publisher_count = len(self.publishers.get(topic, []))
            subscriber_count = len(self.subscribers.get(topic, []))
            
            return {
                "topic": topic,
                "publisher_count": publisher_count,
                "subscriber_count": subscriber_count,
                "publishers": [asdict(p) for p in self.publishers.get(topic, [])],
                "subscribers": [asdict(s) for s in self.subscribers.get(topic, [])]
            }

# Global discovery service instance
discovery_service = DiscoveryService()
