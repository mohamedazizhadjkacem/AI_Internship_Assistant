import os
import uuid
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import time
import re
import streamlit as st

# Try to import from config, fallback to environment variables or Streamlit secrets
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    # Try Streamlit secrets first, then environment variables
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    except:
        # If Streamlit secrets fail, try environment variables
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

class SupabaseDB:
    """A class to manage all interactions with the Supabase database."""
    def __init__(self):
        """Initializes the Supabase client."""
        if not all([SUPABASE_URL, SUPABASE_KEY]):
            raise ConnectionError("Supabase URL or Key is not set. Check your config.py, environment variables, or Streamlit secrets.")
        
        try:
            print(f"Initializing Supabase client with URL: {SUPABASE_URL}")
            # Simple initialization without any additional parameters
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Supabase initialization error: {str(e)}")
            raise ConnectionError(f"Failed to initialize Supabase client: {e}") from e

    def sign_up_user(self, email, password, username, telegram_bot_token=None, telegram_chat_id=None):
        """Signs up a new user, creates their profile, and sets up a default subscription."""
        user = None
        try:
            # Validate Telegram Bot Token format
            if telegram_bot_token is not None:
                token_pattern = r"^\d{9,10}:[A-Za-z0-9_-]{35,}$"
                if not re.match(token_pattern, telegram_bot_token):
                    return {"error": "Invalid Telegram Bot Token format."}
            # Validate Telegram Chat ID format
            if telegram_chat_id is not None:
                chat_id_pattern = r"^-?\d+$"
                if not re.match(chat_id_pattern, str(telegram_chat_id)):
                    return {"error": "Invalid Telegram Chat ID format. It should be a number (can be negative for groups)."}

            # 1. Create auth user
            res = self.client.auth.sign_up({"email": email, "password": password})
            user = res.user
            if not user:
                return {"error": "Failed to create authentication user."}

            # 2. Wait for user to exist in auth.users (retry up to 10 times)
            user_exists = False
            for _ in range(10):
                user_check = self.client.auth.admin.get_user_by_id(user.id)
                if user_check and getattr(user_check, 'user', None):
                    user_exists = True
                    break
                time.sleep(0.5)
            if not user_exists:
                return {"error": "User not found in auth.users after sign up. Please try again."}

            # 3. Create profile (add telegram fields)
            profile_data = {
                'id': user.id,
                'username': username,
                'telegram_bot_token': telegram_bot_token,
                'telegram_chat_id': telegram_chat_id
            }
            profile_res = self.client.table('profiles').insert(profile_data).execute()

            if not profile_res.data:
                raise Exception("Failed to create user profile after authentication.")

            # 4. Create a default subscription
            now = datetime.now(timezone.utc)
            subscription_data = {
                'id': user.id,
                'status': 'active',  # Assuming 'free' is a valid subscription_status
                'current_period_start': now.isoformat(),
                'current_period_end': (now + timedelta(days=365*100)).isoformat(), # Effectively never expires
                'cancel_at_period_end': False
            }
            subscription_res = self.client.table('subscriptions').insert(subscription_data).execute()

            if not subscription_res.data:
                raise Exception("Failed to create user subscription.")
            
            return {"success": True, "user": user}

        except Exception as e:
            # Clean up created user if any part of the process fails
            if user and user.id:
                try:
                    user_check = None
                    try:
                        user_check = self.client.auth.admin.get_user_by_id(user.id)
                    except Exception:
                        pass
                    if user_check and getattr(user_check, 'user', None):
                        self.client.auth.admin.delete_user(user.id)
                    else:
                        print(f"WARNING: User {user.id} not found in auth system, nothing to clean up after sign-up error.")
                except Exception as admin_e:
                    print(f"WARNING: Failed to clean up user {user.id} after sign-up error: {admin_e}")

            if 'User already registered' in str(e):
                return {"error": "This email is already registered."}
            if 'subscription_status' in str(e):
                return {"error": f"Database error: Invalid subscription status used. Details: {e}"}
            return {"error": f"An unexpected error occurred during sign-up: {e}"}

    def sign_in_user(self, email, password):
        """Signs in an existing user."""
        try:
            res = self.client.auth.sign_in_with_password({"email": email, "password": password})
            return {"success": True, "session": res.session}
        except Exception as e:
            return {"error": "Invalid login credentials."}

    def get_user_profile(self, user_id=None):
        """Gets the profile of the specified user, or the currently authenticated user if user_id is None."""
        try:
            if user_id is None:
                user_response = self.client.auth.get_user()
                if user_response and user_response.user:
                    user_id = user_response.user.id
                else:
                    return None
            profile_res = self.client.table('profiles').select('*').eq('id', user_id).single().execute()
            return profile_res.data
        except Exception as e:
            return None

    def check_internship_exists(self, user_id: str, job_data: dict) -> dict:
        """Check if an internship already exists for the user using multiple criteria"""
        try:
            application_link = job_data.get('application_link', '')
            job_title = job_data.get('job_title', '')
            company_name = job_data.get('company_name', '')
            
            # Primary check: exact application link match
            if application_link:
                response = self.client.table('internships').select('id').eq('user_id', user_id).eq('application_link', application_link).execute()
                if hasattr(response, 'data') and response.data and len(response.data) > 0:
                    return {'exists': True, 'reason': 'application_link', 'existing_id': response.data[0]['id']}
            
            # Secondary check: same job title and company combination
            if job_title and company_name:
                response = self.client.table('internships').select('id').eq('user_id', user_id).eq('job_title', job_title).eq('company_name', company_name).execute()
                if hasattr(response, 'data') and response.data and len(response.data) > 0:
                    return {'exists': True, 'reason': 'job_company_match', 'existing_id': response.data[0]['id']}
            
            return {'exists': False}
            
        except Exception as e:
            print(f"[ERROR] Failed to check internship existence: {str(e)}")
            return {'exists': False, 'error': str(e)}

    def add_internship(self, user_id: str, job_data: dict):
        """Adds a new internship record for a specific user with duplicate checking."""
        try:
            # First check if this internship already exists
            duplicate_check = self.check_internship_exists(user_id, job_data)
            if duplicate_check.get('exists'):
                reason = duplicate_check.get('reason', 'unknown')
                existing_id = duplicate_check.get('existing_id', 'unknown')
                print(f"[DEBUG] add_internship: Duplicate detected - {reason} (existing ID: {existing_id})")
                return {'error': 'duplicate', 'message': f'Duplicate internship detected ({reason})', 'existing_id': existing_id}
            
            job_data['user_id'] = user_id
            # Temporarily remove notified field until database is updated
            # job_data['notified'] = job_data.get('notified', False)  # Default to not notified
            print(f"[DEBUG] add_internship: Inserting new internship for user {user_id}: {job_data.get('job_title', 'Unknown')} at {job_data.get('company_name', 'Unknown')}")
            
            # Execute the insert
            response = self.client.table('internships').insert(job_data).execute()
            print(f"[DEBUG] add_internship: Raw response type: {type(response)}")
            print(f"[DEBUG] add_internship: Raw response: {response}")
            
            # Check if response has data
            if hasattr(response, 'data') and response.data:
                print(f"[DEBUG] add_internship: Response data length: {len(response.data)}")
                if len(response.data) > 0:
                    print(f"[DEBUG] add_internship: Successfully inserted internship")
                    return {'success': True, 'data': response.data[0], 'is_new': True}
                else:
                    print(f"[DEBUG] add_internship: No data in response")
                    return {'error': 'Failed to insert data - no records returned.'}
            else:
                print(f"[DEBUG] add_internship: No data attribute in response")
                return {'error': 'Failed to insert data - invalid response format.'}
                
        except Exception as e:
            print(f"[DEBUG] add_internship: Exception occurred: {str(e)}")
            if 'duplicate key value violates unique constraint' in str(e):
                return {"error": "duplicate", "message": "You have already saved this internship."}
            return {"error": str(e)}

    def mark_internship_as_notified(self, internship_id: str):
        """Mark an internship as notified to prevent duplicate notifications"""
        try:
            response = self.client.table('internships').update({'notified': True}).eq('id', internship_id).execute()
            return {'success': True}
        except Exception as e:
            print(f"[ERROR] Failed to mark internship as notified: {str(e)}")
            return {'error': str(e)}
    
    def get_unnotified_internships(self, user_id: str):
        """Get all internships that haven't been notified yet"""
        try:
            # First try to get internships where notified is explicitly False
            response = self.client.table('internships').select('*').eq('user_id', user_id).eq('notified', False).execute()
            unnotified = response.data if hasattr(response, 'data') else response
            
            # Also get internships where notified is NULL (existing records before the update)
            response_null = self.client.table('internships').select('*').eq('user_id', user_id).is_('notified', 'null').execute()
            null_notified = response_null.data if hasattr(response_null, 'data') else response_null
            
            # Combine both lists and remove duplicates
            all_unnotified = unnotified + null_notified
            seen_ids = set()
            unique_unnotified = []
            for internship in all_unnotified:
                if internship['id'] not in seen_ids:
                    seen_ids.add(internship['id'])
                    unique_unnotified.append(internship)
            
            print(f"[DEBUG] Found {len(unique_unnotified)} unnotified internships (explicitly false: {len(unnotified)}, null: {len(null_notified)})")
            return unique_unnotified
            
        except Exception as e:
            print(f"[ERROR] Failed to get unnotified internships: {str(e)}")
            return []
    
    def initialize_notification_field(self, user_id: str):
        """Initialize the notified field for existing internships (migration helper)"""
        try:
            # Update all existing internships for this user that have NULL notified field to True
            # (assuming they were already processed before the notification system)
            response = self.client.table('internships').update({'notified': True}).eq('user_id', user_id).is_('notified', 'null').execute()
            
            updated_count = len(response.data) if hasattr(response, 'data') and response.data else 0
            print(f"[INFO] Initialized notification field for {updated_count} existing internships for user {user_id}")
            return {'success': True, 'updated_count': updated_count}
        except Exception as e:
            print(f"[ERROR] Failed to initialize notification field: {str(e)}")
            return {'error': str(e)}

    def get_internships_by_user(self, user_id: str, limit=None, offset=None):
        """Fetches internship records for a specific user with optional pagination."""
        if not user_id:
            return []
            
        try:
            # If specific pagination is requested, use it
            if limit is not None and offset is not None:
                query = self.client.table('internships').select('*').eq('user_id', user_id)
                query = query.limit(limit).offset(offset)
                response = query.execute()
                data = response.data if hasattr(response, 'data') else response
            else:
                # Fetch all records using pagination to overcome Supabase 1000 record limit
                all_internships = []
                batch_size = 1000
                current_offset = 0
                
                while True:
                    query = self.client.table('internships').select('*').eq('user_id', user_id)
                    query = query.limit(batch_size).offset(current_offset)
                    response = query.execute()
                    
                    batch_data = response.data if hasattr(response, 'data') else response
                    
                    if not batch_data or len(batch_data) == 0:
                        # No more records
                        break
                    
                    all_internships.extend(batch_data)
                    
                    # If we got less than the batch size, we've reached the end
                    if len(batch_data) < batch_size:
                        break
                    
                    current_offset += batch_size
                
                data = all_internships
            
            if not data:
                return []
                
            internships = data if isinstance(data, list) else []
            
            # Sort internships by status priority (new -> applied -> rejected) and then by date
            try:
                sorted_internships = sorted(
                    internships,
                    key=lambda x: (
                        # Status priority (0: new, 1: applied, 2: rejected)
                        {'new': 0, 'applied': 1, 'rejected': 2}.get(x.get('status', 'new'), 3),
                        # Reverse date order (newest first)
                        -int(datetime.fromisoformat(x.get('created_at', '').replace('Z', '+00:00')).timestamp() if x.get('created_at') else 0)
                    )
                )
                return sorted_internships
            except Exception:
                # If sorting fails, return unsorted internships
                return internships
        except Exception as e:
            raise Exception(f"Failed to fetch internships: {str(e)}")

    def get_internships_count(self, user_id: str):
        """Get the total count of internships for a user (for pagination)."""
        if not user_id:
            return 0
        try:
            response = self.client.table('internships').select('id', count='exact').eq('user_id', user_id).execute()
            return response.count if hasattr(response, 'count') else len(response.data or [])
        except Exception as e:
            print(f"Error getting internships count: {e}")
            return 0

    def update_internship_status(self, user_id: str, internship_id: int, new_status: str):
        """Updates the status of a specific internship for a user."""
        try:
            # Validate status
            if new_status not in ['new', 'applied', 'rejected']:
                raise ValueError(f"Invalid status: {new_status}")

            # Ensure internship_id is an integer
            internship_id = int(internship_id)
            
            # First verify the internship exists and belongs to the user
            verify = self.client.table('internships').select('id').match({
                'id': internship_id,
                'user_id': user_id
            }).execute()
            
            if not verify.data or len(verify.data) == 0:
                raise ValueError(f"Internship not found or access denied")
            
            # Update the status
            response = self.client.table('internships').update({
                'status': new_status
            }).match({
                'id': internship_id,
                'user_id': user_id
            }).execute()
            
            if not response.data or len(response.data) == 0:
                return False
                
            return True
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    def delete_internship(self, user_id: str, internship_id: int):
        """Deletes a specific internship for a user."""
        try:
            # Convert internship_id to integer if it's a string
            if isinstance(internship_id, str):
                internship_id = int(internship_id)
                
            response = self.client.table('internships').delete().match({
                'id': internship_id,
                'user_id': user_id
            }).execute()
            
            # Debug prints
            print(f"Delete response: {response}")
            if hasattr(response, 'data'):
                print(f"Response data: {response.data}")
                if len(response.data) > 0:
                    return True
            
            return False
        except Exception as e:
            print(f"Error deleting internship: {str(e)}")  # Debug print
            return False

    def get_all_internship_links(self, user_id: str):
        """Fetches all application_link URLs for a specific user to prevent duplicates."""
        try:
            data, count = self.client.table('internships').select('application_link').eq('user_id', user_id).execute()
            return {item['application_link'] for item in data[1]} if data and len(data[1]) > 0 else set()
        except Exception:
            return set()

    def update_telegram_config(self, user_id, telegram_bot_token, telegram_chat_id):
        """Update Telegram Bot Token and Chat ID for a user."""
        try:
            update_data = {
                'telegram_bot_token': telegram_bot_token,
                'telegram_chat_id': telegram_chat_id
            }
            res = self.client.table('profiles').update(update_data).eq('id', user_id).execute()
            return hasattr(res, 'data') and res.data is not None
        except Exception as e:
            print(f"Error updating Telegram config: {e}")
            return False