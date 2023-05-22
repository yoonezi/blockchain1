from flask import Flask, request, jsonify, render_template, send_from_directory

from blockchain import Blockchain
from uuid import uuid4
import requests
import sys
node_address = str(uuid4()).replace('-', '') 


app = Flask(__name__)
bitcoin = Blockchain()



@app.route('/blockchain', methods=['GET']) #전체 블록을 보여줌
def get_blockchain():
    return jsonify(bitcoin.__dict__)


@app.route('/transaction', methods=['POST']) # pending_transactions에 transaction 추가
def create_transaction():
    new_transaction = request.get_json()
    block_index = bitcoin.add_transaction_to_pending_transactions(new_transaction)
    return jsonify({'note': f'Transaction will be added in block {block_index}.'})




@app.route('/mine', methods=['GET']) # 작업증명
def mine():
    last_block = bitcoin.get_last_block()
    previous_block_hash = last_block['hash']
    merkle_root = bitcoin.create_merkle_tree([bitcoin.hash_function(str(tx)) for tx in bitcoin.pending_transactions])
    current_block_data = {
        'merkle_root': merkle_root,
        'index': last_block['index'] + 1
    }
    bitcoin.create_new_transaction(6.25, "00", node_address)
    nonce = bitcoin.proof_of_work(previous_block_hash, current_block_data)
    block_hash = bitcoin.hash_block(previous_block_hash, current_block_data, nonce)
    new_block = bitcoin.create_new_block(nonce, previous_block_hash, block_hash, merkle_root)

    request_promises = []

    for network_node_url in bitcoin.network_nodes:
        request_options = {
            'newBlock': new_block
        }
        res = requests.post(network_node_url + '/receive-new-block', json=request_options)
        request_promises.append(res)

    responses = [rp.json() for rp in request_promises]

    request_options = {
        'amount': 6.25,
        'sender': "00",
        'recipient': node_address
    }
    requests.post(bitcoin.current_node_url + '/transaction/broadcast', json=request_options)

    return jsonify({
        'note': "New block mined successfully",
        'block': new_block
    })

@app.route('/register-and-broadcast-node', methods=['POST'])
def register_and_broadcast_node():
    new_node_url = request.json['newNodeUrl']
    if new_node_url not in bitcoin.network_nodes:
        bitcoin.network_nodes.append(new_node_url)

    reg_nodes_promises = []
    for network_node_url in bitcoin.network_nodes:
        response = requests.post(f"{network_node_url}/register-node", json={'newNodeUrl': new_node_url})
        reg_nodes_promises.append(response)

    for response in reg_nodes_promises:
        if response.status_code == 200:
            requests.post(f"{new_node_url}/register-nodes-bulk", json={'allNetworkNodes': bitcoin.network_nodes + [bitcoin.current_node_url]})

    return jsonify({'note': 'New node registered with network successfully.'})


@app.route('/register-node', methods=['POST'])
def register_node():
    new_node_url = request.json['newNodeUrl']
    node_not_already_present = new_node_url not in bitcoin.network_nodes
    not_current_node = bitcoin.current_node_url != new_node_url
    if node_not_already_present and not_current_node:
        bitcoin.network_nodes.append(new_node_url)
    return jsonify({'note': 'New node registered successfully.'})


@app.route('/register-nodes-bulk', methods=['POST'])
def register_nodes_bulk():
    all_network_nodes = request.json['allNetworkNodes']
    for network_node_url in all_network_nodes:
        node_not_already_present = network_node_url not in bitcoin.network_nodes
        not_current_node = bitcoin.current_node_url != network_node_url
        if node_not_already_present and not_current_node:
            bitcoin.network_nodes.append(network_node_url)

    return jsonify({'note': 'Bulk registration successful.'}) 

