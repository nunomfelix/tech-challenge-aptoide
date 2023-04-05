import pytest
import json
from challenge import AptoideStore
from pydantic import ValidationError

@pytest.fixture
def test_data():
    with open('./test_data.json') as f:
        data = json.load(f)
    return data

def test_purchase_transaction(test_data):
    
    # Initialize AptoideStore object
    store = AptoideStore(**test_data)

    # Test successful purchase transaction
    tx1 = store.purchase_transaction('app1', 'item1', 'user1')
    print(tx1)
    assert tx1.app_id == 'app1'
    assert tx1.item_id == 'item1'
    assert tx1.currency == '€'
    assert tx1.amount == 1.0
    assert tx1.sender == 'user1'
    assert tx1.receivers == {'store1': 0.25, 'dev1': 0.75}
    assert store.store_balance == 1.25
    assert store.users['dev1'].balance == 0.75
    assert store.users['user1'].balance == 9.0

    # Test failed purchase transaction due to insufficient balance
    tx2 = store.purchase_transaction('app1', 'item2', 'user2')
    assert tx2 is None
    assert store.users['user2'].balance == 0.5

def test_reward_transaction(test_data):
    # Initialize AptoideStore object
    store = AptoideStore(**test_data)
    
    [store.users['user1'].purchases.append({"app_id": "app1", "item_id": "item1", "amount": 1.00}) for _ in range(2)]

    # Test reward transaction with count = 2
    tx1 = store.reward_transaction('user1', 'app1', 1.0)

    assert tx1.tx_type == 'REWARD'
    assert tx1.amount == 0.05
    assert store.store_balance == 0.95
    assert store.users['user1'].balance == 10.05
    
    [store.users['user1'].purchases.append({"app_id": "app1", "item_id": "item1", "amount": 1.00}) for _ in range(9)]
    # Test reward transaction with count = 11
    tx2 = store.reward_transaction('user1', 'app1', 1.0)
    assert tx2.tx_type == 'REWARD'
    assert tx2.amount == 0.10
    assert store.store_balance == 0.85
    assert store.users['user1'].balance == 10.15

    store.users['user1'].purchases = [{"app_id": "app1", "item_id": "item1", "amount": 1.00}]
    # Test reward transaction with count = 1 (should not create a transaction)
    tx3 = store.reward_transaction('user1', 'app1', 1.0)
    assert tx3 is None
    assert store.store_balance == 0.85
    assert store.users['user1'].balance == 10.15
    