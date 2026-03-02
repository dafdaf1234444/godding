"""
Options-specific visualization components for volatility surfaces, Greeks, and option analysis.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
import logging

from ..models.options_pricing import VolatilitySurface

logger = logging.getLogger(__name__)


class OptionsVisualizationManager:
    """Manager for creating options-related visualizations."""
    
    def __init__(self, style: str = 'seaborn-v0_8', figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize options visualization manager.
        
        Args:
            style: Matplotlib style
            figsize: Default figure size
        """
        self.style = style
        self.figsize = figsize
        self.setup_style()
    
    def setup_style(self):
        """Setup matplotlib style and parameters."""
        try:
            plt.style.use(self.style)
        except OSError:
            plt.style.use('default')
        
        plt.rcParams.update({
            'figure.figsize': self.figsize,
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 14
        })
    
    def create_volatility_surface_3d(self, vol_surface: VolatilitySurface, 
                                   save_path: Optional[str] = None) -> plt.Figure:
        """
        Create 3D volatility surface plot.
        
        Args:
            vol_surface: VolatilitySurface object
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig = plt.figure(figsize=(14, 10))
        
        # Get surface data
        surface_data = vol_surface.get_surface_grid()
        
        if not surface_data or 'interpolated_surface' not in surface_data:
            # Fallback to scatter plot if interpolation failed
            return self._create_volatility_scatter(vol_surface, fig, save_path)
        
        ax = fig.add_subplot(111, projection='3d')
        
        # Create meshgrid
        M, T = np.meshgrid(surface_data['moneyness_grid'], surface_data['time_grid'])
        Z = surface_data['interpolated_surface']
        
        # Remove NaN values for plotting
        mask = ~np.isnan(Z)
        if not mask.any():
            return self._create_volatility_scatter(vol_surface, fig, save_path)
        
        # Create surface plot
        surf = ax.plot_surface(M, T, Z, cmap='viridis', alpha=0.8, 
                              linewidth=0, antialiased=True)
        
        # Add actual data points
        surface_points = surface_data['surface_points']
        if surface_points:
            points_df = pd.DataFrame(surface_points)
            calls = points_df[points_df['option_type'] == 'call']
            puts = points_df[points_df['option_type'] == 'put']
            
            if not calls.empty:
                ax.scatter(calls['moneyness'], calls['time_to_expiration'], 
                          calls['implied_volatility'], c='red', s=20, alpha=0.6, label='Calls')
            
            if not puts.empty:
                ax.scatter(puts['moneyness'], puts['time_to_expiration'], 
                          puts['implied_volatility'], c='blue', s=20, alpha=0.6, label='Puts')
        
        # Customize plot
        ax.set_xlabel('Moneyness (Strike/Spot)')
        ax.set_ylabel('Time to Expiration (Years)')
        ax.set_zlabel('Implied Volatility')
        ax.set_title('Options Implied Volatility Surface')
        
        # Add color bar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Implied Volatility')
        
        if surface_points:
            ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Volatility surface saved to {save_path}")
        
        return fig
    
    def _create_volatility_scatter(self, vol_surface: VolatilitySurface, 
                                 fig: plt.Figure, save_path: Optional[str] = None) -> plt.Figure:
        """Create scatter plot when surface interpolation fails."""
        fig.clear()
        ax = fig.add_subplot(111, projection='3d')
        
        if vol_surface.surface_data is not None and not vol_surface.surface_data.empty:
            data = vol_surface.surface_data
            
            calls = data[data['option_type'] == 'call']
            puts = data[data['option_type'] == 'put']
            
            if not calls.empty:
                ax.scatter(calls['moneyness'], calls['time_to_expiration'], 
                          calls['implied_volatility'], c='red', s=30, alpha=0.7, label='Calls')
            
            if not puts.empty:
                ax.scatter(puts['moneyness'], puts['time_to_expiration'], 
                          puts['implied_volatility'], c='blue', s=30, alpha=0.7, label='Puts')
            
            ax.set_xlabel('Moneyness (Strike/Spot)')
            ax.set_ylabel('Time to Expiration (Years)')
            ax.set_zlabel('Implied Volatility')
            ax.set_title('Options Implied Volatility (Scatter Plot)')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 0.5, 'No volatility data available', 
                   transform=ax.transAxes, ha='center', va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_volatility_term_structure(self, vol_surface: VolatilitySurface,
                                       moneyness_levels: List[float] = [0.9, 1.0, 1.1],
                                       save_path: Optional[str] = None) -> plt.Figure:
        """
        Create volatility term structure plot for different moneyness levels.
        
        Args:
            vol_surface: VolatilitySurface object
            moneyness_levels: List of moneyness levels to plot
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        
        for i, moneyness in enumerate(moneyness_levels):
            term_structure = vol_surface.get_term_structure(moneyness)
            
            if not term_structure.empty:
                color = colors[i % len(colors)]
                ax.plot(term_structure['time_to_expiration'], 
                       term_structure['implied_volatility'],
                       marker='o', color=color, linewidth=2, markersize=6,
                       label=f'Moneyness = {moneyness:.1f}')
        
        ax.set_xlabel('Time to Expiration (Years)')
        ax.set_ylabel('Implied Volatility')
        ax.set_title('Volatility Term Structure by Moneyness')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis to show time labels nicely
        ax.set_xlim(left=0)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Term structure plot saved to {save_path}")
        
        return fig
    
    def create_volatility_skew_plot(self, vol_surface: VolatilitySurface,
                                  expiration_dates: Optional[List[str]] = None,
                                  save_path: Optional[str] = None) -> plt.Figure:
        """
        Create volatility skew plot for different expiration dates.
        
        Args:
            vol_surface: VolatilitySurface object
            expiration_dates: List of expiration dates to plot (if None, use all available)
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if vol_surface.surface_data is None or vol_surface.surface_data.empty:
            ax.text(0.5, 0.5, 'No volatility data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Get available expiration dates
        if expiration_dates is None:
            expiration_dates = sorted(vol_surface.surface_data['expiration'].unique())[:5]  # Limit to 5 dates
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(expiration_dates)))
        
        for i, exp_date in enumerate(expiration_dates):
            skew_data = vol_surface.calculate_volatility_skew(exp_date)
            
            if not skew_data.empty:
                # Separate calls and puts
                calls = skew_data[skew_data['option_type'] == 'call']
                puts = skew_data[skew_data['option_type'] == 'put']
                
                color = colors[i]
                
                if not calls.empty:
                    ax.scatter(calls['moneyness'], calls['implied_volatility'], 
                             color=color, marker='o', s=30, alpha=0.7,
                             label=f'{exp_date} (C)')
                
                if not puts.empty:
                    ax.scatter(puts['moneyness'], puts['implied_volatility'], 
                             color=color, marker='^', s=30, alpha=0.7,
                             label=f'{exp_date} (P)')
                
                # Fit a curve through all points for this expiration
                all_points = pd.concat([calls, puts]).sort_values('moneyness')
                if len(all_points) > 2:
                    ax.plot(all_points['moneyness'], all_points['implied_volatility'],
                           color=color, alpha=0.5, linewidth=1)
        
        # Add vertical line at ATM
        ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, label='ATM')
        
        ax.set_xlabel('Moneyness (Strike/Spot)')
        ax.set_ylabel('Implied Volatility')
        ax.set_title('Volatility Skew by Expiration')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Volatility skew plot saved to {save_path}")
        
        return fig
    
    def create_greeks_heatmap(self, options_data: pd.DataFrame, 
                            greek: str = 'delta',
                            save_path: Optional[str] = None) -> plt.Figure:
        """
        Create heatmap of Greeks across strikes and expirations.
        
        Args:
            options_data: DataFrame with options data
            greek: Which Greek to plot ('delta', 'gamma', 'theta', 'vega', 'rho')
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        if options_data.empty or greek not in options_data.columns:
            for ax in [ax1, ax2]:
                ax.text(0.5, 0.5, f'No {greek} data available', 
                       transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Create pivot tables for calls and puts
        calls_data = options_data[options_data['option_type'] == 'call']
        puts_data = options_data[options_data['option_type'] == 'put']
        
        for data, ax, title in [(calls_data, ax1, 'Call Options'), (puts_data, ax2, 'Put Options')]:
            if not data.empty:
                # Create pivot table
                pivot_data = data.pivot_table(
                    values=greek, 
                    index='strike', 
                    columns='expiration', 
                    aggfunc='mean'
                )
                
                if not pivot_data.empty:
                    # Create heatmap
                    sns.heatmap(pivot_data, annot=True, fmt='.3f', cmap='RdYlBu_r', 
                               center=0, ax=ax, cbar_kws={'label': greek.capitalize()})
                    ax.set_title(f'{title} - {greek.capitalize()}')
                    ax.set_xlabel('Expiration Date')
                    ax.set_ylabel('Strike Price')
                else:
                    ax.text(0.5, 0.5, f'No {greek} data for {title.lower()}', 
                           transform=ax.transAxes, ha='center', va='center')
            else:
                ax.text(0.5, 0.5, f'No {title.lower()} data', 
                       transform=ax.transAxes, ha='center', va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Greeks heatmap saved to {save_path}")
        
        return fig
    
    def create_options_pnl_surface(self, options_data: pd.DataFrame, 
                                 price_range: Tuple[float, float],
                                 current_price: float,
                                 save_path: Optional[str] = None) -> plt.Figure:
        """
        Create P&L surface for options position at expiration.
        
        Args:
            options_data: DataFrame with options positions
            price_range: (min_price, max_price) for P&L calculation
            current_price: Current underlying price
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if options_data.empty:
            ax.text(0.5, 0.5, 'No options data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Create price range
        prices = np.linspace(price_range[0], price_range[1], 100)
        
        # Calculate P&L for each expiration date
        expiration_dates = sorted(options_data['expiration'].unique())
        colors = plt.cm.viridis(np.linspace(0, 1, len(expiration_dates)))
        
        for i, exp_date in enumerate(expiration_dates):
            exp_options = options_data[options_data['expiration'] == exp_date]
            
            total_pnl = np.zeros_like(prices)
            
            for _, option in exp_options.iterrows():
                strike = option['strike']
                option_type = option['option_type']
                position_size = option.get('position_size', 1)  # Default to 1 if not specified
                premium_paid = option.get('last_price', 0)
                
                if option_type == 'call':
                    # Call P&L at expiration
                    option_pnl = np.maximum(prices - strike, 0) - premium_paid
                else:
                    # Put P&L at expiration
                    option_pnl = np.maximum(strike - prices, 0) - premium_paid
                
                total_pnl += option_pnl * position_size
            
            # Plot P&L curve
            ax.plot(prices, total_pnl, color=colors[i], linewidth=2, 
                   label=f'Expiration: {exp_date}')
        
        # Add breakeven line
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Breakeven')
        ax.axvline(x=current_price, color='green', linestyle='--', alpha=0.5, label='Current Price')
        
        ax.set_xlabel('Underlying Price at Expiration')
        ax.set_ylabel('Profit/Loss')
        ax.set_title('Options Position P&L at Expiration')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Color profit areas green and loss areas red
        ax.fill_between(prices, total_pnl, 0, where=(total_pnl >= 0), 
                       color='green', alpha=0.2, interpolate=True)
        ax.fill_between(prices, total_pnl, 0, where=(total_pnl < 0), 
                       color='red', alpha=0.2, interpolate=True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"P&L surface saved to {save_path}")
        
        return fig
    
    def create_options_chain_summary(self, options_data: pd.DataFrame,
                                   save_path: Optional[str] = None) -> plt.Figure:
        """
        Create comprehensive options chain summary visualization.
        
        Args:
            options_data: DataFrame with options data
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig = plt.figure(figsize=(16, 12))
        
        if options_data.empty:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No options data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Create subplots
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], hspace=0.3, wspace=0.3)
        
        # 1. Volume by strike (calls vs puts)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_volume_by_strike(options_data, ax1)
        
        # 2. Open interest by strike
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_open_interest_by_strike(options_data, ax2)
        
        # 3. Implied volatility smile
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_iv_smile(options_data, ax3)
        
        # 4. Time value by moneyness
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_time_value(options_data, ax4)
        
        # 5. Greeks summary (delta and gamma)
        ax5 = fig.add_subplot(gs[2, :])
        self._plot_greeks_summary(options_data, ax5)
        
        plt.suptitle('Options Chain Analysis', fontsize=16, y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Options chain summary saved to {save_path}")
        
        return fig
    
    def _plot_volume_by_strike(self, data: pd.DataFrame, ax: plt.Axes):
        """Plot volume by strike for calls and puts."""
        if 'volume' not in data.columns or 'strike' not in data.columns:
            ax.text(0.5, 0.5, 'Volume data not available', transform=ax.transAxes, ha='center')
            return
        
        calls = data[data['option_type'] == 'call'].groupby('strike')['volume'].sum()
        puts = data[data['option_type'] == 'put'].groupby('strike')['volume'].sum()
        
        if not calls.empty:
            ax.bar(calls.index, calls.values, alpha=0.7, color='green', label='Calls', width=1)
        if not puts.empty:
            ax.bar(puts.index, -puts.values, alpha=0.7, color='red', label='Puts', width=1)
        
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Volume')
        ax.set_title('Volume by Strike (Calls vs Puts)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_open_interest_by_strike(self, data: pd.DataFrame, ax: plt.Axes):
        """Plot open interest by strike."""
        if 'open_interest' not in data.columns or 'strike' not in data.columns:
            ax.text(0.5, 0.5, 'Open interest data not available', transform=ax.transAxes, ha='center')
            return
        
        calls = data[data['option_type'] == 'call'].groupby('strike')['open_interest'].sum()
        puts = data[data['option_type'] == 'put'].groupby('strike')['open_interest'].sum()
        
        if not calls.empty:
            ax.bar(calls.index, calls.values, alpha=0.7, color='blue', label='Calls', width=1)
        if not puts.empty:
            ax.bar(puts.index, -puts.values, alpha=0.7, color='orange', label='Puts', width=1)
        
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Open Interest')
        ax.set_title('Open Interest by Strike')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_iv_smile(self, data: pd.DataFrame, ax: plt.Axes):
        """Plot implied volatility smile."""
        if 'implied_volatility' not in data.columns or 'moneyness' not in data.columns:
            ax.text(0.5, 0.5, 'IV data not available', transform=ax.transAxes, ha='center')
            return
        
        calls = data[data['option_type'] == 'call']
        puts = data[data['option_type'] == 'put']
        
        if not calls.empty:
            ax.scatter(calls['moneyness'], calls['implied_volatility'], 
                      color='green', alpha=0.7, s=30, label='Calls')
        if not puts.empty:
            ax.scatter(puts['moneyness'], puts['implied_volatility'], 
                      color='red', alpha=0.7, s=30, label='Puts')
        
        ax.axvline(x=1.0, color='black', linestyle='--', alpha=0.5, label='ATM')
        ax.set_xlabel('Moneyness (Strike/Spot)')
        ax.set_ylabel('Implied Volatility')
        ax.set_title('Implied Volatility Smile')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_time_value(self, data: pd.DataFrame, ax: plt.Axes):
        """Plot time value by moneyness."""
        if 'time_value_call' not in data.columns and 'time_value_put' not in data.columns:
            ax.text(0.5, 0.5, 'Time value data not available', transform=ax.transAxes, ha='center')
            return
        
        calls = data[data['option_type'] == 'call']
        puts = data[data['option_type'] == 'put']
        
        if not calls.empty and 'time_value_call' in calls.columns:
            ax.scatter(calls['moneyness'], calls['time_value_call'], 
                      color='green', alpha=0.7, s=30, label='Calls')
        if not puts.empty and 'time_value_put' in puts.columns:
            ax.scatter(puts['moneyness'], puts['time_value_put'], 
                      color='red', alpha=0.7, s=30, label='Puts')
        
        ax.set_xlabel('Moneyness (Strike/Spot)')
        ax.set_ylabel('Time Value')
        ax.set_title('Time Value by Moneyness')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_greeks_summary(self, data: pd.DataFrame, ax: plt.Axes):
        """Plot Greeks summary (delta and gamma)."""
        if 'delta' not in data.columns:
            ax.text(0.5, 0.5, 'Greeks data not available', transform=ax.transAxes, ha='center')
            return
        
        # Create twin axis for gamma
        ax2 = ax.twinx()
        
        calls = data[data['option_type'] == 'call'].sort_values('strike')
        puts = data[data['option_type'] == 'put'].sort_values('strike')
        
        # Plot delta
        if not calls.empty:
            ax.plot(calls['strike'], calls['delta'], color='green', linewidth=2, 
                   marker='o', markersize=4, label='Call Delta')
        if not puts.empty:
            ax.plot(puts['strike'], puts['delta'], color='red', linewidth=2, 
                   marker='o', markersize=4, label='Put Delta')
        
        # Plot gamma on second axis
        if 'gamma' in data.columns:
            gamma_data = data.groupby('strike')['gamma'].mean()  # Average gamma for calls and puts
            ax2.plot(gamma_data.index, gamma_data.values, color='blue', linewidth=2, 
                    linestyle='--', marker='s', markersize=4, label='Gamma')
        
        ax.set_xlabel('Strike Price')
        ax.set_ylabel('Delta', color='black')
        ax2.set_ylabel('Gamma', color='blue')
        ax.set_title('Options Greeks by Strike')
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='best')
        
        ax.grid(True, alpha=0.3)