@app.route('/transaction/broadcast', methods=['POST'])
def broadcast_transaction():
    new_transaction = bitcoin.create_new_transaction(
        request.json['amount'],
        request.json['sender'],
        request.json['recipient']
    )
    bitcoin.add_transaction_to_pending_transactions(new_transaction)

    request_promises = []
    for network_node_url in bitcoin.network_nodes:
        request_options = {
            'url': network_node_url + '/transaction',
            'json': new_transaction
        }
        request_promises.append(requests.post(**request_options))

    for response in request_promises:
        response.raise_for_status()

    return jsonify({'note': 'Transaction created and broadcast successfully.'})

@app.route('/receive-new-block', methods=['POST'])
def receive_new_block():
    new_block = request.json['newBlock']
    last_block = bitcoin.get_last_block()
    correct_hash = last_block['hash'] == new_block['previous_block_hash']
    correct_index = last_block['index'] + 1 == new_block['index']

    if correct_hash and correct_index:
        bitcoin.chain.append(new_block)
        bitcoin.pending_transactions = []
        return jsonify({
            'note': 'New block received and accepted',
            'newBlock': new_block
        })
    else:
        return jsonify({
            'note': 'New block rejected.',
            'newBlock': new_block
        })

@app.route('/consensus', methods=['GET'])
def consensus():
    request_promises = []
    for network_node_url in bitcoin.network_nodes: #연결된 모든 노드의 체인을 가져오는 과정
        request_promises.append(requests.get(network_node_url + '/blockchain'))

    blockchains = [rp.json() for rp in request_promises]
    
    #현재 노드의 데이터 변수에 저장
    current_chain_length = len(bitcoin.chain)
    max_chain_length = current_chain_length
    new_longest_chain = None
    new_pending_transactions = None

    for blockchain in blockchains: #전체 노드의 블록 순회
        if len(blockchain['chain']) > max_chain_length: # 현재 노드의 블록보다 더 큰 노드를 찾았을 때
            #채우시오 :  #max_chain_length에 찾은 노드의 체인 길이 저장
            #채우시오 :  #가장 긴 노드를 현재 노드의 체인에서 새로운 노드의 체인으로 변경
            #채우시오 :  #마찬가지로 pending_transactions도 변경
            max_chain_length = len(blockchain['chain'])
            new_longest_chain = blockchain['chain']
            new_pending_transactions = blockchain['pending_transactions']

    if not new_longest_chain or (new_longest_chain and not bitcoin.chain_is_valid(new_longest_chain)): #값이 없거나 값이 있는데 체인 검증 결과가 flase 이면 체인은 교체되지 않음
        return jsonify({
            'note': 'Current chain has not been replaced.',
            'chain': bitcoin.chain
        })

    else: #아닐경우 교체됨
        bitcoin.chain = new_longest_chain
        bitcoin.pending_transactions = new_pending_transactions
        return jsonify({
            'note': 'This chain has been replaced.',
            'chain': bitcoin.chain
        })

@app.route('/block/<block_hash>')
def block(block_hash):
    block_data = bitcoin.get_block(block_hash)
    return jsonify({'block': block_data})

@app.route('/transaction/<transaction_id>')
def transaction(transaction_id):
    transaction_data = bitcoin.get_transaction(transaction_id)
    return jsonify({
        'transaction': transaction_data['transaction'],
        'block': transaction_data['block']
    })

@app.route('/address/<address>')
def address(address):
    address_data = bitcoin.get_address_data(address)
    return jsonify({'addressData': address_data})

@app.route('/block-explorer')
def block_explorer():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/merkle-tree', methods=['POST'])
def generate_merkle_tree():
    transactions = bitcoin.pending_transactions

    if not transactions or not isinstance(transactions, list):
        return jsonify({'error': 'Invalid transactions'}), 400

    transaction_hashes = [bitcoin.hash_function(str(tx)) for tx in transactions]
    merkle_root = bitcoin.create_merkle_tree(transaction_hashes)

    return jsonify({'merkle_root': merkle_root}), 200


if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5000  # 기본 포트 번호를 설정하십시오.
    
    if len(sys.argv) > 2:
        current_node_url = sys.argv[2]
    else:
        current_node_url = f"http://localhost:{port}"
    
    bitcoin = Blockchain(current_node_url)  # 현재 노드 URL 전달
    app.run(host="0.0.0.0", port=port)