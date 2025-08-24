import tweepy, json, os, requests


CONSUMER_KEY = os.environ["X_API_KEY"]
CONSUMER_SECRET = os.environ["X_API_SECRET"]
CLIENT_ID = os.environ["X_CLIENT_ID"]
CLIENT_SECRET = os.environ["X_CLIENT_SECRET"]   # Optional but recommended
BEARER_TOKEN = os.environ["X_API_BEARER_TOKEN"] # Optional
REDIRECT_URI = "http://localhost:3000/callback"


# TODO: stop using this: os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class XBot:
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, bearer_token=BEARER_TOKEN, redirect_uri=REDIRECT_URI):
        self.client_id = client_id
        self.client_secret = client_secret  # Optional but recommended
        self.bearer_token = bearer_token    # Helpful for some operations
        self.redirect_uri = redirect_uri
        self.oauth2_user_handler = None
        self.client = None
        self.tokens = {}
        self.token_file = "../tokens.json"     # File to store tokens persistently
        
    def load_tokens(self):
        """Load tokens from file if they exist"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    self.tokens = json.load(f)
                    print("Loaded existing tokens")
                    return True
        except Exception as e:
            print(f"Error loading tokens: {e}")
        return False
        
    def save_tokens(self):
        """Save tokens to file"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
                print("Tokens saved successfully")
        except Exception as e:
            print(f"Error saving tokens: {e}")
    
    def authenticate(self, use_automatic_server=False):  # Default to manual method
        """Perform OAuth 2.0 authentication with PKCE"""
        # Try to load existing tokens first
        if self.load_tokens():
            try:
                self.client = tweepy.Client(
                    consumer_key = CONSUMER_KEY,
                    consumer_secret= CONSUMER_SECRET,
                    bearer_token=self.tokens.get('access_token'),
                    wait_on_rate_limit=True
                )
                
                # Test the connection
                user = self.client.get_me()
                print(f"Already authenticated as: @{user.data.username}")
                return True
                
            except Exception as e:
                print(f"Existing tokens invalid: {e}")
                print("Need to re-authenticate...")
        
        # Create OAuth 2.0 handler with PKCE
        # Temporarily allow HTTP for localhost (for development only)
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        self.oauth2_user_handler = tweepy.OAuth2UserHandler(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
            client_secret=self.client_secret  # Include if you have it
        )
        
        # Get authorization URL
        auth_url = self.oauth2_user_handler.get_authorization_url()
        
        print(f"\n📋 Please visit this URL to authorize the application:")
        print(f"{auth_url}")
        print("\nAfter authorizing, you'll be redirected to a callback URL.")
        print("Copy and paste the ENTIRE callback URL here:")
        callback_url = input("Callback URL: ").strip()
        
        try:
            # Use the full callback URL for token exchange
            # This preserves the state parameter for CSRF protection
            token_response = self.oauth2_user_handler.fetch_token(
                authorization_response=callback_url
            )
            
            # Debug: Print token response to understand its structure
            print(f"Debug - Token response type: {type(token_response)}")
            print(f"Debug - Token response: {token_response}")
            
            # Handle different token response formats
            if isinstance(token_response, dict):
                access_token = token_response.get('access_token')
            elif isinstance(token_response, str):
                access_token = token_response
            else:
                # Sometimes it's a token object
                access_token = str(token_response)
            
            print(f"Debug - Extracted access_token: {access_token}")
            
            # Store tokens
            self.tokens = {
                'access_token': access_token,
            }
            
            self.save_tokens()
            
            # Skip tweepy client creation - use direct API calls instead
            print(f"✅ OAuth 2.0 authentication successful!")
            print(f"🔧 Using direct API calls (bypassing tweepy client issues)")
            
            # Store the oauth handler for future use
            self.oauth2_handler = self.oauth2_user_handler
            self.oauth2_handler.token = token_response
            
            # Set client to None - we'll use direct API calls
            self.client = None
            
            # Verify authentication with a test API call
            user_data = self.get_user_info()
            if user_data:
                print(f"🎉 Authenticated as: @{user_data['username']}")
                return True
            else:
                raise Exception("Failed to verify authentication")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("\nTroubleshooting tips:")
            print("1. Make sure you copied the ENTIRE callback URL")
            print("2. The URL should start with: http://localhost:3000/callback?")
            print("3. Try the authentication process again")
            return False
    
    def _make_oauth2_request(self, method, url, json_data=None):
        """Make direct OAuth 2.0 API request"""        
        headers = {
            "Authorization": f"Bearer {self.tokens.get('access_token')}",
            "Content-Type": "application/json"
        }
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        
        return response
    
    def tweet(self, text):
        """Post a tweet using direct OAuth 2.0 API call"""

        if not text:
            return None

        if not self.tokens.get('access_token'):
            print("Not authenticated. Please call authenticate() first.")
            return None
            
        try:
            # Use direct API call (bypassing tweepy client issues)
            url = "https://api.twitter.com/2/tweets"
            response = self._make_oauth2_request("POST", url, {"text": text})
            
            if response.status_code == 201:
                data = response.json()
                tweet_id = data['data']['id']
                print(f"✅ Tweet posted successfully! ID: {tweet_id}")
                return data
            else:
                print(f"❌ Error posting tweet: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error posting tweet: {e}")
            return None
    
    def get_user_info(self):
        """Get authenticated user information using direct API call"""
        if not self.tokens.get('access_token'):
            print("Not authenticated. Please call authenticate() first.")
            return None
            
        try:
            # Use direct API call (bypassing tweepy client issues)
            url = "https://api.twitter.com/2/users/me?user.fields=public_metrics,description"
            response = self._make_oauth2_request("GET", url)
            
            if response.status_code == 200:
                data = response.json()
                return data['data']
            else:
                print(f"❌ Error getting user info: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            return None
    
    def refresh_token_if_needed(self):
        """Refresh access token if it's expired or about to expire"""
        if not self.tokens:
            return False
            
        # Check if token is expired or expires soon (within 5 minutes)
        import time
        current_time = time.time()
        expires_at = self.tokens.get('expires_at', 0)
        
        if expires_at - current_time < 300:  # Less than 5 minutes left
            print("🔄 Token expired or expiring soon, refreshing...")
            try:
                # Use the refresh token to get a new access token
                refresh_token = self.tokens.get('refresh_token')
                if not refresh_token:
                    print("❌ No refresh token available, need to re-authenticate")
                    return False
                
                # Create a new OAuth handler for refresh
                import os
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                
                oauth_handler = tweepy.OAuth2UserHandler(
                    client_id=self.client_id,
                    redirect_uri=self.redirect_uri,
                    client_secret=self.client_secret
                )
                
                # Refresh the token
                new_token = oauth_handler.refresh_token(
                    f"https://api.twitter.com/2/oauth2/token",
                    refresh_token=refresh_token,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                
                # Update stored tokens
                if isinstance(new_token, dict):
                    access_token = new_token.get('access_token')
                else:
                    access_token = str(new_token)
                
                self.tokens = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,  # Keep the same refresh token
                    'expires_at': current_time + new_token.get('expires_in', 7200)
                }
                
                self.save_tokens()
                print("✅ Token refreshed successfully!")
                return True
                
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                return False
        
        return True  # Token is still valid
    
    def authenticate_silently(self):
        """Try to authenticate using saved tokens without user interaction"""
        if not self.load_tokens():
            print("❌ No saved tokens found. Need to authenticate manually first.")
            return False
        
        if not self.refresh_token_if_needed():
            print("❌ Token refresh failed. Need to authenticate manually.")
            return False
        
        # Test the authentication
        user_info = self.get_user_info()
        if user_info:
            print(f"✅ Silent authentication successful!")
            print(f"🎉 Authenticated as: @{user_info['username']}")
            return True
        else:
            print("❌ Silent authentication failed. Need to authenticate manually.")
            return False
        
        
def main():
    bot = XBot()

    if not bot.authenticate_silently():
        print("Authentication using existing tokens failed.")
        if not bot.authenticate():
            print("Authentication failed. Please check your credentials.")

    print("\n" + "="*50)
    print("X Bot Ready!")
    print("="*50)
    # print_user_info(bot.get_user_info()) # careful with too many requests
    
    while True:
        print("\nOptions:")
        print("1. Post a tweet")
        print("2. Get user info")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == "1":
            tweet_text = input("Enter tweet text: ").strip()
            bot.tweet(tweet_text)
                    
        elif choice == "2":
            print_user_info(bot.get_user_info())
                
        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

def print_user_info(user_info):
    if user_info:
        print(f"\nUser Info:")
        print(f"Username: @{user_info['username']}")
        print(f"Name: {user_info['name']}")
        print(f"Bio: {user_info.get('description', 'No bio')}")
        print(f"Followers: {user_info['public_metrics']['followers_count']}")

if __name__ == "__main__":
    main()
        