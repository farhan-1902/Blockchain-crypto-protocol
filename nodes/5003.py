#requests module is required
# Creating a cryptocurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import time
import requests

#Part 1 - Building the blockchain
#For the cryptocurrency, we need to add transactions to the blockchain

class Blockchain:
    
    def __init__(self): 
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0') #This is the genesis block.
        self.nodes = set() #A set to contain nodes of the blockchain
    
    #This function is called right after a block is mined.
    def create_block(self, proof, previous_hash): 
        block = {'index': len(self.chain)+1, 
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof, #This is the nonce
                 'previous_hash': previous_hash, 
                 'transactions': self.transactions} #This contains the index, timestamp, proof, previous hash, transactions.
        
        #Making the transactions list empty
        self.transactions = []
        
        self.chain.append(block)
        
        return block
    
    def get_previous_block(self): 
        return self.chain[-1]
    
    #Proof of work is the problem that miners have to solve. 
    def proof_of_work(self, previous_proof): 
        new_proof = 1 
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest() #Operation should be non-symmetric
            
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1    
                
        return new_proof
    
    #Check if each block has correct proof of work and if the previous hash is correct.
    
    def hash(self, block): #Returns the hash of a block
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest() 
            
            if hash_operation[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
            
        return True
    
    #Creating a method to add a transaction to the blockchain
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
        
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1     #Returning the index of the block to which the transaction is added
    
    #A method to add a node
    def add_node(self, address): 
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    #Deriving the consensus protocol to follow the longest chain rule
    def replace_chain(self): 
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain) #The current chain at the time of this function being called.
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain') #Getting the chain corresponding to each node.
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
#Part 2 - Mining the blockchain

#Creating a web app
app = Flask(__name__)

#Creating an address for node on port 5000
node_address = str(uuid4()).replace('-', '')

#Creating the blockchain
blockchain = Blockchain()

#Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'User2', amount = 1000)
    block = blockchain.create_block(proof, previous_hash)
    
    response = {'message': 'Congratulations, you just mined a block!', 
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    
    return jsonify(response), 200  #THIS IS THE HTTP STATUS, 200 means OK

#Getting the full blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain, 
                'length': len(blockchain.chain)}
    
    return jsonify(response), 200

#Checking if the blockchain is valid

@app.route('/is_valid', methods=['GET'])
def is_valid():
    chain = blockchain.chain
    response = {'status': blockchain.is_chain_valid(chain)}
    
    return jsonify(response), 200

#Adding a new transaction to the blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount'] #Every transaction must have these keys.
    
    if not all (key in json for key in transaction_keys):
        return 'Error! Please try again', 400
    
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    
    response = {'message': f'Transaction added to block {index}'}
    
    return jsonify(response), 201


#Part 3 - Decentralizing the blockchain

#Adding new nodes to the blockchain
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes') #This will be a list of nodes posted to be added to the chain
    
    if nodes is None:
        return 'No nodes found', 400    
    
    for node in nodes:
        blockchain.add_node(node)
    
    response = {'message': 'All nodes added',
                'total_nodes': list(blockchain.nodes)}
    
    return jsonify(response), 201

#Consensus: Replacing the chain by the longest chain if required
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    
    if is_chain_replaced:
        response = {'message': 'The nodes have been updated.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All nodes have the largest chain',
                    'existing_chain': blockchain.chain}
    
    return jsonify(response), 201
    
# if(len(blockchain.chain) > 1 and len(blockchain.nodes) > 0):
#     requests.get('http://127.0.0.1:5002/replace_chain')
#     time.sleep(10)

#Runnning the app
app.run(host='172.20.10.11  ', port=5003)