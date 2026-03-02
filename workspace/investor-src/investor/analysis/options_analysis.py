"""
Options analysis module integrating options data with the main analysis pipeline.
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import logging

import matplotlib.pyplot as plt

from ..data.options_data import OptionsDataProvider, download_options_data
from ..models.options_pricing import (
    BlackScholesModel, BlackScholesInputs, VolatilitySurface
)
from ..visualization.options_charts import OptionsVisualizationManager
from ..core.config import InvestorConfig

logger = logging.getLogger(__name__)


class OptionsAnalysisManager:
    """Manager for comprehensive options analysis."""
    
    def __init__(self, config: InvestorConfig):
        """
        Initialize options analysis manager.
        
        Args:
            config: Investor configuration
        """
        self.config = config
        self.options_provider = OptionsDataProvider()
        self.viz_manager = OptionsVisualizationManager()
        
    def analyze_options_for_symbols(self, symbols: List[str], 
                                  output_dir: str) -> Dict[str, Any]:
        """
        Perform comprehensive options analysis for given symbols.
        
        Args:
            symbols: List of symbols to analyze
            output_dir: Directory to save analysis outputs
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting options analysis for symbols: {symbols}")
        
        results = {
            'options_data': {},
            'volatility_surfaces': {},
            'options_signals': [],
            'portfolio_greeks': {},
            'visualizations': {},
            'summary': {}
        }
        
        try:
            # Download options data
            options_data = download_options_data(symbols)
            results['options_data'] = options_data
            
            if not options_data:
                logger.warning("No options data downloaded")
                return results
            
            # Analyze each symbol
            for symbol in options_data:
                logger.info(f"Analyzing options for {symbol}")
                
                try:
                    symbol_results = self._analyze_symbol_options(
                        symbol, options_data[symbol], output_dir
                    )
                    
                    # Store symbol-specific results
                    results['volatility_surfaces'][symbol] = symbol_results.get('volatility_surface')
                    results['options_signals'].extend(symbol_results.get('signals', []))
                    results['visualizations'][symbol] = symbol_results.get('visualizations', {})
                    
                except Exception as e:
                    logger.error(f"Error analyzing options for {symbol}: {str(e)}")
                    continue
            
            # Calculate portfolio-level metrics
            if options_data:
                results['portfolio_greeks'] = self._calculate_portfolio_metrics(options_data)
                results['summary'] = self._generate_options_summary(options_data)
            
            logger.info("Options analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error in options analysis: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_symbol_options(self, symbol: str, options_df: pd.DataFrame, 
                              output_dir: str) -> Dict[str, Any]:
        """
        Analyze options for a specific symbol.
        
        Args:
            symbol: Stock symbol
            options_df: Options data DataFrame
            output_dir: Output directory for visualizations
            
        Returns:
            Dictionary with symbol analysis results
        """
        results = {
            'signals': [],
            'volatility_surface': None,
            'visualizations': {}
        }
        
        if options_df.empty:
            return results
        
        try:
            # Create volatility surface
            vol_surface = VolatilitySurface(options_df)
            results['volatility_surface'] = vol_surface
            
            # Generate options signals
            signals = self._generate_options_signals(symbol, options_df, vol_surface)
            results['signals'] = signals
            
            # Create visualizations
            visualizations = self._create_options_visualizations(
                symbol, options_df, vol_surface, output_dir
            )
            results['visualizations'] = visualizations
            
            # Calculate theoretical prices and compare with market
            theoretical_analysis = self._calculate_theoretical_prices(symbol, options_df)
            results['theoretical_analysis'] = theoretical_analysis
            
        except Exception as e:
            logger.error(f"Error in symbol options analysis for {symbol}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _generate_options_signals(self, symbol: str, options_df: pd.DataFrame, 
                                vol_surface: VolatilitySurface) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on options analysis.
        
        Args:
            symbol: Stock symbol
            options_df: Options data
            vol_surface: Volatility surface object
            
        Returns:
            List of trading signals
        """
        signals = []
        
        try:
            current_price = options_df['underlying_price'].iloc[0] if not options_df.empty else 0
            
            # 1. Volatility skew signals
            skew_signals = self._analyze_volatility_skew(symbol, vol_surface, current_price)
            signals.extend(skew_signals)
            
            # 2. Volume and open interest signals
            volume_signals = self._analyze_volume_patterns(symbol, options_df)
            signals.extend(volume_signals)
            
            # 3. Put/Call ratio signals
            pc_signals = self._analyze_put_call_ratio(symbol, options_df)
            signals.extend(pc_signals)
            
            # 4. Unusual options activity
            unusual_signals = self._detect_unusual_options_activity(symbol, options_df)
            signals.extend(unusual_signals)
            
            # 5. Implied volatility term structure signals
            term_signals = self._analyze_iv_term_structure(symbol, vol_surface)
            signals.extend(term_signals)
            
        except Exception as e:
            logger.error(f"Error generating options signals for {symbol}: {str(e)}")
        
        return signals
    
    def _analyze_volatility_skew(self, symbol: str, vol_surface: VolatilitySurface, 
                               current_price: float) -> List[Dict[str, Any]]:
        """Analyze volatility skew for trading signals."""
        signals = []
        
        try:
            # Get near-term volatility skew
            if vol_surface.surface_data is not None and not vol_surface.surface_data.empty:
                near_term_exp = vol_surface.surface_data['expiration'].min()
                skew_data = vol_surface.calculate_volatility_skew(near_term_exp)
                
                if not skew_data.empty:
                    # Calculate skew slope
                    otm_puts = skew_data[(skew_data['option_type'] == 'put') & 
                                       (skew_data['moneyness'] < 0.95)]
                    otm_calls = skew_data[(skew_data['option_type'] == 'call') & 
                                        (skew_data['moneyness'] > 1.05)]
                    
                    if not otm_puts.empty and not otm_calls.empty:
                        put_iv_avg = otm_puts['implied_volatility'].mean()
                        call_iv_avg = otm_calls['implied_volatility'].mean()
                        skew_ratio = put_iv_avg / call_iv_avg
                        
                        if skew_ratio > 1.2:
                            signals.append({
                                'symbol': symbol,
                                'signal_type': 'volatility_skew',
                                'signal': 'bearish_skew',
                                'strength': min((skew_ratio - 1.0) * 5, 1.0),
                                'description': f'High put skew detected (ratio: {skew_ratio:.2f})',
                                'timestamp': datetime.now(),
                                'expiration': near_term_exp,
                                'skew_ratio': skew_ratio
                            })
                        elif skew_ratio < 0.8:
                            signals.append({
                                'symbol': symbol,
                                'signal_type': 'volatility_skew',
                                'signal': 'bullish_skew',
                                'strength': min((1.0 - skew_ratio) * 5, 1.0),
                                'description': f'High call skew detected (ratio: {skew_ratio:.2f})',
                                'timestamp': datetime.now(),
                                'expiration': near_term_exp,
                                'skew_ratio': skew_ratio
                            })
        
        except Exception as e:
            logger.warning(f"Error analyzing volatility skew for {symbol}: {str(e)}")
        
        return signals
    
    def _analyze_volume_patterns(self, symbol: str, options_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze volume patterns for unusual activity."""
        signals = []
        
        try:
            if 'volume' not in options_df.columns or options_df['volume'].sum() == 0:
                return signals
            
            # Calculate volume statistics
            total_call_volume = options_df[options_df['option_type'] == 'call']['volume'].sum()
            total_put_volume = options_df[options_df['option_type'] == 'put']['volume'].sum()
            total_volume = total_call_volume + total_put_volume
            
            if total_volume > 0:
                call_volume_ratio = total_call_volume / total_volume
                
                # High call volume signal
                if call_volume_ratio > 0.75 and total_volume > 1000:
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'volume_pattern',
                        'signal': 'high_call_volume',
                        'strength': min((call_volume_ratio - 0.5) * 2, 1.0),
                        'description': f'Unusually high call volume ({call_volume_ratio:.1%})',
                        'timestamp': datetime.now(),
                        'total_volume': total_volume,
                        'call_volume_ratio': call_volume_ratio
                    })
                
                # High put volume signal
                elif call_volume_ratio < 0.25 and total_volume > 1000:
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'volume_pattern',
                        'signal': 'high_put_volume',
                        'strength': min((0.5 - call_volume_ratio) * 2, 1.0),
                        'description': f'Unusually high put volume ({1-call_volume_ratio:.1%})',
                        'timestamp': datetime.now(),
                        'total_volume': total_volume,
                        'call_volume_ratio': call_volume_ratio
                    })
        
        except Exception as e:
            logger.warning(f"Error analyzing volume patterns for {symbol}: {str(e)}")
        
        return signals
    
    def _analyze_put_call_ratio(self, symbol: str, options_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze put/call ratio for sentiment signals."""
        signals = []
        
        try:
            if options_df.empty:
                return signals
            
            # Volume-based P/C ratio
            call_volume = options_df[options_df['option_type'] == 'call']['volume'].sum()
            put_volume = options_df[options_df['option_type'] == 'put']['volume'].sum()
            
            if call_volume > 0:
                pc_volume_ratio = put_volume / call_volume
                
                if pc_volume_ratio > 1.5:
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'put_call_ratio',
                        'signal': 'bearish_sentiment',
                        'strength': min((pc_volume_ratio - 1.0) / 2, 1.0),
                        'description': f'High P/C volume ratio: {pc_volume_ratio:.2f}',
                        'timestamp': datetime.now(),
                        'pc_ratio': pc_volume_ratio,
                        'metric': 'volume'
                    })
                elif pc_volume_ratio < 0.5:
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'put_call_ratio',
                        'signal': 'bullish_sentiment',
                        'strength': min((1.0 - pc_volume_ratio) / 0.5, 1.0),
                        'description': f'Low P/C volume ratio: {pc_volume_ratio:.2f}',
                        'timestamp': datetime.now(),
                        'pc_ratio': pc_volume_ratio,
                        'metric': 'volume'
                    })
            
            # Open interest-based P/C ratio
            call_oi = options_df[options_df['option_type'] == 'call']['open_interest'].sum()
            put_oi = options_df[options_df['option_type'] == 'put']['open_interest'].sum()
            
            if call_oi > 0:
                pc_oi_ratio = put_oi / call_oi
                
                if pc_oi_ratio > 2.0:
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'put_call_ratio',
                        'signal': 'bearish_positioning',
                        'strength': min((pc_oi_ratio - 1.0) / 3, 1.0),
                        'description': f'High P/C open interest ratio: {pc_oi_ratio:.2f}',
                        'timestamp': datetime.now(),
                        'pc_ratio': pc_oi_ratio,
                        'metric': 'open_interest'
                    })
        
        except Exception as e:
            logger.warning(f"Error analyzing P/C ratio for {symbol}: {str(e)}")
        
        return signals
    
    def _detect_unusual_options_activity(self, symbol: str, options_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual options activity patterns."""
        signals = []
        
        try:
            if options_df.empty or 'volume' not in options_df.columns:
                return signals
            
            # Find contracts with unusual volume relative to open interest
            options_df['volume_oi_ratio'] = options_df['volume'] / options_df['open_interest'].clip(lower=1)
            
            # High volume/OI ratio indicates new interest
            unusual_contracts = options_df[
                (options_df['volume_oi_ratio'] > 2.0) & 
                (options_df['volume'] > 100)
            ]
            
            if not unusual_contracts.empty:
                # Group by option type and expiration
                for (option_type, expiration), group in unusual_contracts.groupby(['option_type', 'expiration']):
                    total_volume = group['volume'].sum()
                    avg_ratio = group['volume_oi_ratio'].mean()
                    
                    if total_volume > 500:  # Significant volume threshold
                        signals.append({
                            'symbol': symbol,
                            'signal_type': 'unusual_activity',
                            'signal': f'high_volume_{option_type}s',
                            'strength': min(avg_ratio / 5, 1.0),
                            'description': f'Unusual {option_type} volume in {expiration} (avg V/OI: {avg_ratio:.1f})',
                            'timestamp': datetime.now(),
                            'expiration': expiration,
                            'option_type': option_type,
                            'total_volume': total_volume,
                            'avg_volume_oi_ratio': avg_ratio
                        })
        
        except Exception as e:
            logger.warning(f"Error detecting unusual activity for {symbol}: {str(e)}")
        
        return signals
    
    def _analyze_iv_term_structure(self, symbol: str, vol_surface: VolatilitySurface) -> List[Dict[str, Any]]:
        """Analyze implied volatility term structure for signals."""
        signals = []
        
        try:
            # Get ATM term structure
            term_structure = vol_surface.get_term_structure(moneyness=1.0, tolerance=0.1)
            
            if len(term_structure) >= 2:
                # Check for inverted volatility term structure
                short_term_iv = term_structure.iloc[0]['implied_volatility']
                long_term_iv = term_structure.iloc[-1]['implied_volatility']
                
                if short_term_iv > long_term_iv * 1.3:  # 30% higher short-term IV
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'term_structure',
                        'signal': 'inverted_volatility',
                        'strength': min((short_term_iv / long_term_iv - 1.0) / 0.5, 1.0),
                        'description': f'Inverted volatility term structure (short: {short_term_iv:.1%}, long: {long_term_iv:.1%})',
                        'timestamp': datetime.now(),
                        'short_term_iv': short_term_iv,
                        'long_term_iv': long_term_iv
                    })
        
        except Exception as e:
            logger.warning(f"Error analyzing term structure for {symbol}: {str(e)}")
        
        return signals
    
    def _calculate_theoretical_prices(self, symbol: str, options_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate theoretical option prices and compare with market prices."""
        results = {}
        
        try:
            if options_df.empty or 'underlying_price' not in options_df.columns:
                return results
            
            current_price = options_df['underlying_price'].iloc[0]
            risk_free_rate = 0.02  # Default 2% risk-free rate
            
            mispriced_options = []
            
            for _, option in options_df.iterrows():
                try:
                    # Calculate time to expiration
                    exp_date = pd.to_datetime(option['expiration'])
                    time_to_exp = (exp_date - datetime.now()).total_seconds() / (365.25 * 24 * 3600)
                    
                    if time_to_exp <= 0 or option['implied_volatility'] <= 0:
                        continue
                    
                    inputs = BlackScholesInputs(
                        S=current_price,
                        K=option['strike'],
                        T=time_to_exp,
                        r=risk_free_rate,
                        sigma=option['implied_volatility']
                    )
                    
                    # Calculate theoretical price
                    if option['option_type'] == 'call':
                        theoretical_price = BlackScholesModel.call_price(
                            inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma
                        )
                    else:
                        theoretical_price = BlackScholesModel.put_price(
                            inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma
                        )
                    
                    market_price = option['last_price']
                    
                    if market_price > 0:
                        price_diff_pct = (market_price - theoretical_price) / theoretical_price
                        
                        # Flag significantly mispriced options
                        if abs(price_diff_pct) > 0.15:  # 15% difference
                            mispriced_options.append({
                                'strike': option['strike'],
                                'expiration': option['expiration'],
                                'option_type': option['option_type'],
                                'market_price': market_price,
                                'theoretical_price': theoretical_price,
                                'price_diff_pct': price_diff_pct,
                                'volume': option['volume'],
                                'implied_volatility': option['implied_volatility']
                            })
                
                except Exception as e:
                    logger.debug(f"Error calculating theoretical price for option: {str(e)}")
                    continue
            
            results['mispriced_options'] = mispriced_options
            results['mispriced_count'] = len(mispriced_options)
            
        except Exception as e:
            logger.warning(f"Error in theoretical price calculation for {symbol}: {str(e)}")
        
        return results
    
    def _create_options_visualizations(self, symbol: str, options_df: pd.DataFrame, 
                                     vol_surface: VolatilitySurface, output_dir: str) -> Dict[str, str]:
        """Create and save options visualizations."""
        visualizations = {}
        
        try:
            import os
            os.makedirs(f"{output_dir}/options", exist_ok=True)
            
            # 1. Volatility surface
            try:
                fig = self.viz_manager.create_volatility_surface_3d(vol_surface)
                surface_path = f"{output_dir}/options/{symbol}_volatility_surface.png"
                fig.savefig(surface_path, dpi=300, bbox_inches='tight')
                visualizations['volatility_surface'] = surface_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Error creating volatility surface for {symbol}: {str(e)}")
            
            # 2. Term structure
            try:
                fig = self.viz_manager.create_volatility_term_structure(vol_surface)
                term_path = f"{output_dir}/options/{symbol}_term_structure.png"
                fig.savefig(term_path, dpi=300, bbox_inches='tight')
                visualizations['term_structure'] = term_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Error creating term structure for {symbol}: {str(e)}")
            
            # 3. Volatility skew
            try:
                fig = self.viz_manager.create_volatility_skew_plot(vol_surface)
                skew_path = f"{output_dir}/options/{symbol}_volatility_skew.png"
                fig.savefig(skew_path, dpi=300, bbox_inches='tight')
                visualizations['volatility_skew'] = skew_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Error creating volatility skew for {symbol}: {str(e)}")
            
            # 4. Options chain summary
            try:
                fig = self.viz_manager.create_options_chain_summary(options_df)
                summary_path = f"{output_dir}/options/{symbol}_options_summary.png"
                fig.savefig(summary_path, dpi=300, bbox_inches='tight')
                visualizations['options_summary'] = summary_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Error creating options summary for {symbol}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error creating visualizations for {symbol}: {str(e)}")
        
        return visualizations
    
    def _calculate_portfolio_metrics(self, options_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate portfolio-level options metrics."""
        portfolio_metrics = {}
        
        try:
            # Aggregate metrics across all symbols
            total_volume = 0
            total_open_interest = 0
            total_call_volume = 0
            total_put_volume = 0
            
            for symbol, df in options_data.items():
                if df.empty:
                    continue
                
                symbol_volume = df['volume'].sum()
                symbol_oi = df['open_interest'].sum()
                symbol_call_vol = df[df['option_type'] == 'call']['volume'].sum()
                symbol_put_vol = df[df['option_type'] == 'put']['volume'].sum()
                
                total_volume += symbol_volume
                total_open_interest += symbol_oi
                total_call_volume += symbol_call_vol
                total_put_volume += symbol_put_vol
            
            portfolio_metrics.update({
                'total_volume': total_volume,
                'total_open_interest': total_open_interest,
                'total_call_volume': total_call_volume,
                'total_put_volume': total_put_volume,
                'portfolio_pc_ratio': total_put_volume / max(total_call_volume, 1),
                'symbols_analyzed': len(options_data)
            })
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
        
        return portfolio_metrics
    
    def _generate_options_summary(self, options_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate summary of options analysis."""
        summary = {
            'analysis_timestamp': datetime.now(),
            'symbols_analyzed': list(options_data.keys()),
            'total_contracts': 0,
            'avg_implied_volatility': 0,
            'most_active_symbol': None,
            'most_active_expiration': None
        }
        
        try:
            all_options = []
            symbol_volumes = {}
            
            for symbol, df in options_data.items():
                if not df.empty:
                    all_options.append(df)
                    symbol_volumes[symbol] = df['volume'].sum()
            
            if all_options:
                combined_df = pd.concat(all_options, ignore_index=True)
                
                summary.update({
                    'total_contracts': len(combined_df),
                    'avg_implied_volatility': combined_df['implied_volatility'].mean(),
                    'most_active_symbol': max(symbol_volumes.items(), key=lambda x: x[1])[0] if symbol_volumes else None,
                    'most_active_expiration': combined_df.groupby('expiration')['volume'].sum().idxmax()
                })
            
        except Exception as e:
            logger.error(f"Error generating options summary: {str(e)}")
        
        return summary