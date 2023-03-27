import pytest
import json
import sys
from io import StringIO

from challenge import AptoideStore

@pytest.fixture
def test_data():
    with open('./test_data.json') as f:
        data = json.load(f)
    return data

def test_purchase_transaction(test_data, monkeypatch):
    # Initialize AptoideStore object
    store = AptoideStore(test_data['store_id'], test_data['store_balance'], test_data['store_comission'],
                         test_data['apps'], test_data['items'], test_data['users'])

    error_output = StringIO()
    monkeypatch.setattr(sys, 'stderr', error_output)
    # Test failed purchase transaction due to invalid app_id
    store.purchase_transaction('invalid_app_id', 'item1', 'user1')
    assert 'ERROR: Invalid AppId/Item/Sender' in error_output.getvalue()
    
    # Test failed purchase transaction due to invalid item_id
    store.purchase_transaction('app1', 'invalid_item_id', 'user1')
    assert 'ERROR: Invalid AppId/Item/Sender' in error_output.getvalue()
    
    # Test failed purchase transaction due to invalid user_id
    store.purchase_transaction('app1', 'item1', 'invalid_user_id')
    assert 'ERROR: Invalid AppId/Item/Sender' in error_output.getvalue()
    
    # Test successful purchase transaction
    tx1 = store.purchase_transaction('app1', 'item1', 'user1')
    assert tx1.type == 'PURCHASE'
    assert tx1.app_id == 'app1'
    assert tx1.item_id == 'item1'
    assert tx1.currency == '€'
    assert tx1.amount == 1.0
    assert tx1.sender == 'user1'
    assert tx1.receivers == {'store1': 0.2, 'dev1': 0.8}
    assert store.balance == 1.20
    assert store.users['dev1'].balance == 0.80
    assert store.users['user1'].balance == 9.0

    # Test failed purchase transaction due to insufficient balance
    tx2 = store.purchase_transaction('app1', 'item2', 'user2')
    assert tx2 is None
    assert store.users['user2'].balance == 0.5

def test_reward_transaction(test_data):
    # Initialize AptoideStore object
    store = AptoideStore(test_data['store_id'], test_data['store_balance'], test_data['store_comission'],
                         test_data['apps'], test_data['items'], test_data['users'])
    
    [store.users['user1'].purchases.append({"app_id": "app1", "item_id": "item1", "amount": 1.00}) for _ in range(2)]
    # Test reward transaction with count = 2
    tx1 = store.reward_transaction('user1', 'app1', 1.0)

    assert tx1.type == 'REWARD'
    assert tx1.amount == 0.05
    assert store.balance == 0.95
    assert store.users['user1'].balance == 10.05
    
    [store.users['user1'].purchases.append({"app_id": "app1", "item_id": "item1", "amount": 1.00}) for _ in range(9)]
    # Test reward transaction with count = 11
    tx2 = store.reward_transaction('user1', 'app1', 1.0)
    assert tx2.type == 'REWARD'
    assert tx2.amount == 0.10
    assert store.balance == 0.85
    assert store.users['user1'].balance == 10.15

    store.users['user1'].purchases = [{"app_id": "app1", "item_id": "item1", "amount": 1.00}]
    # Test reward transaction with count = 1 (should not create a transaction)
    tx3 = store.reward_transaction('user1', 'app1', 1.0)
    assert tx3 is None
    assert store.balance == 0.85
    assert store.users['user1'].balance == 10.15