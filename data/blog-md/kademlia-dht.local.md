# Building a Kademlia Distributed Hash Table

Kademlia is a Distributed Hash Table (DHT) protocol designed for decentralized peer-to-peer (P2P) networks. It enables efficient storage and retrieval of key-value pairs without relying on a central authority. It is widely used in file-sharing networks (e.g., BitTorrent’s DHT), blockchain networks, and decentralized applications.


Some things you should note: 
1. Every node of data has a 160bit or 20bytes unique ID
2. The node that is the closest to a key would be responsible for storing this data. the term closest is obtained by the distance metric, this quantify the disstance between nodes. This netwrok make use of the XOR operator to perform this distance metric; 
    - d(x, x) = x xor x = 0
    - d(x,y) = x xor y > 0
    - d(x,y) + d(y, z) = (x xor y) xor (y xor z) = x xor z = d(x, z)

Every node in the network would need to keep track of a feew nodes, and hope they keep track of others and so on 

Communication happens over  UDP and the routing table hols; 
node -> <ip, udp port>

when a node receives any mesage from other nodes in the network, it updates it appropraite k-bucket with the node id. 

if the routing table is full;
- node pings the laeast-recently seen node (at the haead)
- if no response, then evict and insert new node at tail
- if respond, n ew node is discarded and first node is moved to the tail (the longer a node is oonnline, the higher the probality that a node would be alive in the furture)

These are the apis that i would be implementing;
1. Ping: Probes a node to see if it is online
2. Find Node: The node returns <ip.port, node_id> for the k node it know about that are closer to the requested node. noote the intermidate node do not forward the request, they just return the nodes through which wee could reach the target. This lookup continues until the reach the target and complete the desired action.
3. STORE: Instruct a node to store the key value pair, a node locates the k-nearest node and send them the RPC


An optimization idea: Cache the key vaule pair, so when need, it is first query form the cache, if this is not avaliable in cache, send the request to the network. 


---
Possible resources i might be making use of
https://medium.com/coinmonks/a-brief-overview-of-kademlia-and-its-use-in-various-decentralized-platforms-da08a7f72b8f
https://github.com/vmandke/kademlia
https://medium.com/@vmandke/kademlia-89142a8c2627
https://github.com/f0lg0/kademlia-dht/tree/main/src
https://www.scs.stanford.edu/~dm/home/papers/kpos.pdf



# Reading the paper. 
1. Each node has a 160 bit node id.Every message transmitted contains the node id. 
2. The Keys too are 160bit id similar to the node id. 
3. To publish and find hkey,valuei pairs, Kademlia relies on a notion of distance between two identifiers. Given two 160-bit
identifiers, x and y, Kademlia defines the distance between them as their bitwise exclusive or (XOR) interpreted as an integer, d(x, y) = x ⊕ y.
4. This implemenation would be having 160 k-bucket mapping to every bit, the bucket size I would be making use of is 20. When a Kademlia node receives any message (request or reply) from another node, it updates the appropriate k-bucket for the sender’s node ID. If the sending node already exists in the recipient’s kbucket, the recipient moves it to the tail of the list. If the node is not already in the appropriate k-bucket and the bucket has fewer than k entries, then the recipient just inserts the new sender at the tail of the list. If the appropriate k-bucket is full, however, then the recipient pings the k-bucket’s least-recently seen node to decide what to do. If the least-recently seen node fails to respond, it is evicted from the k-bucket and the new sender inserted at the tail. Otherwise, if the least-recently seen node responds, it is moved to the tail of the list, and the new sender’s contact is discarded.-buckets effectively implement a least-recently seen eviction policy, except that live nodes are never removed from the list.


Still a work in progress, but this is the link to the implemention: 
https://github.com/developeruche/kademlia-dht-rust