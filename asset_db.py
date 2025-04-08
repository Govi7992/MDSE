from typing import Dict, Optional, List, Set
from datetime import datetime

class AssetDB:
    def __init__(self):
        """Initialize AssetDB with in-memory storage"""
        self.user_data = {}  
        self.asset_data = {} 
        self.valid_risk_profiles = {'conservative', 'moderate_conservative', 'moderate', 'moderate_aggressive', 'aggressive'}
        
    def fetch_userdata(self, user_id: str) -> Optional[Dict]:
        """Fetch user data from in-memory storage"""
        return self.user_data.get(user_id)
            
    def fetch_riskprofile(self, user_id: str) -> Optional[str]:
        """
        Fetch user's risk profile from in-memory storage.
        Post-condition: If result is not null, it must be a valid risk profile
        """
        user_data = self.user_data.get(user_id, {})
        risk_profile = user_data.get('risk_profile')

        if risk_profile is not None and risk_profile not in self.valid_risk_profiles:
            raise ValueError(f"Invalid risk profile: {risk_profile}. Must be one of {self.valid_risk_profiles}")
            
        return risk_profile
            
    def fetch_portfolio(self, user_id: str) -> Optional[Dict]:
        """Fetch user's portfolio data from in-memory storage"""
        user_data = self.user_data.get(user_id, {})
        return user_data.get('portfolio')
            
    def update_userdata(self, user_id: str, field: str, value) -> bool:
        """Update a specific field in user data"""
        try:
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
                
            self.user_data[user_id][field] = value

            if field == 'risk_profile' and value not in self.valid_risk_profiles:
                raise ValueError(f"Invalid risk profile: {value}. Must be one of {self.valid_risk_profiles}")
                
            return True
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False
            
    def update_portfolio(self, user_id: str, portfolio_data: Dict) -> bool:
        """
        Update user's portfolio data in memory
        Pre-condition: user_id must exist in user_data
        Post-condition: portfolio_data must be stored in user_data[user_id]['portfolio']
        """
        try:
            if user_id not in self.user_data:
                self.user_data[user_id] = {}

            if not isinstance(portfolio_data, dict):
                raise ValueError("Portfolio data must be a dictionary")

            self.user_data[user_id]['portfolio'] = portfolio_data
            self.user_data[user_id]['last_updated'] = datetime.now()
            
            return True
        
        except Exception as e:
            print(f"Error updating portfolio: {e}")
            return False
            
    def fetch_assetdata(self, asset_id: str) -> Optional[Dict]:
        """Fetch asset data from memory"""
        return self.asset_data.get(asset_id)
        
    def update_assetdata(self, asset_id: str, asset_data: Dict) -> bool:
        """Update asset data in memory"""
        self.asset_data[asset_id] = asset_data
        return True 
