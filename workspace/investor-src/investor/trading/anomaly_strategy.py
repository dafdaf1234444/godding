"""
Anomaly-Based Investment Strategy Framework.

This module implements investment strategies that utilize anomaly detection signals
to make trading decisions, with comprehensive backtesting capabilities.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    entry_date: datetime
    entry_price: float
    quantity: float
    position_type: str  # 'long' or 'short'
    entry_signal: str
    anomaly_type: str
    confidence: float
    expected_duration: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_signal: Optional[str] = None
    pnl: Optional[float] = None
    return_pct: Optional[float] = None


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    num_trades: int
    avg_holding_period: float


class SignalFilter(Enum):
    """Signal filtering strategies."""
    ALL = "all"
    HIGH_CONFIDENCE = "high_confidence"
    MOMENTUM_ONLY = "momentum_only"
    BREAKOUT_ONLY = "breakout_only"
    REGIME_AWARE = "regime_aware"
    CUSTOM = "custom"


class PositionSizing(Enum):
    """Position sizing methods."""
    EQUAL_WEIGHT = "equal_weight"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    KELLY_CRITERION = "kelly_criterion"


class AnomalyTradingStrategy:
    """
    Investment strategy that uses anomaly detection signals for trading decisions.
    
    Features:
    - Multiple signal filtering strategies
    - Dynamic position sizing
    - Risk management with stop-loss and take-profit
    - Portfolio-level risk controls
    - Comprehensive backtesting
    """
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_positions: int = 10,
                 position_sizing: PositionSizing = PositionSizing.EQUAL_WEIGHT,
                 signal_filter: SignalFilter = SignalFilter.HIGH_CONFIDENCE,
                 min_confidence: float = 0.7,
                 max_risk_per_trade: float = 0.02,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.15,
                 transaction_cost: float = 0.001,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the anomaly trading strategy.
        
        Args:
            initial_capital: Starting capital
            max_positions: Maximum number of concurrent positions
            position_sizing: Position sizing method
            signal_filter: Signal filtering strategy
            min_confidence: Minimum confidence threshold for signals
            max_risk_per_trade: Maximum risk per trade as % of capital
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            transaction_cost: Transaction cost as percentage
            config: Additional configuration
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_positions = max_positions
        self.position_sizing = position_sizing
        self.signal_filter = signal_filter
        self.min_confidence = min_confidence
        self.max_risk_per_trade = max_risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.transaction_cost = transaction_cost
        self.config = config or {}
        
        # Trading state
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.portfolio_history: List[Dict] = []
        self.signals_history: List[Dict] = []
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.daily_values: List[float] = []
        self.daily_dates: List[datetime] = []
        
        logger.info(f"Initialized AnomalyTradingStrategy with {initial_capital:,.0f} capital")
    
    def filter_signals(self, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter anomaly signals based on strategy configuration.
        
        Args:
            signals_df: DataFrame with anomaly signals
            
        Returns:
            Filtered signals DataFrame
        """
        if signals_df.empty:
            return signals_df
            
        filtered = signals_df.copy()
        
        # Apply confidence filter
        filtered = filtered[filtered['confidence'] >= self.min_confidence]
        
        # Apply signal-specific filters
        if self.signal_filter == SignalFilter.HIGH_CONFIDENCE:
            filtered = filtered[filtered['confidence'] >= 0.8]
            
        elif self.signal_filter == SignalFilter.MOMENTUM_ONLY:
            filtered = filtered[filtered['anomaly_type'].str.contains('momentum')]
            
        elif self.signal_filter == SignalFilter.BREAKOUT_ONLY:
            filtered = filtered[filtered['anomaly_type'].str.contains('breakout|breakdown')]
            
        elif self.signal_filter == SignalFilter.REGIME_AWARE:
            # Prioritize regime change signals
            high_vol_regime = filtered[filtered['anomaly_type'].str.contains('high_volatility')]
            other_signals = filtered[~filtered['anomaly_type'].str.contains('volatility_regime')]
            filtered = pd.concat([high_vol_regime, other_signals]).drop_duplicates()
        
        # Remove hold signals for active trading
        filtered = filtered[filtered['signal'].isin(['buy', 'sell'])]
        
        # Sort by confidence and expected return
        if 'potential_return' in filtered.columns:
            filtered = filtered.sort_values(['confidence', 'potential_return'], ascending=[False, False])
        else:
            filtered = filtered.sort_values('confidence', ascending=False)
            
        logger.info(f"Filtered {len(signals_df)} signals to {len(filtered)} actionable signals")
        return filtered
    
    def calculate_position_size(self, signal: pd.Series, current_price: float) -> float:
        """
        Calculate position size based on sizing strategy.
        
        Args:
            signal: Signal data
            current_price: Current asset price
            
        Returns:
            Position size (number of shares/units)
        """
        available_capital = self.current_capital * (1 - len(self.positions) * self.max_risk_per_trade)
        available_capital = max(available_capital, self.current_capital * 0.1)  # Minimum 10% available
        
        if self.position_sizing == PositionSizing.EQUAL_WEIGHT:
            position_value = available_capital / max(1, self.max_positions - len(self.positions))
            
        elif self.position_sizing == PositionSizing.CONFIDENCE_WEIGHTED:
            base_position = available_capital / max(1, self.max_positions - len(self.positions))
            confidence_multiplier = signal['confidence']
            position_value = base_position * confidence_multiplier
            
        elif self.position_sizing == PositionSizing.VOLATILITY_ADJUSTED:
            # Adjust based on expected volatility (using severity as proxy)
            severity_map = {'low': 1.5, 'medium': 1.0, 'high': 0.7, 'critical': 0.5}
            vol_adjustment = severity_map.get(signal.get('severity', 'medium'), 1.0)
            base_position = available_capital / max(1, self.max_positions - len(self.positions))
            position_value = base_position * vol_adjustment
            
        elif self.position_sizing == PositionSizing.KELLY_CRITERION:
            # Simplified Kelly using potential_return if available
            if 'potential_return' in signal and signal['potential_return'] is not None:
                expected_return = float(signal['potential_return'])
                win_prob = signal['confidence']
                if expected_return > 0 and win_prob > 0.5:
                    kelly_f = (win_prob * (1 + expected_return) - 1) / expected_return
                    kelly_f = max(0, min(kelly_f, 0.25))  # Cap at 25%
                    position_value = available_capital * kelly_f
                else:
                    position_value = available_capital * 0.05  # Conservative fallback
            else:
                position_value = available_capital / max(1, self.max_positions - len(self.positions))
        else:
            position_value = available_capital / max(1, self.max_positions - len(self.positions))
        
        # Apply risk limit
        max_position_value = self.current_capital * self.max_risk_per_trade
        position_value = min(position_value, max_position_value)
        
        # Calculate number of shares
        position_size = position_value / current_price
        return max(0, position_size)
    
    def enter_position(self, signal: pd.Series, current_price: float, date: datetime) -> Optional[Position]:
        """
        Enter a new trading position based on signal.
        
        Args:
            signal: Anomaly signal
            current_price: Current asset price
            date: Trade date
            
        Returns:
            Position object if trade executed, None otherwise
        """
        if len(self.positions) >= self.max_positions:
            logger.debug(f"Max positions reached, skipping signal for {signal['symbol']}")
            return None
            
        # Check if we already have a position in this symbol
        existing_position = next((p for p in self.positions if p.symbol == signal['symbol']), None)
        if existing_position:
            logger.debug(f"Already have position in {signal['symbol']}, skipping")
            return None
        
        position_size = self.calculate_position_size(signal, current_price)
        if position_size * current_price < 100:  # Minimum trade size
            logger.debug(f"Position size too small for {signal['symbol']}: {position_size}")
            return None
        
        # Create position
        position_type = 'long' if signal['signal'] == 'buy' else 'short'
        transaction_cost = position_size * current_price * self.transaction_cost
        
        position = Position(
            symbol=signal['symbol'],
            entry_date=date,
            entry_price=current_price,
            quantity=position_size,
            position_type=position_type,
            entry_signal=signal['signal'],
            anomaly_type=signal['anomaly_type'],
            confidence=signal['confidence'],
            expected_duration=signal.get('expected_duration', 'unknown'),
            stop_loss=current_price * (1 - self.stop_loss_pct) if position_type == 'long' 
                     else current_price * (1 + self.stop_loss_pct),
            take_profit=current_price * (1 + self.take_profit_pct) if position_type == 'long'
                       else current_price * (1 - self.take_profit_pct)
        )
        
        self.positions.append(position)
        self.current_capital -= transaction_cost
        
        logger.info(f"Entered {position_type} position in {signal['symbol']}: "
                   f"{position_size:.2f} shares @ {current_price:.2f}")
        
        return position
    
    def check_exit_conditions(self, position: Position, current_price: float, 
                            date: datetime, signals_df: pd.DataFrame) -> Optional[str]:
        """
        Check if position should be exited.
        
        Args:
            position: Current position
            current_price: Current asset price
            date: Current date
            signals_df: Current signals for exit signal detection
            
        Returns:
            Exit reason if should exit, None otherwise
        """
        # Check stop loss
        if position.position_type == 'long' and current_price <= position.stop_loss:
            return 'stop_loss'
        elif position.position_type == 'short' and current_price >= position.stop_loss:
            return 'stop_loss'
            
        # Check take profit
        if position.position_type == 'long' and current_price >= position.take_profit:
            return 'take_profit'
        elif position.position_type == 'short' and current_price <= position.take_profit:
            return 'take_profit'
        
        # Check for opposing signals
        symbol_signals = signals_df[signals_df['symbol'] == position.symbol]
        if not symbol_signals.empty:
            latest_signal = symbol_signals.iloc[0]
            if ((position.position_type == 'long' and latest_signal['signal'] == 'sell') or
                (position.position_type == 'short' and latest_signal['signal'] == 'buy')):
                if latest_signal['confidence'] >= self.min_confidence:
                    return 'opposing_signal'
        
        # Check holding period (exit after maximum expected duration)
        holding_days = (date - position.entry_date).days
        max_hold_days = {'immediate': 1, 'short_term': 10, 'medium_term': 30, 'long_term': 90}
        
        # Parse expected_duration
        expected_duration = position.expected_duration.lower()
        if 'day' in expected_duration:
            max_days = 5  # Default for day-based durations
        elif 'week' in expected_duration:
            max_days = 14  # Default for week-based durations
        elif any(term in expected_duration for term in ['immediate', 'short', 'medium', 'long']):
            for term, days in max_hold_days.items():
                if term in expected_duration:
                    max_days = days
                    break
            else:
                max_days = 30  # Default
        else:
            max_days = 30  # Default
            
        if holding_days > max_days:
            return 'max_holding_period'
            
        return None
    
    def exit_position(self, position: Position, current_price: float, 
                     date: datetime, exit_reason: str) -> Position:
        """
        Exit a trading position.
        
        Args:
            position: Position to exit
            current_price: Exit price
            date: Exit date
            exit_reason: Reason for exit
            
        Returns:
            Updated position with exit information
        """
        transaction_cost = position.quantity * current_price * self.transaction_cost
        
        if position.position_type == 'long':
            pnl = (current_price - position.entry_price) * position.quantity - transaction_cost
        else:
            pnl = (position.entry_price - current_price) * position.quantity - transaction_cost
        
        return_pct = pnl / (position.quantity * position.entry_price)
        
        position.exit_date = date
        position.exit_price = current_price
        position.exit_signal = exit_reason
        position.pnl = pnl
        position.return_pct = return_pct
        
        self.current_capital += position.quantity * current_price - transaction_cost
        self.closed_positions.append(position)
        
        logger.info(f"Exited {position.position_type} position in {position.symbol}: "
                   f"PnL: {pnl:.2f} ({return_pct:.2%}) - {exit_reason}")
        
        return position
    
    def update_portfolio_value(self, date: datetime, price_data: Dict[str, float]):
        """
        Update portfolio value and track performance.
        
        Args:
            date: Current date
            price_data: Current prices for all symbols
        """
        # Calculate current portfolio value
        cash_value = self.current_capital
        position_value = 0
        
        for position in self.positions:
            if position.symbol in price_data:
                current_price = price_data[position.symbol]
                if position.position_type == 'long':
                    position_value += position.quantity * current_price
                else:
                    # For short positions, value decreases as price increases
                    position_value += position.quantity * (2 * position.entry_price - current_price)
        
        total_value = cash_value + position_value
        
        # Calculate daily return
        if self.daily_values:
            daily_return = (total_value - self.daily_values[-1]) / self.daily_values[-1]
        else:
            daily_return = 0
            
        self.daily_values.append(total_value)
        self.daily_returns.append(daily_return)
        self.daily_dates.append(date)
        
        # Track portfolio history
        self.portfolio_history.append({
            'date': date,
            'total_value': total_value,
            'cash': cash_value,
            'position_value': position_value,
            'num_positions': len(self.positions),
            'daily_return': daily_return
        })
    
    def calculate_metrics(self) -> PortfolioMetrics:
        """Calculate comprehensive portfolio performance metrics."""
        if not self.daily_returns or len(self.daily_returns) < 2:
            return PortfolioMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        returns = np.array(self.daily_returns[1:])  # Skip first zero return
        
        # Basic metrics
        total_return = (self.daily_values[-1] - self.initial_capital) / self.initial_capital
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown calculation
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Trade metrics
        if self.closed_positions:
            winning_trades = [p for p in self.closed_positions if p.pnl > 0]
            losing_trades = [p for p in self.closed_positions if p.pnl <= 0]
            
            win_rate = len(winning_trades) / len(self.closed_positions)
            avg_win = np.mean([p.pnl for p in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([p.pnl for p in losing_trades]) if losing_trades else 0
            
            total_wins = sum(p.pnl for p in winning_trades)
            total_losses = abs(sum(p.pnl for p in losing_trades))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            avg_holding_period = np.mean([
                (p.exit_date - p.entry_date).days for p in self.closed_positions
            ])
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            avg_holding_period = 0
        
        return PortfolioMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            num_trades=len(self.closed_positions),
            avg_holding_period=avg_holding_period
        )


class AnomalyStrategyBacktester:
    """
    Comprehensive backtesting framework for anomaly-based strategies.
    """
    
    def __init__(self, 
                 start_date: str = "2023-01-01",
                 end_date: str = "2024-12-31",
                 benchmark_symbol: str = "SPY"):
        """
        Initialize the backtester.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date  
            benchmark_symbol: Benchmark for comparison (default SPY)
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.benchmark_symbol = benchmark_symbol
        
        logger.info(f"Initialized backtester for {start_date} to {end_date}")
    
    def run_backtest(self, 
                     strategy: AnomalyTradingStrategy,
                     signals_df: pd.DataFrame,
                     price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run comprehensive backtest of anomaly strategy.
        
        Args:
            strategy: Trading strategy to test
            signals_df: Anomaly signals data
            price_data: Historical price data
            
        Returns:
            Backtest results dictionary
        """
        logger.info("Starting backtest execution...")
        
        # Filter data to backtest period
        # Handle timezone-aware datetimes
        if 'date' in signals_df.columns:
            try:
                signals_df['date'] = pd.to_datetime(signals_df['date'], utc=True).dt.tz_convert(None)
            except Exception as e:
                logger.warning(f"Error converting dates: {e}. Trying alternative approach.")
                signals_df['date'] = pd.to_datetime(signals_df['date']).dt.tz_localize(None)
        
        # Convert start/end dates to datetime if they're not already
        start_date = pd.to_datetime(self.start_date)
        end_date = pd.to_datetime(self.end_date)
        
        # More robust filtering
        try:
            mask = (signals_df['date'] >= start_date) & (signals_df['date'] <= end_date)
            signals_df = signals_df[mask].copy()
        except Exception as e:
            logger.error(f"Error filtering signals: {e}")
            logger.info(f"Date column type: {signals_df['date'].dtype}")
            logger.info(f"Start date type: {type(start_date)}")
            logger.info(f"Sample dates: {signals_df['date'].head()}")
            raise
        
        price_data = price_data[
            (price_data.index >= start_date) &
            (price_data.index <= end_date)
        ].copy()
        
        # Sort signals by date
        signals_df = signals_df.sort_values('date')
        
        # Group signals by date for daily processing
        daily_signals = signals_df.groupby(signals_df['date'].dt.date)
        
        # Main backtest loop
        for date in pd.date_range(start_date, end_date, freq='D'):
            if date.weekday() >= 5:  # Skip weekends
                continue
                
            date_str = date.date()
            
            # Get current day's signals
            if date_str in daily_signals.groups:
                day_signals = daily_signals.get_group(date_str)
                filtered_signals = strategy.filter_signals(day_signals)
            else:
                filtered_signals = pd.DataFrame()
            
            # Get current prices
            if date.date() in price_data.index.date:
                current_prices = price_data.loc[date].to_dict()
            else:
                # Use last available prices
                available_dates = price_data.index[price_data.index <= date]
                if len(available_dates) > 0:
                    latest_date = available_dates[-1]
                    current_prices = price_data.loc[latest_date].to_dict()
                else:
                    continue
            
            # Check exit conditions for existing positions
            positions_to_exit = []
            for position in strategy.positions:
                if position.symbol in current_prices:
                    current_price = current_prices[position.symbol]
                    exit_reason = strategy.check_exit_conditions(
                        position, current_price, date, filtered_signals
                    )
                    if exit_reason:
                        positions_to_exit.append((position, exit_reason))
            
            # Exit positions
            for position, exit_reason in positions_to_exit:
                current_price = current_prices[position.symbol]
                strategy.exit_position(position, current_price, date, exit_reason)
                strategy.positions.remove(position)
            
            # Enter new positions
            for _, signal in filtered_signals.iterrows():
                if signal['symbol'] in current_prices:
                    current_price = current_prices[signal['symbol']]
                    new_position = strategy.enter_position(signal, current_price, date)
                    if new_position:
                        strategy.signals_history.append({
                            'date': date,
                            'action': 'enter',
                            'signal': signal.to_dict(),
                            'price': current_price
                        })
            
            # Update portfolio value
            strategy.update_portfolio_value(date, current_prices)
        
        # Close any remaining positions at end date
        final_prices = price_data.iloc[-1].to_dict()
        for position in strategy.positions[:]:
            if position.symbol in final_prices:
                final_price = final_prices[position.symbol]
                strategy.exit_position(position, final_price, end_date, 'backtest_end')
                strategy.positions.remove(position)
        
        # Calculate final metrics
        metrics = strategy.calculate_metrics()
        
        # Calculate benchmark performance
        benchmark_performance = self._calculate_benchmark_performance(price_data)
        
        results = {
            'strategy_metrics': metrics,
            'benchmark_performance': benchmark_performance,
            'portfolio_history': strategy.portfolio_history,
            'closed_positions': strategy.closed_positions,
            'signals_history': strategy.signals_history,
            'daily_returns': strategy.daily_returns,
            'daily_values': strategy.daily_values,
            'daily_dates': strategy.daily_dates
        }
        
        logger.info(f"Backtest completed: {metrics.num_trades} trades, "
                   f"{metrics.total_return:.2%} total return, "
                   f"{metrics.sharpe_ratio:.2f} Sharpe ratio")
        
        return results
    
    def _calculate_benchmark_performance(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate buy-and-hold benchmark performance."""
        if self.benchmark_symbol in price_data.columns:
            benchmark_prices = price_data[self.benchmark_symbol].dropna()
            if len(benchmark_prices) > 1:
                total_return = (benchmark_prices.iloc[-1] - benchmark_prices.iloc[0]) / benchmark_prices.iloc[0]
                daily_returns = benchmark_prices.pct_change().dropna()
                annualized_return = (1 + total_return) ** (252 / len(daily_returns)) - 1
                volatility = daily_returns.std() * np.sqrt(252)
                sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
                
                return {
                    'total_return': total_return,
                    'annualized_return': annualized_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio
                }
        
        return {'total_return': 0, 'annualized_return': 0, 'volatility': 0, 'sharpe_ratio': 0}
    
    def compare_strategies(self, results_list: List[Dict[str, Any]], 
                          strategy_names: List[str]) -> pd.DataFrame:
        """
        Compare multiple strategy results.
        
        Args:
            results_list: List of backtest results
            strategy_names: Names for each strategy
            
        Returns:
            Comparison DataFrame
        """
        comparison_data = []
        
        for i, (results, name) in enumerate(zip(results_list, strategy_names)):
            metrics = results['strategy_metrics']
            comparison_data.append({
                'Strategy': name,
                'Total Return': f"{metrics.total_return:.2%}",
                'Annualized Return': f"{metrics.annualized_return:.2%}",
                'Volatility': f"{metrics.volatility:.2%}",
                'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
                'Max Drawdown': f"{metrics.max_drawdown:.2%}",
                'Win Rate': f"{metrics.win_rate:.2%}",
                'Profit Factor': f"{metrics.profit_factor:.2f}",
                'Num Trades': metrics.num_trades,
                'Avg Holding (days)': f"{metrics.avg_holding_period:.1f}"
            })
        
        # Add benchmark
        if results_list:
            benchmark = results_list[0]['benchmark_performance']
            comparison_data.append({
                'Strategy': f'Buy & Hold ({self.benchmark_symbol})',
                'Total Return': f"{benchmark['total_return']:.2%}",
                'Annualized Return': f"{benchmark['annualized_return']:.2%}",
                'Volatility': f"{benchmark['volatility']:.2%}",
                'Sharpe Ratio': f"{benchmark['sharpe_ratio']:.2f}",
                'Max Drawdown': 'N/A',
                'Win Rate': 'N/A',
                'Profit Factor': 'N/A',
                'Num Trades': 0,
                'Avg Holding (days)': 'N/A'
            })
        
        return pd.DataFrame(comparison_data)