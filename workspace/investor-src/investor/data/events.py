"""
Event data management for integrating major events with financial analysis.
"""
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class EventDataManager:
    """Manage major events data for financial analysis integration."""
    
    def __init__(self, events_dir: str = "events"):
        """
        Initialize event data manager.
        
        Args:
            events_dir: Directory containing events data
        """
        self.events_dir = Path(events_dir)
        self.events_cache = {}
        self._load_all_events()
    
    def _load_all_events(self) -> None:
        """Load all events from JSON files into memory."""
        try:
            self.events_cache = {}
            
            if not self.events_dir.exists():
                logger.warning(f"Events directory not found: {self.events_dir}")
                return
            
            # Load events from all subdirectories
            for json_file in self.events_dir.rglob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        events_data = json.load(f)
                    
                    # Handle both single events and lists of events
                    if isinstance(events_data, list):
                        events = events_data
                    else:
                        events = [events_data]
                    
                    # Store events by category
                    category = json_file.parent.name
                    if category not in self.events_cache:
                        self.events_cache[category] = []
                    
                    self.events_cache[category].extend(events)
                    
                    logger.debug(f"Loaded {len(events)} events from {json_file}")
                    
                except Exception as e:
                    logger.error(f"Error loading events from {json_file}: {e}")
            
            total_events = sum(len(events) for events in self.events_cache.values())
            logger.info(f"Loaded {total_events} events from {len(self.events_cache)} categories")
            
        except Exception as e:
            logger.error(f"Error loading events: {e}")
    
    def get_events_for_timeframe(self, start_date: date, end_date: date, 
                                categories: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get events within a specific timeframe.
        
        Args:
            start_date: Start date for events
            end_date: End date for events
            categories: Optional list of categories to include
            
        Returns:
            DataFrame with filtered events
        """
        all_events = []
        
        for category, events in self.events_cache.items():
            if categories and category not in categories:
                continue
                
            for event in events:
                try:
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    
                    if start_date <= event_date <= end_date:
                        event_copy = event.copy()
                        event_copy['category'] = category
                        all_events.append(event_copy)
                        
                except Exception as e:
                    logger.debug(f"Error processing event {event.get('event_id', 'unknown')}: {e}")
        
        if not all_events:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_events)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def get_events_for_symbols(self, symbols: List[str], 
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Get events that might affect specific symbols.
        
        Args:
            symbols: List of stock symbols
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            DataFrame with relevant events
        """
        relevant_events = []
        
        for category, events in self.events_cache.items():
            for event in events:
                try:
                    # Check if event affects any of the requested symbols
                    affected_symbols = event.get('affected_symbols', [])
                    
                    if any(symbol in affected_symbols for symbol in symbols):
                        # Apply date filter if specified
                        if start_date or end_date:
                            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                            
                            if start_date and event_date < start_date:
                                continue
                            if end_date and event_date > end_date:
                                continue
                        
                        event_copy = event.copy()
                        event_copy['category'] = category
                        relevant_events.append(event_copy)
                        
                except Exception as e:
                    logger.debug(f"Error processing event {event.get('event_id', 'unknown')}: {e}")
        
        if not relevant_events:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(relevant_events)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def get_events_by_severity(self, severity: str) -> pd.DataFrame:
        """Get events by severity level."""
        filtered_events = []
        
        for category, events in self.events_cache.items():
            for event in events:
                if event.get('severity') == severity:
                    event_copy = event.copy()
                    event_copy['category'] = category
                    filtered_events.append(event_copy)
        
        if not filtered_events:
            return pd.DataFrame()
        
        df = pd.DataFrame(filtered_events)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def get_event_summary(self) -> Dict[str, Any]:
        """Get summary statistics about available events."""
        summary = {
            'total_events': 0,
            'categories': {},
            'severity_distribution': {},
            'date_range': {},
            'most_affected_symbols': {}
        }
        
        all_symbols = []
        all_dates = []
        
        for category, events in self.events_cache.items():
            summary['categories'][category] = len(events)
            summary['total_events'] += len(events)
            
            for event in events:
                # Count severity
                severity = event.get('severity', 'unknown')
                summary['severity_distribution'][severity] = summary['severity_distribution'].get(severity, 0) + 1
                
                # Collect symbols and dates
                all_symbols.extend(event.get('affected_symbols', []))
                try:
                    all_dates.append(datetime.strptime(event['date'], '%Y-%m-%d'))
                except:
                    pass
        
        # Calculate date range
        if all_dates:
            summary['date_range'] = {
                'earliest': min(all_dates).strftime('%Y-%m-%d'),
                'latest': max(all_dates).strftime('%Y-%m-%d')
            }
        
        # Most affected symbols
        if all_symbols:
            symbol_counts = {}
            for symbol in all_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            # Top 10 most affected symbols
            sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
            summary['most_affected_symbols'] = dict(sorted_symbols[:10])
        
        return summary
    
    def add_event(self, event: Dict[str, Any], category: str) -> bool:
        """
        Add a new event to the database.
        
        Args:
            event: Event dictionary following the schema
            category: Event category
            
        Returns:
            True if successful
        """
        try:
            # Validate required fields
            required_fields = ['event_id', 'date', 'title', 'description', 'severity']
            for field in required_fields:
                if field not in event:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add to cache
            if category not in self.events_cache:
                self.events_cache[category] = []
            
            self.events_cache[category].append(event)
            
            # Save to file
            category_dir = self.events_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename based on event date and id
            filename = f"{event['date']}_{event['event_id']}.json"
            filepath = category_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(event, f, indent=2)
            
            logger.info(f"Added event {event['event_id']} to category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return False