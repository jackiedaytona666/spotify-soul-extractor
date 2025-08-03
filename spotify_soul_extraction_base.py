#!/usr/bin/env python3
"""
Spotify data extraction script
"""

import json
import os
import datetime
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class ExtractionConfig:
    """Configuration for Spotify data extraction"""
    token_dir: str = "tokens"
    output_dir: str = "data"
    scope: str = "user-top-read user-read-recently-played user-library-read"
    max_retries: int = 3
    rate_limit_delay: float = 0.5

class SpotifyTokenManager:
    """Manages Spotify authentication tokens with automatic discovery"""
    
    def __init__(self, token_dir: str = "tokens"):
        self.token_dir = Path(token_dir)
        self.token_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_token(self) -> Path:
        """Find and return the latest token file"""
        token_files = [
            f for f in self.token_dir.iterdir() 
            if f.is_file() and f.name.startswith("spotify_token_") and f.suffix == ".json"
        ]
        
        if not token_files:
            logger.error("No Spotify token files found in tokens/ directory")
            logger.info("Please run the authentication flow first:")
            logger.info("   1. Run server.py to start the auth server")
            logger.info("   2. Visit the auth URL in your browser")
            logger.info("   3. Complete the OAuth flow")
            raise FileNotFoundError("No Spotify token files found in tokens/. Please authenticate first.")
        
        # Sort by creation time and get the most recent
        latest_token = max(token_files, key=lambda f: f.stat().st_ctime)
        
        logger.info(f"Using token: {latest_token.name}")
        logger.info(f"Token created: {datetime.datetime.fromtimestamp(latest_token.stat().st_ctime)}")
        
        return latest_token
    
    def validate_token(self, token_path: Path) -> bool:
        """Validate that the token file is properly formatted"""
        try:
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            
            required_fields = ['access_token', 'token_type', 'expires_at']
            missing_fields = [field for field in required_fields if field not in token_data]
            
            if missing_fields:
                logger.warning(f"Token missing fields: {missing_fields}")
                return False
            
            # Check if token is expired
            expires_at = token_data.get('expires_at', 0)
            if expires_at < time.time():
                logger.warning("Token appears to be expired")
                return False
            
            logger.info("Token validation passed")
            return True
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Token validation failed: {e}")
            return False

