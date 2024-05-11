from datetime import datetime 
class License:
    def __init__(self, name: str, email: str, license: str, max_device: int, created_date: str, expired_date: str, id: int = 0, logged_in_device : int = 0):
        self.id = id
        self.name = name
        self.email = email
        self.license = license
        self.max_device = max_device
        self.logged_in_device = logged_in_device
        self.created_date = created_date
        self.expired_date = expired_date

    def maxDeviceReached(self):
        return (self.max_device <= self.logged_in_device)
    
    def isExpired(self):
        current_time = datetime.now()
        
        return current_time > self.expired_date 