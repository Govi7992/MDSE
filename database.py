from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta
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
    """Verify a password against a hashed version"""
    try:
        # Check if the hashed password is bytes or string
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
            
        # Handle both string and bytes input for password
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password
            
        # Use bcrypt to check the password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        # In case of any error, return False for security
        return False

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
    """
    Store risk assessment data
    
    OCL Constraints:
    pre ValidUserID: ObjectId.is_valid(user_id)
    pre RequiredFields: assessment_data->includesAll(Set{'score', 'profile', 'responses'})
    post AssessmentStored: risk_assessments_collection->exists(a | a.user_id = user_id)
    post ModificationLimit: existing <> null implies (existing.created_at.differenceInDays(currentDate()) <= 30)
    """
    try:
        # Pre-condition: ValidUserID
        if not user_id or not ObjectId.is_valid(str(user_id)):
            raise ValueError("Invalid user ID")
            
        # Pre-condition: RequiredFields
        required_fields = ['score', 'profile', 'responses']
        for field in required_fields:
            if field not in assessment_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert to ObjectId if needed
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        assessment_data["user_id"] = user_id_obj
        assessment_data["updated_at"] = datetime.utcnow()
        
        # Check if assessment exists
        existing_assessment = risk_assessments_collection.find_one(
            {"user_id": user_id_obj}
        )
        
        if existing_assessment:
            # Post-condition: ModificationLimit
            created_at = existing_assessment.get("created_at", datetime.utcnow())
            modification_limit = created_at + timedelta(days=30)
            
            if datetime.utcnow() > modification_limit:
                raise ValueError("Cannot modify risk assessment after 30 days of creation")
                
            # Update existing assessment (atomic operation)
            result = risk_assessments_collection.update_one(
                {"user_id": user_id_obj},
                {"$set": assessment_data}
            )
            return existing_assessment["_id"]
        else:
            # Create new assessment
            assessment_data["created_at"] = datetime.utcnow()
            result = risk_assessments_collection.insert_one(assessment_data)
            
            # Post-condition: AssessmentStored verification
            if not result.inserted_id:
                raise RuntimeError("Failed to store assessment")
                
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

def execute_transaction(operations):
    """OCL: AtomicTransactions"""
    transaction_status = 'pending'
    changes = []
    
    try:
        # Begin transaction
        transaction_status = 'in_progress'
        session = client.start_session()
        session.start_transaction()
        
        # Execute operations
        for operation in operations:
            result = operation(session)
            changes.append(result)
            
        # Commit transaction
        session.commit_transaction()
        session.end_session()
        transaction_status = 'completed'
        return changes
    except Exception as e:
        # Rollback transaction
        if transaction_status == 'in_progress':
            try:
                session.abort_transaction()
                session.end_session()
            except:
                pass
        
        transaction_status = 'failed'
        changes = []  # OCL: AtomicTransactions - Clear all changes when transaction fails
        print(f"Transaction failed: {e}")
        raise e
    finally:
        # Log transaction status
        print(f"Transaction completed with status: {transaction_status}")
        
        # OCL: AtomicTransactions - Ensure no changes if transaction failed
        if transaction_status == 'failed':
            assert len(changes) == 0, "Failed transaction should not have changes" 
