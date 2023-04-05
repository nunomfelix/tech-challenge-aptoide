import json
import sys
from typing import List, Dict, Optional
from pydantic import BaseModel, ValidationError, validator

class TransactionInput(BaseModel):
    app_id: str 
    item_id: str
    user_id: str
    
class Transaction(BaseModel):
    tx_type: str
    id: int
    app_id: str
    item_id: str
    currency: str
    amount: float
    sender: str
    receivers: dict

    def __str__(self) -> str:
        if self.tx_type == 'REWARD':
            return f"{self.tx_type} TRANSACTION => id: {self.id}; amount: {self.currency}{self.amount:.2f}; sender: {self.sender}; receivers: {'; '.join([f'{receiver}: {self.currency}{value}' for receiver, value in self.receivers.items()])}"
        else:
            return f"{self.tx_type} TRANSACTION => id: {self.id}; app: {self.app_id}; item: {self.item_id}; amount: {self.currency}{self.amount:.2f}; sender: {self.sender}; receivers: {'; '.join([f'{receiver}: {self.currency}{value}' for receiver, value in self.receivers.items()])}"

class User(BaseModel):
    id: str
    balance: float
    purchases: List[dict] = []

    def __str__(self) -> str:
        return f"User(id={self.id}, balance={self.balance})"

class App(BaseModel):
    id: str
    dev_id: str
    items: Dict[str, dict]
    comission: float = 0.75
    
    @validator('items', pre=True)
    def instantiate_items(cls, items):
        return {item['id']: item for item in items}

    def __str__(self) -> str:
        return f"App(id={self.id}, dev_id={self.dev_id}, items={self.items}, comission={self.comission})"

class AptoideStore(BaseModel):
    store_id: str
    store_balance: float
    comission: float = 0.25
    apps: Dict[str, App]
    users: Dict[str, User]
    transactions: Optional[List[Transaction]] = []
    
    @validator('apps', pre=True)
    def instantiate_apps(cls, apps):
        return {app['id']: App(**app) for app in apps}

    @validator('users', pre=True)
    def instantiate_users(cls, users):
        return {user['id']: User(**user) for user in users}

    def purchase_transaction(self, app_id: str, item_id: str, sender_id: str) -> 'Transaction':
        try:
            if app_id not in self.apps:
                print(f"ERROR: Invalid AppId", file=sys.stderr)
                return None

            if sender_id not in self.users:
                print(f"ERROR: Invalid SenderId", file=sys.stderr)
                return None
            
            if item_id not in self.apps[app_id].items:
                print(f"ERROR: Invalid Item", file=sys.stderr)
                return None

            app = self.apps[app_id]
            item = app.items[item_id]
            sender = self.users[sender_id]
            amount = item['price']

            if sender.balance < amount:
                print(f"ERROR: User {sender.id} doesn't have enough balance to make this purchase")
                return None

            if self.comission + app.comission != 1:
                print(f"ERROR: The comissions between the Store and the App don't add up to 100%")
                return None

            store_share = round(self.comission * amount, 2)
            dev_share = round(app.comission * amount, 2)

            sender.balance -= amount
            self.store_balance += store_share
            self.users[app.dev_id].balance += dev_share

            receivers = {
                self.users[app.dev_id].id: dev_share,
                self.store_id: store_share
            }

            balances = {
                sender.id: sender.balance,
                self.users[app.dev_id].id: self.users[app.dev_id].balance,
                self.store_id: self.store_balance
            }

            transaction = Transaction(
                tx_type='PURCHASE',
                id=len(self.transactions)+1,
                app_id=app_id,
                item_id=item_id,
                currency=item['currency'],
                amount=amount,
                sender=sender.id,
                receivers=receivers
            )
            self.transactions.append(transaction)
            sender.purchases.append({"app_id": app_id, "item_id": item_id, "amount": amount})
            print(transaction, '\n', f"BALANCE => {'; '.join([f'{user}: €{amount:.2f}' for user, amount in balances.items()])}")

            self.reward_transaction(sender.id, app_id, amount)
            return transaction

        except Exception as err:
            raise err

    def reward_transaction(self, user_id: str, app_id: str, amount: float) -> 'Transaction':
        count = len([purchase for purchase in self.users[user_id].purchases if purchase['app_id'] == app_id])
        reward_percent = 0.05 if 2 <= count <= 10 else 0.10 if count >= 11 else None
        if reward_percent is None:
            return

        reward_amount = round(amount * reward_percent, 2)
        self.users[user_id].balance += reward_amount
        self.store_balance -= reward_amount

        transaction = Transaction(
            tx_type='REWARD',
            id=len(self.transactions) + 1,
            app_id='',
            item_id='',
            currency='€',
            amount=reward_amount,
            sender=self.store_id,
            receivers={user_id: reward_amount}
        )
        self.transactions.append(transaction)

        balances = {
            user_id: self.users[user_id].balance,
            self.store_id: self.store_balance
        }
        
        print("#########\n", transaction, '\n', f"BALANCE => {'; '.join([f'{user}: €{amount:.2f}' for user, amount in balances.items()])}")
        return transaction 
    
def main():
    data = json.load(open('./data.json'))
    store = AptoideStore(**data)

    while True:
        _input = input()
        _input_split = _input.split(" ")

        try:
            transaction_input = TransactionInput(app_id=_input_split[0], item_id=_input_split[1], user_id=_input_split[2])
            store.purchase_transaction(transaction_input.app_id, transaction_input.item_id, transaction_input.user_id)
        
        except IndexError:
            print("Invalid Input: Expected three inputs separated by spaces")
            
        except ValidationError as e:
            print(f"Invalid Input: {e}")

if __name__ == "__main__":
    main()
