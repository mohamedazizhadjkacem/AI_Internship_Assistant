import os
import uuid
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import time
import re

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL, SUPABASE_KEY = None, None

class SupabaseDB:
    """A class to manage all interactions with the Supabase database."""
    def __init__(self):
        """Initializes the Supabase client."""
        if not all([SUPABASE_URL, SUPABASE_KEY]):
            raise ConnectionError("Supabase URL or Key is not set in config.py.")
        try:
            print("Initializing Supabase client with:", SUPABASE_URL, SUPABASE_KEY)
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
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

    def add_internship(self, user_id: str, job_data: dict):
        """Adds a new internship record for a specific user."""
        try:
            job_data['user_id'] = user_id
            data, count = self.client.table('internships').insert(job_data).execute()
            if data and len(data[1]) > 0:
                return {'success': True, 'data': data[1][0], 'is_new': True}
            else:
                return {'error': 'Failed to insert data.'}
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                return {"error": "duplicate", "message": "You have already saved this internship."}
            return {"error": str(e)}

    def get_internships_by_user(self, user_id: str):
        """Fetches all internship records for a specific user."""
        if not user_id:
            return []
            
        try:
            response = self.client.table('internships').select('*').eq('user_id', user_id).execute()
            
            # Get data from response
            data = response.data if hasattr(response, 'data') else response
            
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

