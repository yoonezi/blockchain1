import time
import hashlib
import json
from uuid import uuid4
from urllib.request import urlopen

class Blockchain:
    def __init__(self, current_node_url=None):
        self.chain = []
        self.pending_transactions = []
        self.current_node_url = current_node_url

        self.merkle_tree_proecss = []
        self.network_nodes = []
        self.genesis_nonce = self.proof_of_work(self.hash_function('0'), {'merkle_root':self.create_merkle_tree([self.hash_function(str(tx)) for tx in self.pending_transactions]),'index' : 1})
        if len(self.chain) == 0 :
            self.add_genesis_transaction({'amount' : 50,'sender': '0','recipient':self.node_address(),'transaction_id' : str(uuid4()).replace('-','')})
        self.create_new_block(self.genesis_nonce, self.hash_function('0'), self.hash_block(self.hash_function('0'), {'merkle_root':self.create_merkle_tree([self.hash_function(str(tx)) for tx in self.pending_transactions]),'index' : 1},self.genesis_nonce),self.create_merkle_tree([self.hash_function(str(tx)) for tx in self.pending_transactions]))
        if(len(self.chain) == 1):
            self.pending_transactions.append(self.create_new_transaction(6.25,'00',"00"))
        

    def create_new_block(self, nonce, previous_block_hash, hash_, merkle_root):
        new_block = {
            'index': len(self.chain) + 1,
            'timestamp': int(time.time() * 1000),
            'transactions': self.pending_transactions,
            'merkle_root': merkle_root,
            'nonce': nonce,
            'hash': hash_,
            'previous_block_hash': previous_block_hash
        }
        self.pending_transactions = []
        
        self.chain.append(new_block)
        return new_block
    
    def get_last_block(self):
        return self.chain[len(self.chain) - 1]
    
    def create_new_transaction(self,amount,sender,recipient):
        new_transaction = {
            'amount' : amount,
            'sender' : sender,
            'recipient' : recipient,
            'transaction_id': str(uuid4()).replace('-', '')
        }
        return new_transaction

    def hash_block(self, previous_block_hash, current_block_data, nonce):
        data_as_string = previous_block_hash + str(nonce) + json.dumps(current_block_data, separators=(',', ':'))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        hash_object = hashlib.sha256(data_as_string.encode())
        hash_ = hash_object.hexdigest()
        return hash_
    
    def proof_of_work(self,previous_block_hash, current_block_data):
        nonce = 0
        hash_ = self.hash_block(previous_block_hash, current_block_data, nonce)
        while hash_[:4] != '0000':
            nonce += 1
            hash_ = self.hash_block(previous_block_hash, current_block_data, nonce)
            print(hash_)
        return nonce
    
    def add_transaction_to_pending_transactions(self,transaction_obj):
        self.pending_transactions.append(transaction_obj)
        return self.get_last_block()['index'] + 1
    
    def add_genesis_transaction(self,transaction_obj):
        self.pending_transactions.append(transaction_obj)
        return True

    
    def get_block(self, block_hash):
        correct_block = None
        for block in self.chain:
            if block['hash'] == block_hash:
                correct_block = block
                break
        return correct_block

    def get_transaction(self, transaction_id):
        correct_transaction = None
        correct_block = None
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['transaction_id'] == transaction_id:
                    correct_transaction = transaction
                    correct_block = block
                    break
            if correct_transaction:
                break
        return {
            'transaction': correct_transaction,
            'block': correct_block
        }

    def get_address_data(self, address):
        address_transactions = []
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['sender'] == address or transaction['recipient'] == address:
                    address_transactions.append(transaction)

        balance = 0
        for transaction in address_transactions:
            if transaction['recipient'] == address:
                balance += transaction['amount']
            elif transaction['sender'] == address:
                balance -= transaction['amount']

        return {
            'addressTransactions': address_transactions,
            'addressBalance': balance
        }
    
    #검증함수
    def chain_is_valid(self, chain):
            validChain  = True

            for i in range(1, len(chain)):
                current_block = chain[i] ## 채우시오 : 현재 체인 i를 이용해서 채우시오
                prev_block = chain[i - 1] #채우시오 : 이전 노드 i를 이용해서 채우시오

                block_hash = self.hash_block(prev_block['hash'],{"transactions": current_block['transactions'], "index": current_block['index']}, current_block['nonce'])
                print(block_hash)
                if block_hash[:4] != '0000': #채우시오 : i가 1이 아니거나 hash값 찾은 hash값 조건 넣기 :
                    validChain = False

                if i != 1 and current_block['previous_block_hash'] != prev_block['hash']: #채우시오 : i가 1이 아니거나 현재 블럭의 previous_hash값과 이전 블럭의 hash값이 같은지 비교:
                    validChain = False

            return validChain



    #hash화 하는 함수
    def hash_function(self, data): 
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    # left,right 노드 받아서 더하고 hash 하는 함수
    def create_merkle_tree_node(self, left, right):
        return self.hash_function(left + right)
    

    #create_merkle_tree
    def create_merkle_tree(self, transactions):
        if len(transactions) == 0:
            return None

        elif len(transactions) == 1: # 제네시스생성 및 tx가 처음부터 한개일때 (coinbase tx만 있을때)
            #채우시오 : 가장 마지막 tx를 trasactions에 추가
            transactions.append(transactions[-1])
            new_level = []
            #for i in range(#채우시오, 채우시오, 채우시오): 0부터 len(tx)까지
            for i in range(0, len(transactions), 2):
                left = transactions[i] #채우시오
                right = transactions[i + 1] #채우시오
                new_level.append(self.create_merkle_tree_node(left, right))
            
            transactions = new_level

            return transactions[0]
        
        else: #두개
            while len(transactions) > 1:
                if len(transactions) % 2 != 0:  #채우시오 : 홀수일 때:
                     transactions.append(transactions[-1]) #채우시오 : 가장 마지막 tx를 trasactions에 추가

                new_level = []
                #for i in range(#채우시오, 채우시오, 채우시오): 0부터 len(tx)까지
                for i in range(0, len(transactions), 2):
                    left = transactions[i] #채우시오 : i를 활용하여 왼쪽 노드
                    right = transactions[i + 1] #채우시오 : i를 활용하여 오른쪽노드
                    new_level.append(self.create_merkle_tree_node(left, right))

                transactions = new_level

            return transactions[0]
    
    def node_address(self):
        node_address = str(uuid4()).replace('-', '')
        return node_address