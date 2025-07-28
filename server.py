#!/usr/bin/env python3
"""
Spotify OAuth server for soul extraction app
"""

import os
import json
import time
import datetime
import logging
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from flask import Flask, redirect, request, jsonify, render_template, session, flash
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import spotipy
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest, InternalServerError

load_dotenv()

# basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oauth_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8889
    debug: bool = True
    tokens_dir: str = "tokens"
    session_timeout: int = 3600  # 1 hour
    max_token_age: int = 86400   # 24 hours
    scope: str = "user-top-read user-read-recently-played user-library-read playlist-read-private playlist-modify-public playlist-modify-private"

class SpotifyOAuthManager:
    """Handles Spotify OAuth flow"""

    

    def __init__(self, config: ServerConfig):
        self.config = config
        self.tokens_dir = Path(config.tokens_dir)
        self.tokens_dir.mkdir(exist_ok=True)
        
        required = [
            'SPOTIPY_CLIENT_ID',
            'SPOTIPY_CLIENT_SECRET', 
            'SPOTIPY_REDIRECT_URI'
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            logger.error(f"Missing env vars: {missing}")
            raise ValueError(f"Missing: {missing}")
        
        logger.info("Environment vars loaded")
        
        self.sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope=config.scope,
            show_dialog=True
        )
        
        self.auth_attempts = {}
        self.successful_auths = []
        self.start_time = datetime.datetime.now()
    
    def generate_auth_url(self, state: Optional[str] = None) -> Dict[str, Any]:
        if not state:
            state = secrets.token_urlsafe(32)
        
        try:
            auth_url = self.sp_oauth.get_authorize_url(state=state)
            
            logger.info(f"Auth URL generated for {state[:8]}...")
            
            return {
                'auth_url': auth_url,
                'state': state,
                'expires_in': 600,
                'scope': self.config.scope
            }
            
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            raise
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        logger.info(f"Processing callback for {state[:8]}...")
        
        try:
            token_info = self.sp_oauth.get_access_token(code, as_dict=True, check_cache=False)
            
            if not token_info:
                raise ValueError("No token received")
            
            user_profile = self._get_user_profile(token_info['access_token'])
            user_id = user_profile['id']
            
            token_file = self._save_token(token_info, user_profile)
            
            logger.info(f"Auth completed for {user_profile.get('display_name', user_id)}")
            
            return {
                'success': True,
                'user_id': user_id,
                'user_name': user_profile.get('display_name'),
                'token_file': str(token_file),
                'expires_at': token_info.get('expires_at'),
                'scope': token_info.get('scope')
            }
            
        except SpotifyException as e:
            logger.error(f"Spotify error: {e}")
            raise BadRequest(f"Spotify auth failed: {e}")
            
        except Exception as e:
            logger.error(f"Callback error: {e}")
            raise InternalServerError(f"she dont work: {e}")
    
    def _get_user_profile(self, access_token: str) -> Dict[str, Any]:
        # need this to get user info - pretty basic stuff
        try:
            sp = spotipy.Spotify(auth=access_token)
            profile = sp.current_user()
            if not profile:
                # this shouldnt happen but just in case
                raise ValueError("profile came back empty")
            return profile
        except Exception as e:
            # sometimes spotify is weird about this
            logger.error(f"Failed to get user profile: {e}")
            raise
    
    def _save_token(self, token_info: Dict[str, Any], user_profile: Dict[str, Any]) -> Path:
        user_id = user_profile['id']
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        token_file = self.tokens_dir / f"spotify_token_{user_id}_{timestamp}.json"
        
        try:
            with open(token_file, 'w') as f:
                json.dump(token_info, f, indent=2, ensure_ascii=False)
            
            token_file.chmod(0o600)  # secure permissions
            
            self._cleanup_old_tokens(user_id)
            
            logger.info(f"Token saved: {token_file.name}")
            return token_file
            
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            raise
    
    def _cleanup_old_tokens(self, user_id: str, keep_count: int = 3):
        try:
            user_tokens = sorted(
                [f for f in self.tokens_dir.glob(f"*{user_id}_*.json")],
                key=lambda f: f.stat().st_ctime,
                reverse=True
            )
            
            # Remove old tokens beyond keep_count
            for old_token in user_tokens[keep_count:]:
                old_token.unlink()
                logger.info(f"Cleaned up old token: {old_token.name}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old tokens: {e}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        now = datetime.datetime.now()
        
        token_files = list(self.tokens_dir.glob("*.json"))
        recent_tokens = [
            f for f in token_files 
            if (now - datetime.datetime.fromtimestamp(f.stat().st_ctime)).seconds < 3600
        ]
        
        return {
            'server_uptime': getattr(self, '_start_time', now).isoformat(),
            'total_tokens': len(token_files),
            'recent_tokens': len(recent_tokens),
            'server_version': '2.0'
        }

# init the OAuth manager
config = ServerConfig()
oauth_manager = SpotifyOAuthManager(config)

# init Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = False  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(seconds=config.session_timeout)

@app.route('/')
def index():
    stats = oauth_manager.get_server_stats()
    return render_template('entrance.html', stats=stats)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '2.0'
    })



@app.route('/get-auth-url')
def get_auth_url():
    try:
        auth_data = oauth_manager.generate_auth_url()
        session['oauth_state'] = auth_data['state']
        return jsonify(auth_data)
        
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        return jsonify({'error': 'auth url messed up'}), 500

@app.route('/callback')
def spotify_callback():
    """Handle Spotify OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return f"""
        <div style="font-family: Arial; padding: 20px; background: #1a1a1a; color: #1db954;">
            <h1>❌ Authorization Failed</h1>
            <p>Error: {error}</p>
            <p>Please try again.</p>
        </div>
        """, 400
    
    if code:
        return f"""
        <div style="font-family: Arial; padding: 20px; background: #1a1a1a; color: #1db954;">
            <h1>✅ Authorization Successful!</h1>
            <p><strong>Copy this ENTIRE URL and paste it into your terminal:</strong></p>
            <div style="background: #333; padding: 10px; border-radius: 5px; word-break: break-all; margin: 10px 0;">
                <code style="color: #fff;">{request.url}</code>
            </div>
            <p>Then press Enter in your terminal to continue.</p>
        </div>
        """
    
    return "No authorization code received", 400

@app.route('/exit')
def exit_screen():
    status = request.args.get('status', 'unknown')
    auth_success = session.get('auth_success')
    
    return render_template('exit.html', 
                         status=status, 
                         auth_success=auth_success,
                         timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.after_request
def add_security_headers(response):
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Development helper (remove in production)
    if config.debug:
        response.headers["ngrok-skip-browser-warning"] = "true"
    
    return response

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('index.html', error="page doesnt work"), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"❌ Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main server startup"""
    logger.info(f"Starting Spotify OAuth Server on {config.host}:{config.port}")
    
    try:
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main()