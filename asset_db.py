from typing import Dict, Optional
from datetime import datetime

class AssetDB:
    def __init__(self):
        self.user_data = {} 
        self.asset_data = {}
        
    def fetch_userdata(self, user_id: str) -> Optional[Dict]:
        return self.user_data.get(user_id)
            
    def fetch_riskprofile(self, user_id: str) -> Optional[Dict]:
        user_data = self.user_data.get(user_id, {})
        return user_data.get('risk_profile')
            
    def fetch_portfolio(self, user_id: str) -> Optional[Dict]:
        user_data = self.user_data.get(user_id, {})
        return user_data.get('portfolio')
            
    def update_portfolio(self, user_id: str, portfolio_data: Dict) -> bool:
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['portfolio'] = portfolio_data
        return True
            
    def fetch_assetdata(self, asset_id: str) -> Optional[Dict]:
        return self.asset_data.get(asset_id)
        
    def update_assetdata(self, asset_id: str, asset_data: Dict) -> bool:
        self.asset_data[asset_id] = asset_data
        return True 
