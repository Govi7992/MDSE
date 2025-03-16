from pymongo import MongoClient
import bcrypt
from datetime import datetime
from bson import ObjectId

uri = "mongodb+srv://deshmukhanna105:yMO52hfsY6Wf7ize@mbse.knpxy.mongodb.net/?retryWrites=true&w=majority&appName=MBSE"
client = MongoClient(uri)
db = client["MBSE"]
users_collection = db["users"]
risk_assessments_collection = db["risk_assessments"]
recommendations_collection = db["recommendations"]

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_or_update_user(user_data):
    try:
        existing_user = get_user_by_email(user_data["email"])
        if existing_user:
            # Update existing user
            user_data["updated_at"] = datetime.utcnow()
            if "password" in user_data:
                user_data["password"] = hash_password(user_data["password"]).decode('utf-8')
            users_collection.update_one(
                {"_id": existing_user["_id"]},
                {"$set": user_data}
            )
            return existing_user["_id"]
        else:
            # Create new user
            if "password" in user_data:
                user_data["password"] = hash_password(user_data["password"]).decode('utf-8')
            user_data["account_creation_date"] = datetime.utcnow()
            result = users_collection.insert_one(user_data)
            return result.inserted_id
    except Exception as e:
        print(f"Error creating/updating user: {e}")
        return None

def get_user_by_email(email):
    return users_collection.find_one({"email": email})

def get_user_by_id(user_id):
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None

def has_risk_assessment(user_id):
    try:
        assessment = risk_assessments_collection.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("created_at", -1)]
        )
        return assessment is not None
    except:
        return False

def has_recommendations(user_id):
    try:
        recommendations = recommendations_collection.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("created_at", -1)]
        )
        return recommendations is not None
    except:
        return False

def update_user_profile(user_id, profile_data):
    try:
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": profile_data}
        )
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and verify_password(password, user["password"]):
        return True
    return False

def store_risk_assessment(user_id, assessment_data):
    try:
        assessment_data["user_id"] = ObjectId(user_id)
        assessment_data["updated_at"] = datetime.utcnow()
        
        # Check if assessment exists
        existing_assessment = risk_assessments_collection.find_one(
            {"user_id": ObjectId(user_id)}
        )
        
        if existing_assessment:
            # Update existing assessment
            result = risk_assessments_collection.update_one(
                {"user_id": ObjectId(user_id)},
                {"$set": assessment_data}
            )
            return existing_assessment["_id"]
        else:
            # Create new assessment
            assessment_data["created_at"] = datetime.utcnow()
            result = risk_assessments_collection.insert_one(assessment_data)
            return result.inserted_id
    except Exception as e:
        print(f"Error storing risk assessment: {e}")
        return None

def get_user_risk_assessment(user_id):
    try:
        return risk_assessments_collection.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("created_at", -1)]
        )
    except:
        return None

def store_recommendations(user_id, recommendations_data):
    try:
        recommendations_data["user_id"] = ObjectId(user_id)
        recommendations_data["created_at"] = datetime.utcnow()
        result = recommendations_collection.insert_one(recommendations_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error storing recommendations: {e}")
        return None

def get_user_recommendations(user_id):
    try:
        return recommendations_collection.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("created_at", -1)]
        )
    except:
        return None

def update_user_details(user_id, user_details):
    try:
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "name": user_details.get("name"),
                "phone_number": user_details.get("phone_number"),
                "date_of_birth": user_details.get("date_of_birth"),
                "gender": user_details.get("gender"),
                "marital_status": user_details.get("marital_status"),
                "annual_income": user_details.get("annual_income"),
                "financial_literacy_level": user_details.get("financial_literacy_level"),
                "preferred_notification_method": user_details.get("preferred_notification_method", "Email"),
                "updated_at": datetime.utcnow()
            }}
        )
        return True
    except Exception as e:
        print(f"Error updating user details: {e}")
        return False 