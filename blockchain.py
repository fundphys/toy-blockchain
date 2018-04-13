import hashlib
import json
import sys
import requests
from time import time
from textwrap import dedent
from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        #Create genesis block
        self.new_block(previous_hash=1, proof=100)
    
    def valid_chain(self, chain):
        """
        Detrmine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not 
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n------------\n")
            #chack that the hash of the block is correct
            if block["previous_hash"] != self.hash(last_block):
                return False
            
            #Check that the Proof of Work is correct
            if not self.valide_proof(last_block["proof"], block["proof"]):
                return False

            last_block = block 
            current_index += 1

        return True
    
    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes 
        new_chain = None

        #We're only looking fr chains longer than ours 
        max_length = len(self.chain)

        #Grab and verify the chains from all the nodes in our network 
        for node in neighbours:
            response = requests.get(f"http://{node}/chain")

            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]

                #Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        #Replace our chain if we discovered a new, valid chain longer then ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def register_node(self, address):
        """
        Add a new node to the list of nodes.
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1])
        }
        
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        })
        return self.last_block["index"] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of block
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valide_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof * proof ) contains 4 leading zeros?
        """
        guess = f"{last_proof*proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == "00"


    def proof_of_work(self, last_proof):
        """
        Simple Proof_of_Work Algorithm:
        - Find a number p' such that hash(p*p') contain leading 4 zeros where p is previous p'
        - p is the previous proof, and p' is the new proof

        :param last_proof: <int> 
        :return: <int>
        """
        print("proof_of_work call!")
        proof = 0
        while self.valide_proof(last_proof, proof) is False:
            proof += 1

        return proof


app = Flask(__name__)
node_identifier = str(uuid4()).replace("-", "")
blockchain = Blockchain()


@app.route("/mine", methods=["GET"])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)
    print(proof)

    blockchain.new_transaction(
        sender = "0",
        recipient = node_identifier, 
        amount = 1,
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }
    
    return jsonify(response), 200



@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()
    print(values)
    #check that all fields in POST data
    requared = ["sender", "recipient", "amount"]
    if not all([k in values for k in requared]):
        return "Missing values", 400

    #Create a new Transition
    index = blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])
    response = {"message" : "Transaction will be added to Block {}".format(index)}
    return jsonify(response), 201



@app.route("/chain", methods = ["GET"])
def full_chain():
    response = {
        "chain" : blockchain.chain,
        "length" : len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route("/nodes/register", methods=["POST"])
def register_node():
    values = request.get_json()
    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        "message": "New node have been added",
        "total_nodes": list(blockchain.nodes),
    }

    return jsonify(response), 201

@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            "message": "Our chain was replaced",
            "new_chain": blockchain.chain,
        }
    else:
        response = {
            "message": "Our chain is authoritative",
            "new_chain": blockchain.chain,
        }

    return jsonify(response), 200 


def main(argv):
    port = int(argv)
    app.run(host="0.0.0.0", port = port)


if __name__ == "__main__":
   main(sys.argv[1])
