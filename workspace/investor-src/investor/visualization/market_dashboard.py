"""
Market Dashboard - Single-page comprehensive market overview for quants.
Focus on essential signals: regime, cross-asset performance, sector rotation.
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MarketDashboard:
    """
    Create comprehensive single-page market dashboard with essential information.
    Designed for quick market assessment by quantitative traders.
    """
    
    def __init__(self, figsize: tuple = (20, 12)):
        """Initialize market dashboard."""
        self.figsize = figsize
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Color scheme for consistent visualization
        self.colors = {
            'positive': '#2E8B57',  # Sea green
            'negative': '#DC143C',  # Crimson
            'neutral': '#4682B4',   # Steel blue
            'warning': '#FF8C00',   # Dark orange
            'critical': '#B22222',  # Fire brick
            'background': '#F5F5F5' # White smoke
        }
    
    def create_comprehensive_dashboard(self, 
                                    market_data: Dict[str, pd.DataFrame],
                                    regime_summary: Dict[str, str],
                                    insights: List[str],
                                    events_data: Optional[pd.DataFrame] = None,
                                    output_dir: str = "outputs/latest_run/forecasting/charts") -> str:
        """
        Create comprehensive market dashboard.
        
        Args:
            market_data: Dictionary with asset data (SPY, TLT, GLD, VIX, etc.)
            regime_summary: Market regime summary
            insights: List of actionable insights
            
        Returns:
            Path to saved dashboard image
        """
        try:
            # Create figure with custom grid layout
            fig = plt.figure(figsize=self.figsize, facecolor=self.colors['background'])
            gs = gridspec.GridSpec(5, 4, figure=fig, hspace=0.3, wspace=0.3)
            
            # Title with timestamp
            fig.suptitle(f'Market Dashboard - {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                        fontsize=20, fontweight='bold', y=0.95)
            
            # 1. Market Regime Panel (Top Left)
            self._plot_regime_panel(fig, gs[0, :2], regime_summary)
            
            # 2. Cross-Asset Performance Heatmap (Top Right)
            self._plot_performance_heatmap(fig, gs[0, 2:], market_data)
            
            # 3. Yield Curve & VIX (Second Row Left)
            self._plot_yield_curve_vix(fig, gs[1, :2], market_data)
            
            # 4. Sector Rotation (Second Row Right)
            self._plot_sector_rotation(fig, gs[1, 2:], market_data)
            
            # 5. Cross-Asset Correlations (Third Row Left)
            self._plot_correlations(fig, gs[2, :2], market_data)
            
            # 6. Risk Metrics (Third Row Right)
            self._plot_risk_metrics(fig, gs[2, 2:], market_data)
            
            # 7. Event Impact Analysis (Fourth Row)
            if events_data is not None and not events_data.empty:
                self._plot_event_impact_analysis(fig, gs[3, :], events_data, market_data)
            
            # 8. Key Insights Panel (Bottom)
            self._plot_insights_panel(fig, gs[4, :], insights, regime_summary)
            
            # Save dashboard
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_dashboard_{timestamp}.png"
            
            # Ensure output directory exists
            import os
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                       facecolor=self.colors['background'], edgecolor='none')
            plt.close()
            
            logger.info(f"Market dashboard saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating market dashboard: {e}")
            return ""
    
    def _plot_regime_panel(self, fig, gs_position, regime_summary: Dict[str, str]):
        """Plot market regime summary panel."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('MARKET REGIME ANALYSIS', fontweight='bold', fontsize=14)
        
        # Create regime status boxes
        regime_info = [
            ('Overall', regime_summary.get('overall_regime', 'UNKNOWN')),
            ('Yield Curve', regime_summary.get('yield_curve', 'UNKNOWN')),
            ('Volatility', regime_summary.get('volatility', 'UNKNOWN')),
            ('Risk Sentiment', regime_summary.get('risk_sentiment', 'UNKNOWN'))
        ]
        
        y_positions = np.linspace(0.8, 0.2, len(regime_info))
        
        for i, (label, value) in enumerate(regime_info):
            # Color coding based on value
            if 'HIGH' in value or 'INVERTED' in value or 'RISK_OFF' in value:
                color = self.colors['critical']
            elif 'MEDIUM' in value or 'FLAT' in value:
                color = self.colors['warning']
            else:
                color = self.colors['positive']
            
            # Create colored box
            bbox = dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7)
            ax.text(0.1, y_positions[i], label, fontweight='bold', fontsize=11)
            ax.text(0.6, y_positions[i], value, fontweight='bold', fontsize=11,
                   bbox=bbox, color='white')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    def _plot_performance_heatmap(self, fig, gs_position, market_data: Dict[str, pd.DataFrame]):
        """Plot cross-asset performance heatmap."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('CROSS-ASSET PERFORMANCE', fontweight='bold', fontsize=14)
        
        try:
            # Calculate returns for different timeframes
            performance_data = []
            # Use available assets from the data, prioritizing key market indicators
            preferred_assets = ['SPY', 'QQQ', 'TLT', 'GLD', '^VIX', 'AAPL', 'MSFT', 'XLK', 'XLF']
            assets = []
            
            # Select up to 5 available assets for the heatmap
            for asset in preferred_assets:
                if asset in market_data and not market_data[asset].empty:
                    assets.append(asset)
                    if len(assets) >= 5:
                        break
            
            # If we don't have preferred assets, use any available assets
            if len(assets) < 3:
                available_assets = [k for k in market_data.keys() if not market_data[k].empty]
                for asset in available_assets[:5]:
                    if asset not in assets:
                        assets.append(asset)
                        if len(assets) >= 5:
                            break
            
            timeframes = ['1D', '1W', '1M', '3M']
            
            perf_matrix = np.zeros((len(assets), len(timeframes)))
            
            for i, asset in enumerate(assets):
                if asset in market_data and not market_data[asset].empty:
                    data = market_data[asset]
                    if 'Close' in data.columns:
                        prices = data['Close'].dropna()
                        
                        if len(prices) > 0:
                            # Calculate returns for different periods
                            current = prices.iloc[-1]
                            
                            for j, period in enumerate([1, 5, 20, 60]):  # 1D, 1W, 1M, 3M
                                if len(prices) > period:
                                    past = prices.iloc[-period-1]
                                    ret = (current - past) / past * 100
                                    perf_matrix[i, j] = ret
            
            # Create heatmap
            sns.heatmap(perf_matrix, 
                       xticklabels=timeframes,
                       yticklabels=assets,
                       annot=True, 
                       fmt='.1f',
                       cmap='RdYlGn',
                       center=0,
                       ax=ax,
                       cbar_kws={'label': 'Return (%)'})
            
        except Exception as e:
            logger.warning(f"Error creating performance heatmap: {e}")
            ax.text(0.5, 0.5, 'Performance data unavailable', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_yield_curve_vix(self, fig, gs_position, market_data: Dict[str, pd.DataFrame]):
        """Plot yield curve slope and VIX."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('YIELD CURVE & VOLATILITY', fontweight='bold', fontsize=14)
        
        try:
            # Create dual y-axis plot
            ax2 = ax.twinx()
            
            # Plot yield curve slope if available
            if 'yield_curve_slope' in market_data:
                slope_data = market_data['yield_curve_slope'].dropna()
                if not slope_data.empty:
                    ax.plot(slope_data.index[-60:], slope_data.iloc[-60:], 
                           color=self.colors['neutral'], linewidth=2, label='10Y-2Y Spread')
                    ax.axhline(y=0, color=self.colors['critical'], 
                              linestyle='--', alpha=0.7, label='Inversion Line')
                    ax.set_ylabel('Yield Spread (%)', color=self.colors['neutral'])
                    ax.tick_params(axis='y', labelcolor=self.colors['neutral'])
            
            # Plot VIX if available (check different VIX symbol formats)
            vix_data = None
            for vix_symbol in ['^VIX', 'VIX', 'VIXCLS']:
                if vix_symbol in market_data and not market_data[vix_symbol].empty:
                    vix_df = market_data[vix_symbol]
                    
                    # Handle different VIX data formats
                    if 'Close' in vix_df.columns:
                        vix_data = vix_df['Close'].dropna()
                    elif 'VIX' in vix_df.columns:
                        vix_data = vix_df['VIX'].dropna()
                    elif len(vix_df.columns) > 0:
                        vix_data = vix_df.iloc[:, 0].dropna()
                    break
            
            if vix_data is not None and not vix_data.empty:
                ax2.plot(vix_data.index[-60:], vix_data.iloc[-60:], 
                        color=self.colors['warning'], linewidth=2, label='VIX')
                ax2.axhline(y=20, color=self.colors['positive'], 
                           linestyle='--', alpha=0.5, label='Low Vol')
                ax2.axhline(y=30, color=self.colors['critical'], 
                           linestyle='--', alpha=0.5, label='High Vol')
                ax2.set_ylabel('VIX Level', color=self.colors['warning'])
                ax2.tick_params(axis='y', labelcolor=self.colors['warning'])
                
                # Add current VIX level text
                current_vix = vix_data.iloc[-1]
                vix_color = (self.colors['critical'] if current_vix > 30 else 
                           self.colors['warning'] if current_vix > 20 else 
                           self.colors['positive'])
                ax2.text(0.98, 0.98, f'VIX: {current_vix:.1f}', 
                        transform=ax2.transAxes, verticalalignment='top',
                        horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor=vix_color, alpha=0.8),
                        color='white', fontweight='bold', fontsize=10)
            
            # Calculate and display yield curve slope if treasury data available
            tnx_data = market_data.get('^TNX')  # 10Y Treasury
            fvx_data = market_data.get('^FVX')  # 5Y Treasury
            
            if tnx_data is not None and fvx_data is not None:
                try:
                    tnx_close = tnx_data['Close'].dropna()
                    fvx_close = fvx_data['Close'].dropna()
                    
                    if not tnx_close.empty and not fvx_close.empty:
                        # Align dates and calculate spread
                        common_dates = tnx_close.index.intersection(fvx_close.index)
                        if len(common_dates) > 0:
                            spread = tnx_close.loc[common_dates] - fvx_close.loc[common_dates]
                            
                            if len(spread) > 0:
                                current_spread = spread.iloc[-1]
                                spread_color = (self.colors['negative'] if current_spread < 0 else 
                                              self.colors['positive'])
                                
                                ax.text(0.02, 0.98, f'10Y-5Y: {current_spread:.2f}%', 
                                       transform=ax.transAxes, verticalalignment='top',
                                       bbox=dict(boxstyle='round', facecolor=spread_color, alpha=0.8),
                                       color='white', fontweight='bold', fontsize=10)
                except Exception as e:
                    logger.warning(f"Error calculating yield spread: {e}")
            
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left')
            if 'VIX' in market_data:
                ax2.legend(loc='upper right')
            
        except Exception as e:
            logger.warning(f"Error plotting yield curve/VIX: {e}")
            ax.text(0.5, 0.5, 'Yield curve/VIX data unavailable', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_sector_rotation(self, fig, gs_position, market_data: Dict[str, pd.DataFrame]):
        """Plot sector rotation analysis."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('SECTOR ROTATION (1M Performance)', fontweight='bold', fontsize=14)
        
        try:
            # Sector ETFs for rotation analysis
            sectors = {
                'XLK': 'Technology',
                'XLF': 'Financials', 
                'XLE': 'Energy',
                'XLV': 'Healthcare',
                'XLI': 'Industrials',
                'XLP': 'Staples',
                'XLU': 'Utilities',
                'XLB': 'Materials'
            }
            
            sector_returns = {}
            
            for etf, name in sectors.items():
                if etf in market_data and not market_data[etf].empty:
                    data = market_data[etf]
                    if 'Close' in data.columns:
                        prices = data['Close'].dropna()
                        if len(prices) > 20:  # 1 month
                            ret = (prices.iloc[-1] - prices.iloc[-21]) / prices.iloc[-21] * 100
                            sector_returns[name] = ret
            
            if sector_returns:
                # Create horizontal bar chart
                sectors_sorted = sorted(sector_returns.items(), key=lambda x: x[1], reverse=True)
                names, returns = zip(*sectors_sorted)
                
                colors = [self.colors['positive'] if r > 0 else self.colors['negative'] for r in returns]
                
                bars = ax.barh(names, returns, color=colors, alpha=0.7)
                ax.set_xlabel('1-Month Return (%)')
                ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
                
                # Add value labels on bars
                for bar, value in zip(bars, returns):
                    width = bar.get_width()
                    ax.text(width + (0.1 if width > 0 else -0.1), bar.get_y() + bar.get_height()/2,
                           f'{value:.1f}%', ha='left' if width > 0 else 'right', va='center')
            else:
                ax.text(0.5, 0.5, 'Sector data unavailable', 
                       ha='center', va='center', transform=ax.transAxes)
                
        except Exception as e:
            logger.warning(f"Error plotting sector rotation: {e}")
            ax.text(0.5, 0.5, 'Sector rotation data unavailable', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_correlations(self, fig, gs_position, market_data: Dict[str, pd.DataFrame]):
        """Plot key cross-asset correlations."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('KEY CORRELATIONS (60-Day)', fontweight='bold', fontsize=14)
        
        try:
            # Calculate key correlations
            correlations = {}
            
            # Get return series for available assets
            returns_data = {}
            correlation_assets = ['SPY', 'TLT', 'GLD', '^VIX', 'AAPL', 'MSFT', 'XLK', 'XLF']
            
            for asset in correlation_assets:
                if asset in market_data and not market_data[asset].empty:
                    data = market_data[asset]
                    if 'Close' in data.columns:
                        returns = data['Close'].pct_change().dropna()
                        returns_data[asset] = returns
                        if len(returns_data) >= 4:  # Limit to 4 assets for clarity
                            break
            
            # Calculate specific correlations of interest using available assets
            asset_names = list(returns_data.keys())
            
            # Find stock proxy (prefer SPY, then AAPL/MSFT)
            stock_proxy = None
            for asset in ['SPY', 'AAPL', 'MSFT', 'XLK']:
                if asset in returns_data:
                    stock_proxy = asset
                    break
            
            if stock_proxy and len(asset_names) >= 2:
                for i, other_asset in enumerate(asset_names):
                    if other_asset != stock_proxy and len(correlations) < 3:
                        try:
                            corr = returns_data[stock_proxy].rolling(60).corr(returns_data[other_asset]).iloc[-1]
                            if not pd.isna(corr):
                                correlations[f'{stock_proxy}-{other_asset}'] = corr
                        except:
                            pass
            
            if correlations:
                # Create correlation bar chart
                names = list(correlations.keys())
                values = list(correlations.values())
                
                colors = []
                for v in values:
                    if abs(v) > 0.5:
                        colors.append(self.colors['critical'])
                    elif abs(v) > 0.3:
                        colors.append(self.colors['warning'])
                    else:
                        colors.append(self.colors['neutral'])
                
                bars = ax.bar(names, values, color=colors, alpha=0.7)
                ax.set_ylabel('Correlation')
                ax.set_ylim(-1, 1)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                ax.axhline(y=0.5, color=self.colors['warning'], linestyle='--', alpha=0.5)
                ax.axhline(y=-0.5, color=self.colors['warning'], linestyle='--', alpha=0.5)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + (0.02 if height > 0 else -0.05),
                           f'{value:.2f}', ha='center', va='bottom' if height > 0 else 'top')
            else:
                ax.text(0.5, 0.5, 'Correlation data unavailable', 
                       ha='center', va='center', transform=ax.transAxes)
                
        except Exception as e:
            logger.warning(f"Error plotting correlations: {e}")
            ax.text(0.5, 0.5, 'Correlation calculation error', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_risk_metrics(self, fig, gs_position, market_data: Dict[str, pd.DataFrame]):
        """Plot key risk metrics."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('RISK METRICS', fontweight='bold', fontsize=14)
        
        try:
            risk_metrics = {}
            
            # Calculate risk metrics for available stock data (prefer SPY, then others)
            stock_data = None
            stock_symbol = None
            
            for asset in ['SPY', 'AAPL', 'MSFT', 'QQQ', 'XLK']:
                if asset in market_data and not market_data[asset].empty:
                    if 'Close' in market_data[asset].columns:
                        stock_data = market_data[asset]
                        stock_symbol = asset
                        break
            
            if stock_data is not None:
                returns = stock_data['Close'].pct_change().dropna()
                
                # Recent volatility (annualized)
                recent_vol = returns.tail(20).std() * np.sqrt(252) * 100
                risk_metrics[f'20D Vol % ({stock_symbol})'] = recent_vol
                
                # Maximum drawdown (last 60 days)
                prices = stock_data['Close'].tail(60)
                cumulative = (1 + returns.tail(60)).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_dd = drawdown.min() * 100
                risk_metrics[f'Max DD % ({stock_symbol})'] = abs(max_dd)
                
                # Sharpe ratio (last 60 days, assuming 2% risk-free rate)
                avg_return = returns.tail(60).mean() * 252
                vol = returns.tail(60).std() * np.sqrt(252)
                sharpe = (avg_return - 0.02) / vol if vol > 0 else 0
                risk_metrics[f'Sharpe ({stock_symbol})'] = sharpe
            
            if risk_metrics:
                # Create metrics display
                y_pos = 0.8
                for metric, value in risk_metrics.items():
                    # Color coding for risk levels
                    if 'Vol' in metric:
                        color = self.colors['critical'] if value > 25 else self.colors['warning'] if value > 15 else self.colors['positive']
                    elif 'DD' in metric:
                        color = self.colors['critical'] if value > 10 else self.colors['warning'] if value > 5 else self.colors['positive']
                    elif 'Sharpe' in metric:
                        color = self.colors['positive'] if value > 1 else self.colors['warning'] if value > 0 else self.colors['critical']
                    else:
                        color = self.colors['neutral']
                    
                    ax.text(0.1, y_pos, metric, fontweight='bold', fontsize=12)
                    ax.text(0.7, y_pos, f'{value:.2f}', fontweight='bold', fontsize=12, color=color)
                    y_pos -= 0.2
            else:
                ax.text(0.5, 0.5, 'Risk metrics unavailable', 
                       ha='center', va='center', transform=ax.transAxes)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
        except Exception as e:
            logger.warning(f"Error plotting risk metrics: {e}")
            ax.text(0.5, 0.5, 'Risk metrics calculation error', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_event_impact_analysis(self, fig, gs_position, events_data: pd.DataFrame, market_data: Dict[str, pd.DataFrame]):
        """Plot event impact analysis panel."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('EVENT IMPACT ANALYSIS', fontweight='bold', fontsize=14)
        
        try:
            # Get recent events (last 30 days)
            recent_date = datetime.now() - timedelta(days=30)
            
            # Filter events data
            if 'date' in events_data.columns:
                events_data['date'] = pd.to_datetime(events_data['date'])
                recent_events = events_data[events_data['date'] >= recent_date].copy()
            else:
                recent_events = events_data.copy()
            
            if recent_events.empty:
                ax.text(0.5, 0.5, 'No recent events to analyze', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.axis('off')
                return
            
            # Sort by date and take most recent events
            recent_events = recent_events.sort_values('date', ascending=False).head(8)
            
            # Create event impact visualization
            event_impacts = []
            event_labels = []
            severity_colors = []
            
            for _, event in recent_events.iterrows():
                # Calculate estimated market impact
                severity = event.get('severity', 'medium')
                category = event.get('category', 'market_events')
                title = event.get('title', 'Unknown Event')
                
                # Simple impact scoring based on severity and category
                impact_score = self._calculate_event_impact_score(severity, category)
                
                event_impacts.append(impact_score)
                event_labels.append(f"{title[:25]}..." if len(title) > 25 else title)
                
                # Color based on severity
                if severity == 'critical':
                    severity_colors.append(self.colors['critical'])
                elif severity == 'high':
                    severity_colors.append(self.colors['warning'])
                elif severity == 'medium':
                    severity_colors.append(self.colors['neutral'])
                else:
                    severity_colors.append(self.colors['positive'])
            
            # Create horizontal bar chart
            y_pos = np.arange(len(event_labels))
            bars = ax.barh(y_pos, event_impacts, color=severity_colors, alpha=0.7)
            
            # Customize chart
            ax.set_yticks(y_pos)
            ax.set_yticklabels(event_labels, fontsize=8)
            ax.set_xlabel('Estimated Market Impact', fontsize=10)
            ax.set_xlim(0, 1)
            
            # Add impact score labels
            for i, (bar, score) in enumerate(zip(bars, event_impacts)):
                ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                       f'{score:.2f}', ha='left', va='center', fontsize=8)
            
            # Add severity legend
            severity_legend = {
                'Critical': self.colors['critical'],
                'High': self.colors['warning'],
                'Medium': self.colors['neutral'],
                'Low': self.colors['positive']
            }
            
            legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7) 
                             for color in severity_legend.values()]
            ax.legend(legend_elements, severity_legend.keys(), 
                     loc='lower right', fontsize=8, title='Severity')
            
            ax.grid(True, alpha=0.3, axis='x')
            ax.invert_yaxis()  # Most recent events at top
            
        except Exception as e:
            logger.warning(f"Error plotting event impact analysis: {e}")
            ax.text(0.5, 0.5, 'Event impact analysis error', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')
    
    def _calculate_event_impact_score(self, severity: str, category: str) -> float:
        """Calculate estimated market impact score for an event."""
        # Base score by severity
        severity_scores = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }
        
        # Category multipliers
        category_multipliers = {
            'economic': 1.2,
            'market_events': 1.1,
            'political': 1.0,
            'earnings': 0.8,
            'natural_disasters': 0.9
        }
        
        base_score = severity_scores.get(severity.lower(), 0.5)
        multiplier = category_multipliers.get(category.lower(), 1.0)
        
        return min(1.0, base_score * multiplier)
    
    def _plot_insights_panel(self, fig, gs_position, insights: List[str], regime_summary: Dict[str, str]):
        """Plot actionable insights panel."""
        ax = fig.add_subplot(gs_position)
        ax.set_title('ACTIONABLE INSIGHTS', fontweight='bold', fontsize=14)
        
        # Display key insights
        insight_text = "\\n".join(insights[:8])  # Show top 8 insights
        
        if not insight_text.strip():
            insight_text = "No specific insights generated"
        
        # Add regime summary
        risk_level = regime_summary.get('risk_level', 'UNKNOWN')
        overall_regime = regime_summary.get('overall_regime', 'UNKNOWN')
        
        header_text = f"CURRENT REGIME: {overall_regime} (Risk Level: {risk_level})\\n\\n"
        full_text = header_text + insight_text
        
        ax.text(0.05, 0.95, full_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')