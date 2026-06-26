# Building EIP2771 Gasless Relayer

Building a highly scalable, fault-tolerant relayer for EIP-2771 requires a robust architecture that can efficiently handle meta-transactions at scale. 

### System Goals
1.	High Scalability: Handle thousands of concurrent meta-transactions with low latency.
2.	Fault Tolerance: No single point of failure; system should remain operational under load or partial outages.
3.	Security: Protect user data, ensure valid meta-transactions, and prevent abuse.
4.	Flexibility: Easy to integrate with various dApps and support future protocol upgrades.


## High-Level Overview
The server will have two primary threads:
1.	Relay Thread: Handles incoming meta-transaction requests, signs them, and sends them to the blockchain. Returns transaction hashes to REST API clients.
2.	Monitor Thread: Monitors the blockchain for transaction confirmations, updates the database, and generates analytical insights.




## Future works
1. The threading concept could be changed to a MessageQueuing process, with a little change in the code, greater scaliablity and redundancy can be achieved