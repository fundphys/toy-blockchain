# toy-blockchain

# Main idea source: 
#    https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

# start guide 
#    python3 -m venv env
#    source env/bin/activate
#    pip insatll --upgrade pip
#    pip install Flask==0.12.2
#    pip install requests==2.18.4 

# python3 blockchain.py [port] - it run script and bind 127.0.0.1:[port] 

# Mine new block 
#    curl -G http://localhost:5000/mine

# Add a transaction to block
#   curl -X POST -H "Content-Type: application/json" -d '{
#       "sender": "0x01",
#       "recipient": "0x02",
#       "amount": 5
#       }' "http://localhost:5000/transactions/new" 

# Register new node "5001" on node "5000"
#   curl -X POST -H "Content-Type: application/json" -d '{
#       "nodes": ["http://127.0.0.1:5001"]
#       }' "http://localhost:5000/nodes/register"

# Get all chain 
#   curl -G http://localhost:5000/chain

# Resolve collision
#    curl - G http://localhost:5000/nodes/resolve





