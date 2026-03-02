"""
Visualization management component for the investor analysis system.
Handles all visualization and reporting operations.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .config import InvestorConfig
from .exceptions import VisualizationError
from ..forecasting.scalable_plotting import ScalablePlottingSystem
from ..visualization.market_dashboard import MarketDashboard
from ..visualization.events_overlay import EventsOverlay
from ..data.events import EventDataManager

logger = logging.getLogger(__name__)


class VisualizationManager:
    """Manages all visualization and reporting operations."""
    
    def __init__(self, config: InvestorConfig):
        """Initialize the visualization manager."""
        self.config = config
        
        # Initialize visualization components
        self.plotting_system = None
        self.market_dashboard = MarketDashboard()
        self.events_overlay = EventsOverlay()
        self.events_manager = EventDataManager()
        
        logger.info("VisualizationManager initialized")
    
    def create_visualizations(self, data: Dict[str, pd.DataFrame], 
                            predictions: Dict[str, pd.DataFrame],
                            investment_signals: List[Dict[str, Any]],
                            output_dir: Path) -> Dict[str, str]:
        """
        Create comprehensive visualizations for the analysis results.
        
        Args:
            data: Raw stock data
            predictions: Forecasting results
            investment_signals: Anomaly detection results
            output_dir: Directory to save visualizations
            
        Returns:
            Dictionary mapping visualization names to file paths
            
        Raises:
            VisualizationError: If visualization creation fails
        """
        if not self.config.analysis.enable_visualization:
            logger.info("Visualization disabled in configuration")
            return {}
        
        logger.info("Creating comprehensive visualizations...")
        
        try:
            visualizations = {}
            
            # Initialize plotting system if needed
            if self.plotting_system is None:
                charts_dir = output_dir / "charts"
                charts_dir.mkdir(parents=True, exist_ok=True)
                self.plotting_system = ScalablePlottingSystem(charts_dir)
            
            # Create overview charts
            overview_path = self._create_overview_charts(data, output_dir)
            if overview_path:
                visualizations['overview'] = str(overview_path)
            
            # Create detailed forecast charts
            forecast_paths = self._create_forecast_charts(data, predictions, output_dir)
            visualizations.update(forecast_paths)
            
            # Create market dashboard
            dashboard_path = self._create_market_dashboard(data, investment_signals, output_dir)
            if dashboard_path:
                visualizations['market_dashboard'] = str(dashboard_path)
            
            # Create events analysis
            events_paths = self._create_events_analysis(data, output_dir)
            visualizations.update(events_paths)
            
            logger.info(f"Created {len(visualizations)} visualizations")
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            raise VisualizationError(f"Visualization creation failed: {e}")
    
    def _create_overview_charts(self, data: Dict[str, pd.DataFrame], output_dir: Path) -> Optional[Path]:
        """Create overview charts for all symbols."""
        try:
            logger.info("Creating overview charts")
            
            charts_dir = output_dir / "charts"
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create multi-stock overview
            overview_path = charts_dir / "portfolio_overview.png"
            
            self.plotting_system.create_portfolio_overview(
                data, 
                predictions=pd.DataFrame(),  # Empty DataFrame for predictions
                investment_signals=[],  # Empty signals for overview
                title="Portfolio Overview"
            )
            
            logger.info(f"Created overview chart: {overview_path}")
            return overview_path
            
        except Exception as e:
            logger.error(f"Error creating overview charts: {e}")
            return None
    
    def _create_forecast_charts(self, data: Dict[str, pd.DataFrame], 
                               predictions: Dict[str, pd.DataFrame],
                               output_dir: Path) -> Dict[str, str]:
        """Create detailed forecast charts for each symbol."""
        forecast_paths = {}
        
        try:
            charts_dir = output_dir / "charts"
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            for symbol in data.keys():
                try:
                    symbol_data = data.get(symbol, pd.DataFrame())
                    symbol_predictions = predictions.get(symbol, pd.DataFrame())
                    
                    if symbol_data.empty:
                        continue
                    
                    # Create detailed chart with or without predictions
                    chart_path = charts_dir / f"{symbol}_detailed.png"
                    
                    # Use the detailed stock view method that exists
                    self.plotting_system.create_detailed_stock_view(
                        symbol,
                        symbol_data,
                        symbol_predictions if not symbol_predictions.empty else pd.DataFrame(),
                        investment_signals=[],  # Filter signals for this symbol if needed
                        events_overlay=self.events_overlay
                    )
                    
                    forecast_paths[f"{symbol}_chart"] = str(chart_path)
                    logger.info(f"Created chart for {symbol}: {chart_path}")
                    
                except Exception as e:
                    logger.error(f"Error creating chart for {symbol}: {e}")
            
        except Exception as e:
            logger.error(f"Error creating forecast charts: {e}")
        
        return forecast_paths
    
    def _create_market_dashboard(self, data: Dict[str, pd.DataFrame], 
                               investment_signals: List[Dict[str, Any]],
                               output_dir: Path) -> Optional[Path]:
        """Create comprehensive market dashboard."""
        try:
            logger.info("Creating market dashboard")
            
            dashboard_path = output_dir / "market_dashboard.png"
            
            # Prepare data for dashboard
            dashboard_data = {**data}  # Include all data
            
            # Generate real regime summary from available data
            regime_summary = self._generate_regime_summary(data)
            
            # Generate actionable insights from investment signals
            insights = self._generate_actionable_insights(investment_signals, data)
            
            # Get events data if available
            events_data = self._get_recent_events_data()
            
            self.market_dashboard.create_comprehensive_dashboard(
                dashboard_data,
                regime_summary,
                insights,
                events_data=events_data
            )
            
            logger.info(f"Created market dashboard: {dashboard_path}")
            return dashboard_path
            
        except Exception as e:
            logger.error(f"Error creating market dashboard: {e}")
            return None
    
    def _create_events_analysis(self, data: Dict[str, pd.DataFrame], 
                              output_dir: Path) -> Dict[str, str]:
        """Create events analysis visualizations."""
        events_paths = {}
        
        try:
            # Get events for the analysis period
            symbols = list(data.keys())
            start_date, end_date = self._get_date_range(data)
            
            if start_date and end_date:
                events_data = self.events_manager.get_events_for_symbols(symbols, start_date, end_date)
                
                if not events_data.empty:
                    events_dir = output_dir / "events"
                    events_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create events timeline
                    timeline_path = events_dir / "events_timeline.png"
                    
                    # Create comprehensive events visualizations
                    logger.info(f"Found {len(events_data)} events for visualization")
                    
                    # Create events timeline visualization
                    try:
                        timeline_path = self.events_overlay.create_events_timeline(
                            events_data, 
                            output_dir=str(events_dir)
                        )
                        events_paths['events_timeline'] = timeline_path
                        logger.info(f"Created events timeline: {timeline_path}")
                    except Exception as e:
                        logger.warning(f"Could not create events timeline: {e}")
                    
                    # Create event impact analysis for main symbols
                    if data:
                        for symbol, symbol_data in data.items():
                            # Only create impact analysis for main symbols (not ETFs/indices)
                            if symbol in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']:
                                try:
                                    impact_path = self.events_overlay.create_event_impact_analysis(
                                        symbol, 
                                        symbol_data, 
                                        events_data,
                                        output_dir=str(events_dir)
                                    )
                                    events_paths[f'{symbol}_event_impact'] = impact_path
                                    logger.info(f"Created event impact analysis for {symbol}: {impact_path}")
                                except Exception as e:
                                    logger.warning(f"Could not create event impact analysis for {symbol}: {e}")
                    
                    # Create events summary text file
                    events_summary_path = events_dir / "events_summary.txt"
                    with open(events_summary_path, 'w') as f:
                        f.write("Events Analysis Summary\n")
                        f.write("======================\n")
                        f.write(f"Analysis Period: {start_date} to {end_date}\n")
                        f.write(f"Total Events: {len(events_data)}\n")
                        
                        if 'event_type' in events_data.columns:
                            event_types = events_data['event_type'].value_counts()
                            f.write("\nEvent Types:\n")
                            for event_type, count in event_types.items():
                                f.write(f"  {event_type}: {count}\n")
                        
                        f.write("\nGenerated Visualizations:\n")
                        for viz_name, viz_path in events_paths.items():
                            if viz_name != 'events_summary':
                                f.write(f"  {viz_name}: {viz_path}\n")
                    
                    events_paths['events_summary'] = str(events_summary_path)
                    logger.info(f"Created events analysis summary: {events_summary_path}")
        
        except Exception as e:
            logger.error(f"Error creating events analysis: {e}")
        
        return events_paths
    
    def _generate_regime_summary(self, data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Generate market regime summary from available data."""
        regime_summary = {
            'overall_regime': 'UNKNOWN',
            'yield_curve': 'UNKNOWN', 
            'volatility': 'UNKNOWN',
            'risk_sentiment': 'UNKNOWN',
            'risk_level': 'UNKNOWN'
        }
        
        try:
            # Analyze VIX for volatility regime
            if '^VIX' in data and not data['^VIX'].empty:
                vix_data = data['^VIX']
                if 'Close' in vix_data.columns:
                    current_vix = vix_data['Close'].iloc[-1]
                    
                    if current_vix > 30:
                        regime_summary['volatility'] = 'HIGH'
                        regime_summary['risk_level'] = 'HIGH'
                    elif current_vix > 20:
                        regime_summary['volatility'] = 'MEDIUM'
                        regime_summary['risk_level'] = 'MEDIUM'
                    else:
                        regime_summary['volatility'] = 'LOW'
                        regime_summary['risk_level'] = 'LOW'
            
            # Analyze yield curve
            if '^TNX' in data and '^FVX' in data:
                try:
                    tnx_data = data['^TNX']['Close'].iloc[-1]  # 10Y
                    fvx_data = data['^FVX']['Close'].iloc[-1]  # 5Y
                    spread = tnx_data - fvx_data
                    
                    if spread < 0:
                        regime_summary['yield_curve'] = 'INVERTED'
                    elif spread < 0.5:
                        regime_summary['yield_curve'] = 'FLAT'
                    else:
                        regime_summary['yield_curve'] = 'NORMAL'
                except:
                    pass
            
            # Determine overall regime based on volatility and yield curve
            vol_regime = regime_summary['volatility']
            curve_regime = regime_summary['yield_curve']
            
            if vol_regime == 'HIGH' or curve_regime == 'INVERTED':
                regime_summary['overall_regime'] = 'RISK_OFF'
                regime_summary['risk_sentiment'] = 'BEARISH'
            elif vol_regime == 'LOW' and curve_regime == 'NORMAL':
                regime_summary['overall_regime'] = 'RISK_ON'
                regime_summary['risk_sentiment'] = 'BULLISH'
            else:
                regime_summary['overall_regime'] = 'TRANSITIONAL'
                regime_summary['risk_sentiment'] = 'NEUTRAL'
                
        except Exception as e:
            logger.warning(f"Error generating regime summary: {e}")
            
        return regime_summary
    
    def _generate_actionable_insights(self, investment_signals: List[Dict[str, Any]], 
                                    data: Dict[str, pd.DataFrame]) -> List[str]:
        """Generate actionable insights from investment signals and data."""
        insights = []
        
        try:
            # Analyze signals for insights
            if investment_signals:
                signal_types = {}
                for signal in investment_signals:
                    signal_type = signal.get('signal_type', 'unknown')
                    signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
                
                # Generate insights based on signal patterns
                total_signals = len(investment_signals)
                if total_signals > 0:
                    insights.append(f"Generated {total_signals} investment signals")
                    
                    # Analyze signal composition
                    for signal_type, count in signal_types.items():
                        percentage = (count / total_signals) * 100
                        if percentage > 20:
                            insights.append(f"High frequency of {signal_type} signals ({percentage:.1f}%)")
            
            # Market-specific insights
            if '^VIX' in data:
                try:
                    vix_current = data['^VIX']['Close'].iloc[-1]
                    vix_prev = data['^VIX']['Close'].iloc[-20]  # 20 days ago
                    vix_change = ((vix_current - vix_prev) / vix_prev) * 100
                    
                    if abs(vix_change) > 20:
                        direction = "increased" if vix_change > 0 else "decreased"
                        insights.append(f"VIX has {direction} {abs(vix_change):.1f}% over 20 days")
                        
                        if vix_change > 20:
                            insights.append("Consider defensive positioning due to rising volatility")
                        elif vix_change < -20:
                            insights.append("Volatility declining - potential for risk-on positioning")
                except:
                    pass
            
            # Yield curve insights
            if '^TNX' in data and '^FVX' in data:
                try:
                    tnx_current = data['^TNX']['Close'].iloc[-1]
                    fvx_current = data['^FVX']['Close'].iloc[-1]
                    spread = tnx_current - fvx_current
                    
                    if spread < 0:
                        insights.append("ALERT: Yield curve inverted - recession risk elevated")
                    elif spread < 0.5:
                        insights.append("Yield curve flattening - monitor for inversion")
                    elif spread > 2.0:
                        insights.append("Steep yield curve - favorable for growth/financials")
                except:
                    pass
            
            # Sector performance insights
            sector_etfs = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLU', 'XLB']
            sector_performance = {}
            
            for etf in sector_etfs:
                if etf in data and not data[etf].empty:
                    try:
                        current = data[etf]['Close'].iloc[-1]
                        month_ago = data[etf]['Close'].iloc[-20]
                        ret = ((current - month_ago) / month_ago) * 100
                        sector_performance[etf] = ret
                    except:
                        pass
            
            if sector_performance:
                best_sector = max(sector_performance, key=sector_performance.get)
                worst_sector = min(sector_performance, key=sector_performance.get)
                
                best_return = sector_performance[best_sector]
                worst_return = sector_performance[worst_sector]
                
                if best_return > 5:
                    insights.append(f"Strong sector rotation: {best_sector} leading (+{best_return:.1f}%)")
                if worst_return < -5:
                    insights.append(f"Sector weakness: {worst_sector} lagging ({worst_return:.1f}%)")
            
            # Default insight if none generated
            if not insights:
                insights.append("Market analysis completed - monitor key levels")
                
        except Exception as e:
            logger.warning(f"Error generating insights: {e}")
            insights = ["Market analysis in progress"]
            
        return insights[:8]  # Limit to 8 insights
    
    def _get_recent_events_data(self) -> pd.DataFrame:
        """Get recent events data for dashboard."""
        try:
            # Get events for the last 30 days
            from datetime import datetime, timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            recent_events = self.events_manager.get_events_for_timeframe(start_date, end_date)
            return recent_events if recent_events is not None else pd.DataFrame()
        except Exception as e:
            logger.warning(f"Could not load events data: {e}")
            return pd.DataFrame()
    
    def _get_date_range(self, data: Dict[str, pd.DataFrame]) -> tuple:
        """Get the overall date range from the data."""
        start_date = None
        end_date = None
        
        try:
            for symbol_data in data.values():
                if not symbol_data.empty:
                    if 'Date' in symbol_data.columns:
                        dates = pd.to_datetime(symbol_data['Date'])
                    elif hasattr(symbol_data.index, 'min') and pd.api.types.is_datetime64_any_dtype(symbol_data.index):
                        dates = symbol_data.index
                    else:
                        continue
                    
                    data_start = dates.min().date()
                    data_end = dates.max().date()
                    
                    if start_date is None or data_start < start_date:
                        start_date = data_start
                    if end_date is None or data_end > end_date:
                        end_date = data_end
        
        except Exception as e:
            logger.error(f"Error determining date range: {e}")
        
        return start_date, end_date
    
    def create_performance_summary(self, data: Dict[str, pd.DataFrame], 
                                 predictions: Dict[str, pd.DataFrame],
                                 investment_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a performance summary of the analysis."""
        logger.info("Creating performance summary")
        
        summary = {
            'data_summary': {},
            'prediction_summary': {},
            'signals_summary': {},
            'overall_stats': {}
        }
        
        try:
            # Data summary
            for symbol, symbol_data in data.items():
                if not symbol_data.empty:
                    latest_price = symbol_data['Close'].iloc[-1] if 'Close' in symbol_data.columns else None
                    price_change = None
                    if 'Close' in symbol_data.columns and len(symbol_data) > 1:
                        price_change = ((symbol_data['Close'].iloc[-1] - symbol_data['Close'].iloc[0]) / symbol_data['Close'].iloc[0]) * 100
                    
                    summary['data_summary'][symbol] = {
                        'rows': len(symbol_data),
                        'latest_price': latest_price,
                        'total_return_pct': price_change,
                        'date_range': f"{symbol_data.index[0].strftime('%Y-%m-%d')} to {symbol_data.index[-1].strftime('%Y-%m-%d')}" if hasattr(symbol_data.index, 'strftime') else "Unknown"
                    }
            
            # Prediction summary
            for symbol, pred_data in predictions.items():
                if not pred_data.empty and 'forecast' in pred_data.columns:
                    forecast_values = pred_data['forecast'].dropna()
                    summary['prediction_summary'][symbol] = {
                        'forecast_points': len(forecast_values),
                        'avg_forecast': forecast_values.mean() if len(forecast_values) > 0 else None,
                        'forecast_std': forecast_values.std() if len(forecast_values) > 0 else None
                    }
            
            # Signals summary
            if investment_signals:
                signal_types = {}
                for signal in investment_signals:
                    # Handle both dict and AnomalySignal objects
                    if hasattr(signal, 'signal'):
                        signal_type = signal.signal
                    elif hasattr(signal, 'anomaly_type'):
                        signal_type = signal.anomaly_type
                    elif isinstance(signal, dict):
                        signal_type = signal.get('signal_type', 'unknown')
                    else:
                        signal_type = 'unknown'
                    signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
                
                summary['signals_summary'] = {
                    'total_signals': len(investment_signals),
                    'signal_types': signal_types
                }
            
            # Overall stats
            summary['overall_stats'] = {
                'symbols_analyzed': len(data),
                'symbols_with_predictions': len(predictions),
                'total_signals': len(investment_signals),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error creating performance summary: {e}")
        
        return summary