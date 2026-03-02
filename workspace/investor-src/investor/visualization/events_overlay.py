"""
Events overlay visualization for stock charts.
Integrates major market events as annotations and overlays on price charts.
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class EventsOverlay:
    """Create event overlays and annotations for stock charts."""
    
    def __init__(self):
        """Initialize events overlay system."""
        self.severity_colors = {
            'critical': '#DC143C',  # Crimson
            'high': '#FF8C00',      # Dark orange
            'medium': '#FFD700',    # Gold
            'low': '#32CD32',       # Lime green
            'unknown': '#808080'    # Gray
        }
        
        self.category_markers = {
            'economic': 'v',        # Triangle down
            'market_events': 'o',   # Circle
            'earnings': 's',        # Square
            'political': '^',       # Triangle up
            'natural_disasters': 'D' # Diamond
        }
    
    def add_events_to_chart(self, ax, price_data: pd.DataFrame, 
                           events_data: pd.DataFrame, 
                           show_annotations: bool = True,
                           show_price_impact: bool = True) -> None:
        """
        Add event markers and annotations to an existing chart.
        
        Args:
            ax: Matplotlib axis object
            price_data: Stock price DataFrame with datetime index
            events_data: Events DataFrame with date, title, severity columns
            show_annotations: Whether to show text annotations
            show_price_impact: Whether to highlight price impact areas
        """
        if events_data.empty:
            return
        
        # Ensure price_data has datetime index
        if not isinstance(price_data.index, pd.DatetimeIndex):
            if 'Date' in price_data.columns:
                price_data = price_data.set_index('Date')
            price_data.index = pd.to_datetime(price_data.index)
        
        # Get price range for positioning annotations
        price_min = price_data['Close'].min()
        price_max = price_data['Close'].max()
        price_range = price_max - price_min
        
        annotation_positions = []
        
        for idx, event in events_data.iterrows():
            event_date = pd.to_datetime(event['date'])
            
            # Skip events outside the price data range
            if event_date < price_data.index.min() or event_date > price_data.index.max():
                continue
            
            # Get closest price point
            closest_price_idx = price_data.index.get_indexer([event_date], method='nearest')[0]
            if closest_price_idx == -1:
                continue
                
            closest_date = price_data.index[closest_price_idx]
            event_price = price_data.iloc[closest_price_idx]['Close']
            
            # Color and marker based on severity and category
            color = self.severity_colors.get(event.get('severity', 'unknown'), '#808080')
            marker = self.category_markers.get(event.get('category', 'market_events'), 'o')
            
            # Add event marker
            ax.scatter(closest_date, event_price, 
                      color=color, marker=marker, s=100, 
                      alpha=0.8, edgecolors='black', linewidth=1,
                      zorder=10)
            
            # Add price impact highlighting
            if show_price_impact:
                self._add_price_impact_highlight(ax, price_data, event_date, color)
            
            # Add text annotation
            if show_annotations:
                # Calculate annotation position to avoid overlap
                annotation_y = self._calculate_annotation_position(
                    event_price, price_min, price_max, annotation_positions
                )
                annotation_positions.append(annotation_y)
                
                # Create annotation text
                annotation_text = f"{event.get('title', 'Event')[:30]}"
                if len(event.get('title', '')) > 30:
                    annotation_text += "..."
                
                # Add severity indicator
                severity = event.get('severity', 'unknown').upper()
                annotation_text = f"[{severity}] {annotation_text}"
                
                # Add annotation with arrow
                ax.annotate(annotation_text,
                           xy=(closest_date, event_price),
                           xytext=(closest_date, annotation_y),
                           fontsize=8,
                           bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor=color, alpha=0.7),
                           arrowprops=dict(arrowstyle='->', 
                                         connectionstyle='arc3,rad=0.1',
                                         color=color))
    
    def _add_price_impact_highlight(self, ax, price_data: pd.DataFrame, 
                                  event_date: pd.Timestamp, color: str) -> None:
        """Add price impact highlighting around event date."""
        # Define impact window (3 days before and after)
        impact_window = 3
        start_date = event_date - timedelta(days=impact_window)
        end_date = event_date + timedelta(days=impact_window)
        
        # Get price range
        price_min = price_data['Close'].min()
        price_max = price_data['Close'].max()
        
        # Add semi-transparent rectangle
        rect = Rectangle((start_date, price_min), 
                        end_date - start_date, 
                        price_max - price_min,
                        facecolor=color, alpha=0.1, zorder=1)
        ax.add_patch(rect)
    
    def _calculate_annotation_position(self, event_price: float, 
                                     price_min: float, price_max: float,
                                     existing_positions: List[float]) -> float:
        """Calculate annotation position to minimize overlap."""
        price_range = price_max - price_min
        
        # Start with position above the event price
        base_position = event_price + (price_range * 0.1)
        
        # Adjust if too close to existing annotations
        min_distance = price_range * 0.05
        position = base_position
        
        for existing_pos in existing_positions:
            if abs(position - existing_pos) < min_distance:
                # Move up to avoid overlap
                position = existing_pos + min_distance
        
        # Keep within chart bounds
        max_position = price_max + (price_range * 0.05)
        position = min(position, max_position)
        
        return position
    
    def create_events_timeline(self, events_data: pd.DataFrame, 
                             figsize: Tuple[int, int] = (15, 8),
                             output_dir: str = "outputs/latest_run/forecasting/charts") -> str:
        """
        Create a dedicated events timeline chart.
        
        Args:
            events_data: Events DataFrame
            figsize: Figure size tuple
            
        Returns:
            Path to saved timeline chart
        """
        if events_data.empty:
            logger.warning("No events data provided for timeline")
            return ""
        
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Convert dates
        events_data['date'] = pd.to_datetime(events_data['date'])
        events_data = events_data.sort_values('date')
        
        # Create timeline positions
        y_positions = []
        categories = events_data['category'].unique()
        category_positions = {cat: i for i, cat in enumerate(categories)}
        
        for _, event in events_data.iterrows():
            y_pos = category_positions[event['category']]
            y_positions.append(y_pos)
        
        events_data['y_position'] = y_positions
        
        # Plot events
        for _, event in events_data.iterrows():
            color = self.severity_colors.get(event.get('severity', 'unknown'), '#808080')
            marker = self.category_markers.get(event.get('category', 'market_events'), 'o')
            
            ax.scatter(event['date'], event['y_position'], 
                      color=color, marker=marker, s=150, 
                      alpha=0.8, edgecolors='black', linewidth=1)
            
            # Add event title
            ax.annotate(event.get('title', 'Event')[:40],
                       xy=(event['date'], event['y_position']),
                       xytext=(10, 5),
                       textcoords='offset points',
                       fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", 
                               facecolor=color, alpha=0.6))
        
        # Customize chart
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels([cat.replace('_', ' ').title() for cat in categories])
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Event Category', fontsize=12)
        ax.set_title('Market Events Timeline', fontsize=16, fontweight='bold')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add severity legend
        self._add_severity_legend(ax)
        
        plt.tight_layout()
        
        # Save timeline
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"events_timeline_{timestamp}.png"
        
        # Ensure output directory exists
        import os
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Events timeline saved: {filepath}")
        return filepath
    
    def create_event_impact_analysis(self, symbol: str, price_data: pd.DataFrame,
                                   events_data: pd.DataFrame, impact_window: int = 5,
                                   figsize: Tuple[int, int] = (15, 10),
                                   output_dir: str = "outputs/latest_run/forecasting/charts") -> str:
        """
        Create event impact analysis chart.
        
        Args:
            symbol: Stock symbol
            price_data: Stock price DataFrame
            events_data: Events DataFrame
            impact_window: Days before/after event to analyze
            figsize: Figure size tuple
            
        Returns:
            Path to saved impact analysis chart
        """
        if events_data.empty or price_data.empty:
            logger.warning("Insufficient data for event impact analysis")
            return ""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                      height_ratios=[3, 1], facecolor='white')
        
        # Ensure proper datetime index
        if not isinstance(price_data.index, pd.DatetimeIndex):
            if 'Date' in price_data.columns:
                price_data = price_data.set_index('Date')
            price_data.index = pd.to_datetime(price_data.index)
        
        # Plot price chart with events
        ax1.plot(price_data.index, price_data['Close'], 
                linewidth=2, color='#1f77b4', label=f'{symbol} Price')
        
        # Add events overlay
        self.add_events_to_chart(ax1, price_data, events_data, 
                               show_annotations=True, show_price_impact=True)
        
        ax1.set_title(f'{symbol} Price with Major Events', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Calculate and plot impact analysis
        impact_data = self._calculate_event_impacts(price_data, events_data, impact_window)
        
        if impact_data:
            impacts = [item['impact_percent'] for item in impact_data]
            event_dates = [pd.to_datetime(item['date']) for item in impact_data]
            colors = [self.severity_colors.get(item['severity'], '#808080') for item in impact_data]
            
            ax2.bar(event_dates, impacts, color=colors, alpha=0.7, width=1)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_title('Event Impact Analysis (% Price Change)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Impact (%)', fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_event_impact_{timestamp}.png"
        
        # Ensure output directory exists
        import os
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Event impact analysis saved: {filepath}")
        return filepath
    
    def _calculate_event_impacts(self, price_data: pd.DataFrame, 
                               events_data: pd.DataFrame, 
                               impact_window: int) -> List[Dict[str, Any]]:
        """Calculate price impact for each event."""
        impacts = []
        
        for _, event in events_data.iterrows():
            event_date = pd.to_datetime(event['date'])
            
            # Find price data around the event
            start_date = event_date - timedelta(days=impact_window)
            end_date = event_date + timedelta(days=impact_window)
            
            # Get price data in the window
            window_data = price_data[
                (price_data.index >= start_date) & 
                (price_data.index <= end_date)
            ]
            
            if len(window_data) < 2:
                continue
            
            try:
                # Get prices before and after event
                pre_event_data = window_data[window_data.index <= event_date]
                post_event_data = window_data[window_data.index > event_date]
                
                if len(pre_event_data) == 0 or len(post_event_data) == 0:
                    continue
                
                pre_price = pre_event_data['Close'].iloc[-1]
                post_price = post_event_data['Close'].iloc[0]
                
                impact_pct = ((post_price - pre_price) / pre_price) * 100
                
                impacts.append({
                    'date': event['date'],
                    'title': event.get('title', ''),
                    'severity': event.get('severity', 'unknown'),
                    'impact_percent': impact_pct,
                    'pre_price': pre_price,
                    'post_price': post_price
                })
                
            except Exception as e:
                logger.debug(f"Could not calculate impact for event {event.get('title', '')}: {e}")
                continue
        
        return impacts
    
    def _add_severity_legend(self, ax) -> None:
        """Add severity color legend to chart."""
        from matplotlib.lines import Line2D
        
        legend_elements = []
        for severity, color in self.severity_colors.items():
            if severity != 'unknown':
                legend_elements.append(
                    Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=color, markersize=8, 
                          label=severity.capitalize())
                )
        
        ax.legend(handles=legend_elements, loc='upper right', 
                 title='Event Severity', fontsize=9)
    
    def create_events_summary_table(self, events_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create a summary table of events for reporting.
        
        Args:
            events_data: Events DataFrame
            
        Returns:
            Summary DataFrame for display/export
        """
        if events_data.empty:
            return pd.DataFrame()
        
        summary_data = []
        
        for _, event in events_data.iterrows():
            summary_row = {
                'Date': event['date'].strftime('%Y-%m-%d') if pd.notnull(event['date']) else 'Unknown',
                'Title': event.get('title', 'Unknown Event')[:50],
                'Category': event.get('category', 'unknown').replace('_', ' ').title(),
                'Severity': event.get('severity', 'unknown').capitalize(),
                'Impact Scope': event.get('impact_scope', 'unknown').capitalize(),
                'Affected Symbols': ', '.join(event.get('affected_symbols', [])[:3]),
                'Description': event.get('description', '')[:100] + '...' if len(event.get('description', '')) > 100 else event.get('description', '')
            }
            summary_data.append(summary_row)
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Date', ascending=False)
        
        return summary_df