class SpotifyDataExtractor:
    """pulls spotify data and tries not to break"""
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self.token_manager = SpotifyTokenManager(self.config.token_dir)
        self.sp = self._initialize_spotify_client()
        self._setup_output_directory()
    
    def _setup_output_directory(self):
        self.output_path = Path(self.config.output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.output_path / "raw").mkdir(exist_ok=True)
        (self.output_path / "processed").mkdir(exist_ok=True)
        (self.output_path / "backups").mkdir(exist_ok=True)
    
    def _initialize_spotify_client(self) -> Spotify:
        latest_token = self.token_manager.get_latest_token()
        
        # Validate token before using
        if not self.token_manager.validate_token(latest_token):
            logger.error("Token validation failed. Please re-authenticate to obtain a valid token.")
            raise FileNotFoundError("Invalid or expired Spotify token. Please run the authentication flow again.")
        
        try:
            sp = Spotify(auth_manager=SpotifyOAuth(
                scope=self.config.scope,
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                cache_path=str(latest_token)
            ))
            
            # Test the connection
            user = sp.current_user()
            if user:
                logger.info(f"Connected as: {user.get('display_name', 'Unknown')} ({user.get('id', 'Unknown')})")
            else:
                # sometimes user comes back empty - weird but whatever
                logger.info("Connected but user profile empty")
            
            return sp
            
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise
    
    def _safe_api_call(self, func, operation_name: str = "API call") -> Optional[Dict[str, Any]]:
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Attempting {operation_name} (attempt {attempt + 1})")
                time.sleep(self.config.rate_limit_delay)  # Rate limiting
                result = func()
                logger.debug(f"{operation_name} successful")
                return result
                
            except SpotifyException as e:
                logger.warning(f"Spotify API error in {operation_name} (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    logger.error(f"{operation_name} failed after {self.config.max_retries} attempts")
                    return None
                # Exponential backoff
                time.sleep(self.config.rate_limit_delay * (2 ** attempt))
                
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                return None
        
        return None
    
    def extract_comprehensive_data(self) -> Dict[str, Any]:
        """Extract Spotify data with progress tracking - should work"""
        logger.info("Starting comprehensive Spotify data extraction...")
        
        # this takes a while so be patient
        extraction_start = time.time()
        
        # Initialize data structure with metadata
        data = {
            "extraction_metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "extractor_version": "2.0",
                "spotify_user_id": None,
                "total_extraction_time": None,
                "data_completeness": {}
            }
        }
        
        # Get user profile first
        logger.info("Extracting user profile...")
        user_profile = self._safe_api_call(
            lambda: self.sp.current_user(),
            "user profile extraction"
        )
        if user_profile:
            data["user_profile"] = user_profile
            data["extraction_metadata"]["spotify_user_id"] = user_profile.get('id') # type: ignore
            logger.info(f"User: {user_profile.get('display_name', 'Unknown')}")
        
        # Extract top items
        logger.info("Extracting top tracks and artists...")
        data["top_tracks"] = self._extract_top_items('tracks')
        data["top_artists"] = self._extract_top_items('artists')
        
        # Extract recent tracks
        logger.info("Extracting recently played tracks...")
        recent_tracks = self._safe_api_call(
            lambda: self.sp.current_user_recently_played(limit=50),
            "recent tracks extraction"
        )
        # handle None case - api sometimes fails
        data["recent_tracks"] = recent_tracks if recent_tracks else {"items": []}
        
        # Extract saved tracks
        logger.info("Extracting saved tracks...")
        saved_tracks = self._safe_api_call(
            lambda: self.sp.current_user_saved_tracks(limit=50),
            "saved tracks extraction"
        )
        # same deal as recent tracks - dont let None break things
        data["saved_tracks"] = saved_tracks if saved_tracks else {"items": []}
        
        # Calculate extraction metrics
        extraction_time = time.time() - extraction_start
        data["extraction_metadata"]["total_extraction_time"] = f"{extraction_time:.2f} seconds"
        data["extraction_metadata"]["data_completeness"] = self._calculate_data_completeness(data)
        
        logger.info(f"Extraction completed in {extraction_time:.2f} seconds")
        
        return data
    
    def _extract_top_items(self, item_type: str) -> Dict[str, Any]:
        # gets top tracks or artists - basic stuff
        time_ranges = {
            'short_term': '4 weeks',
            'medium_term': '6 months',
            'long_term': 'all time'
        }
        
        top_items = {}
        
        for time_range, description in time_ranges.items():
            logger.info(f"  Extracting top {item_type} ({description})...")
            
            # api is messing up again figure it out
            if item_type == 'tracks':
                api_call = lambda tr=time_range: self.sp.current_user_top_tracks(time_range=tr, limit=50)
            else:
                api_call = lambda tr=time_range: self.sp.current_user_top_artists(time_range=tr, limit=50)

            items = self._safe_api_call(
                api_call,
                f"top {item_type} ({time_range})"
            )
            
            if items and 'items' in items:
                item_count = len(items['items'])
                logger.info(f"    Found {item_count} {item_type} for {time_range}")
                
                
                
                
                
                # doit later - need to work on this tomrrow
                # dev needs more sleep brb we'll work on this tomrrow
                
                if item_count == 0:
                    logger.warning(f"    No {item_type} found for {time_range} - user might be new or have limited listening history")
            
            top_items[time_range] = items
        
        return top_items
    
    def _calculate_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        completeness = {}
        
        if "top_tracks" in data:
            for time_range, tracks_data in data["top_tracks"].items():
                if tracks_data and 'items' in tracks_data:
                    completeness[f"top_tracks_{time_range}"] = len(tracks_data['items'])
                else:
                    completeness[f"top_tracks_{time_range}"] = 0
        
        if "top_artists" in data:
            for time_range, artists_data in data["top_artists"].items():
                if artists_data and 'items' in artists_data:
                    completeness[f"top_artists_{time_range}"] = len(artists_data['items'])
                else:
                    completeness[f"top_artists_{time_range}"] = 0
        
        if "recent_tracks" in data and data["recent_tracks"]:
            completeness["recent_tracks"] = len(data["recent_tracks"].get('items', []))
        
        if "saved_tracks" in data and data["saved_tracks"]:
            completeness["saved_tracks"] = len(data["saved_tracks"].get('items', []))
        
        total_possible = sum(completeness.values())
        expected_minimum = 50  # Rough estimate of minimum expected data points
        completeness["overall_score"] = min(total_possible / expected_minimum, 1.0) if expected_minimum > 0 else 0
        
        return completeness
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # checks if the data looks right - sometimes api returns weird stuff
        validation_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "validation_passed": True,
            "warnings": [],
            "errors": [],
            "data_quality_score": 1.0
        }
        
        empty_sections = []
        for section_name in ["top_tracks", "top_artists", "recent_tracks"]:
            if section_name in data:
                if section_name in ["top_tracks", "top_artists"]:
                    for time_range, section_data in data[section_name].items():
                        if not section_data or not section_data.get('items'):
                            empty_sections.append(f"{section_name}_{time_range}")
                else:
                    if not data[section_name] or not data[section_name].get('items'):
                        empty_sections.append(section_name)
        
        if empty_sections:
            validation_report["warnings"].append(f"Empty data sections: {', '.join(empty_sections)}")
            validation_report["data_quality_score"] *= 0.8
        
        if "user_profile" not in data or not data["user_profile"]:
            validation_report["errors"].append("Missing user profile data")
            validation_report["validation_passed"] = False
            validation_report["data_quality_score"] *= 0.5
        
        if validation_report["validation_passed"]:
            logger.info(f"Data validation passed (Quality Score: {validation_report['data_quality_score']:.2f})")
        else:
            logger.error("Data validation failed")
        
        for warning in validation_report["warnings"]:
            logger.warning(f"{warning}")
        
        for error in validation_report["errors"]:
            logger.error(f"{error}")
        
        return validation_report
    
    def save_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        # saves data to file - pretty straightforward 
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spotify_soul_data_{timestamp}.json"
        
        output_file = self.output_path / "raw" / filename
        
        # backup old files - dont want to lose anything
        if output_file.exists():
            backup_file = self.output_path / "backups" / f"backup_{filename}"
            # Ensure backup file does not overwrite an existing backup
            if backup_file.exists():
                base = backup_file.stem
                ext = backup_file.suffix
                i = 1
                while True:
                    new_backup_file = backup_file.parent / f"{base}_{i}{ext}"
                    if not new_backup_file.exists():
                        backup_file = new_backup_file
                        break
                    i += 1
            output_file.rename(backup_file)
            logger.info(f"Created backup: {backup_file}")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to: {output_file}")
        except Exception as e:
            # file writing messed up
            logger.error(f"Couldn't save file: {e}")
            raise IOError(f"Failed to save data to {output_file}: {e}")
        file_size = output_file.stat().st_size
        logger.info(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return output_file
    
    def generate_extraction_summary(self, data: Dict[str, Any], validation_report: Dict[str, Any]) -> str:
        user = data.get('user_profile', {})
        metadata = data.get('extraction_metadata', {})
        completeness = metadata.get('data_completeness', {})
        
        # Build the summary step by step - easier to debug this way
        summary = "=== SPOTIFY DATA EXTRACTION REPORT ===\n\n"
        summary += f"User: {user.get('display_name', 'Unknown')} ({user.get('id', 'Unknown')})\n"
        summary += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"Extraction Time: {metadata.get('total_extraction_time', 'Unknown')}\n"
        summary += f"Quality Score: {validation_report.get('data_quality_score', 0):.2f}/1.00\n\n"
        summary += "TOP TRACKS:\n"
        
        for time_range in ['short_term', 'medium_term', 'long_term']:
            count = completeness.get(f'top_tracks_{time_range}', 0)
            range_name = {'short_term': '4 weeks', 'medium_term': '6 months', 'long_term': 'all time'}
            summary += f"   {range_name[time_range]:>8}: {count:>2} tracks\n"
        
        summary += "\nTOP ARTISTS:\n"
        for time_range in ['short_term', 'medium_term', 'long_term']:
            count = completeness.get(f'top_artists_{time_range}', 0)
            range_name = {'short_term': '4 weeks', 'medium_term': '6 months', 'long_term': 'all time'}
            summary += f"   {range_name[time_range]:>8}: {count:>2} artists\n"
        
        summary += f"\nRecent Tracks: {completeness.get('recent_tracks', 0)} tracks\n"
        summary += f"Saved Tracks: {completeness.get('saved_tracks', 0)} tracks\n"
        
        if validation_report.get('warnings'):
            summary += "\nWARNINGS:\n"
            for warning in validation_report['warnings']:
                summary += f"   - {warning}\n"
        
        if validation_report.get('errors'):
            summary += "\nERRORS:\n"
            for error in validation_report['errors']:
                summary += f"   - {error}\n"
        
        summary += f"\nOverall Quality: {validation_report.get('data_quality_score', 0):.1%}\n"
        summary += "\nGenerated by Spotify Soul Extractor v2.0\n"
        
        return summary

def main():
    """Main execution function"""
    try:
        config = ExtractionConfig()
        extractor = SpotifyDataExtractor(config)
        data = extractor.extract_comprehensive_data()
        validation_report = extractor.validate_extracted_data(data)
        output_file = extractor.save_data(data)
        summary = extractor.generate_extraction_summary(data, validation_report)
        print(summary)
        summary_file = output_file.parent / f"summary_{output_file.stem}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Summary saved to: {summary_file}")
        logger.info("Extraction completed successfully!")
    except FileNotFoundError as e:
        logger.error(f"Authentication error: {e}")
        logger.info("Please run the authentication flow first")
    except Exception as e:
        # something went really wrong here
        logger.error(f"Unexpected error during extraction: {e}")
        logger.exception("Full error details:")

if __name__ == "__main__":
    main()