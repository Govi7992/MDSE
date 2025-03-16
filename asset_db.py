from typing import Dict, Optional
from datetime import datetime

class AssetDB:
    def __init__(self):
        """Initialize AssetDB with in-memory storage"""
        self.user_data = {}  # In-memory user data store
        self.asset_data = {}  # In-memory asset data store
        
    def fetch_userdata(self, user_id: str) -> Optional[Dict]:
        """Fetch user data from in-memory storage"""
        return self.user_data.get(user_id)
            
    def fetch_riskprofile(self, user_id: str) -> Optional[Dict]:
        """Fetch user's risk profile from in-memory storage"""
        user_data = self.user_data.get(user_id, {})
        return user_data.get('risk_profile')
            
    def fetch_portfolio(self, user_id: str) -> Optional[Dict]:
        """Fetch user's portfolio data from in-memory storage"""
        user_data = self.user_data.get(user_id, {})
        return user_data.get('portfolio')
            
    def update_portfolio(self, user_id: str, portfolio_data: Dict) -> bool:
        """Update user's portfolio data in memory"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['portfolio'] = portfolio_data
        return True
            
    def fetch_assetdata(self, asset_id: str) -> Optional[Dict]:
        """Fetch asset data from memory"""
        return self.asset_data.get(asset_id)
        
    def update_assetdata(self, asset_id: str, asset_data: Dict) -> bool:
        """Update asset data in memory"""
        self.asset_data[asset_id] = asset_data
        return True 
