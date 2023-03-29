import json
import sys 

def main():
    data = json.load(open('./data.json'))
    store = AptoideStore(data['store_id'], data['store_balance'], data['store_comission'],\
    data['apps'],data['items'],data['users'])

    while True:
        _input = input()
        _input_split = _input.split(" ")
        
        if(len(_input_split) != 3):
            print("Invalid Input: Expected three inputs separated by spaces")
        else:
            app, item, user = _input_split
            store.purchase_transaction(app, item, user)

class AptoideStore():
    def __init__(self, id: str, balance: float, comission:float =0.25, apps:list=[], items:list=[], users:list=[]) -> None:
        self.id = id
        self.balance = balance
        self.comission = comission
        self.apps = {app['id']: App(app['id'],app['dev_id'],[item for item in items if item['app_id'] == app['id']], app['comission']) for app in apps}
        self.users = {user['id']: User(user['id'], user['balance']) for user in users}
        self.transactions = []

    def purchase_transaction(self, app_id: str, item: str, sender: str) -> 'Transaction':
        try:
            if app_id not in self.apps or \
                item not in self.apps[app_id].items or \
                sender not in self.users:
                print(f"ERROR: Invalid AppId/Item/Sender", file=sys.stderr)
                return
            
            app = self.apps[app_id]
            item = app.items[item]
            sender = self.users[sender]
            amount = item['price']
            
            if sender.balance < amount:
                print(f"ERROR: User {sender.user_id} doesn't have enough balance to make this purchase")
                return
            
            if self.comission + app.comission != 1:
                print(f"ERROR: The comissions between the Store and the App don't add up to 100%")
                return
            
            store_share=round(self.comission * amount, 2)
            dev_share=round(app.comission * amount, 2)

            sender.balance-=amount
            self.balance+=store_share
            self.users[app.dev_id].balance+=dev_share
            
            receivers={
                self.users[app.dev_id].user_id: dev_share,
                self.id: store_share
            }
            
            balances={
                sender.user_id: sender.balance,
                self.users[app.dev_id].user_id: self.users[app.dev_id].balance,
                self.id: self.balance
            }
            
            tx_data=['PURCHASE', len(self.transactions)+1, app_id, item['id'], item['currency'], item['price'], sender.user_id, receivers]
            transaction = Transaction(tx_data)
            self.transactions.append(transaction)
            self.users[sender.user_id].purchases.append({"app_id": app_id, "item_id": item['id'], "amount": amount})
            print(transaction, '\n', f"BALANCE => {'; '.join([f'{user}: €{amount:.2f}' for user, amount in balances.items()])}")
            
            self.reward_transaction(sender.user_id, app_id, amount)
            return transaction
        
        except Exception as err: 
            raise err
    
    def reward_transaction(self, user_id: str, app_id: str, amount: float) -> 'Transaction':
        count = len([purchase for purchase in self.users[user_id].purchases if purchase['app_id'] == app_id])
        reward_percent = 0.05 if 2 <= count <= 10 else 0.10 if count >= 11 else None
        if(reward_percent is None):
            return
        reward_amount = round(amount * reward_percent, 2)
        self.users[user_id].balance+=reward_amount
        self.balance-=reward_amount
        tx_data=['REWARD', len(self.transactions)+1,'', '', '€', reward_amount, self.id, {user_id: reward_amount}]
        tx = Transaction(tx_data)
        self.transactions.append(tx)
        
        balances={
            user_id: self.users[user_id].balance,
            self.id: self.balance
        }
        print("#########\n",tx, '\n', f"BALANCE => {'; '.join([f'{user}: €{amount:.2f}' for user, amount in balances.items()])}")
        return tx
    
class User():
    def __init__(self, user_id: list, balance: float) -> None:
        self.user_id = user_id
        self.balance = balance
        self.purchases = []
        
    def __str__(self) -> str:
        return f"User(id={self.user_id}, balance={self.balance})"
    
class App():
    def __init__(self, id: str, dev_id: str, items: list, comission:float=0.75) -> None:
        self.id = id
        self.dev_id = dev_id
        self.items = {item['id']: item for item in items}
        self.comission = comission
        
    def __str__(self) -> str:
        return f"App(id={self.id}, dev_id={self.dev_id}, items={self.items}, comission={self.comission})"

class Transaction():
    def __init__(self, tx_data: list) -> 'Transaction':
        self.type, self.id, self.app_id, self.item_id, self.currency, self.amount, self.sender, self.receivers = tx_data
        
    def __str__(self) -> str:
        if self.type == 'REWARD':
            return f"{self.type} TRANSACTION => id: {self.id}; amount: {self.currency}{self.amount:.2f}; sender: {self.sender}; receivers: {'; '.join([f'{receiver}: {self.currency}{value}' for receiver, value in self.receivers.items()])}"
        else:
            return f"{self.type} TRANSACTION => id: {self.id}; app: {self.app_id}; item: {self.item_id}; amount: {self.currency}{self.amount:.2f}; sender: {self.sender}; receivers: {'; '.join([f'{receiver}: {self.currency}{value}' for receiver, value in self.receivers.items()])}"

if __name__ == "__main__":
    main()
    