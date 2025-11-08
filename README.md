# Assignment-1
Timeo Williams
CS 6381-50 Distributed Systems Principles


In tacking this assignment, the first thing I did was copy the Pub-Sub folder from the examples repo and put in the assignment 1 repo. I then used uv, a python package manager, to install the pyzmq dependency and run the publisher.py & subscriber.py in two separate terminals. 

Upon invokation, 

publisher.py

```
(base) timwilliams@Tims-MacBook-Pro Assignment1 % uv run publisher.py
Current libzmq version is 4.3.5
Current  pyzmq version is 27.1.0
```

subscriber.py

```
(base) timwilliams@Tims-MacBook-Pro Assignment1 % uv run subscriber.py
\Collecting updates from weather server...
Average temperature for zipcode '10001' was 43F
```


The task for assignment 1 states as follows: 

> A more desirable solution therefore is where the application logic of the publishers and subscribers remains anonymous to each other; naturally somebody and at some level must still need to maintain these associations thereby breaking the definition but that is ok as long as the application-level logic complies with the ideal definition. So, in our assignment, we are going to push this responsibility to a layer of middleware that we are going to design and then have our application logic use the API of our middleware instead of directly using ZMQ API.

To allow for this to be decoupled in the sense that the subscriber doesn't directly know the publisher, we'll be adding a CS6381 API to act as middleware in between the pub/sub to create anonymity. 


I'm thinking that the CS6381 API should have its own PORT. And instead of the publisher dirrectly connecting to the sub using the tcp protocol, it connects to the CS6381 API. The CS6381 API will take an argument for the PORT for the directed subscriber and then from this create a connection and forward the arguements. 

On looking at the assignment details more closely, there's a strict mention that the publisher and subscriber should not use ZMQ directly. So all of the method invokations from ZMQ should be occurring inside the CS6381 API


```nginx
Publisher -> CS6381 API -> ZMQ
Subscriber -> CS6381 API -> ZMQ
```

Defining the CS6381 API 

Given that this should support is *many-to-many connections* (I cannot assume just 1 publisher or 1 subscriber)
``` bash
P1 ──>  Topic A  ─┐
P2 ──>  Topic A  ─┤──>  S1
P3 ──>  Topic B  ─┘     S2
`
```
And the discovery service will maintain a registry like this:
```python
{
  "topicA": {"publishers": ["P1", "P2"], "subscribers": ["S1"]},
  "topicB": {"publishers": ["P3"], "subscribers": ["S2"]}
}
```

| Entity                                            | Role                 | What It Does in Milestone 1                                                                        |
| ------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| **Discovery Service**                             | Server               | Maintains registry of all publishers and subscribers; replies to registration & readiness queries. |
| **Publisher App**                                 | Client               | Registers its topics with Discovery via middleware.                                                |
| **Subscriber App**                                | Client               | Registers its interests (topics) with Discovery via middleware.                                    |
| **CS6381 Middleware (Publisher/Subscriber side)** | API + Client wrapper | Hides ZMQ REQ/REP socket details from the app.                                                     |




```python
class CS6381 API 


def register()
    accepts an argument, topic, which is a string. And then makes ZeroMQ calls the Context API to establish a container/environment for all sockets 

    After the context is registered, we can perform the methods of creating a socket, binding to a port BASED off the topic that the newly created pub/sub service requests, perform any business logic associated with that given topic, and last, but not least, make sure to store the newly created metadata (keeping track of new pub subs and what topics they're associated with) - this should be known to the discovery service & persisted there. 

    As far as unique identifiers (i think since we're using a queue data structure) - we can use the index within the array as the ID. Given that there are NO LATE Comers, I can assume that none of the pub/sub services will leave the system, so we don't have to write logic to handle reassignment/removal. 


def sendMessage(topic, msg (optional, defaults to ""))
    given that the CS6381 API houses the business logic associated for actions to be performed given a topic. The moment that a publisher would like to disseminate a new message, it sends a msg and we will compute anything necessary for that given topic and also perform the act of pushing that message out to the list of subscribers (queue datastructure)


class CS6381API:
    def register(self, role, topics, addr):
        # still REQ/REP with Discovery

    def lookup(self, topic):
        # REQ/REP with Discovery, return publisher addresses

    def publish(self, topic, msg):
        # if role == publisher, send via PUB socket

    def subscribe(self, topic, callback):
        # if role == subscriber, connect SUB socket(s)
        # invoke callback on message arrival

def lookup()
    checks to see if a given topic is live? Handled by the discovery service



```












