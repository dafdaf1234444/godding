"""
Earnings data processing and feature engineering for machine learning models.
Provides normalized earnings features with temporal validation.
"""
import pandas as pd
from datetime import timedelta
from typing import Dict, Any
import logging
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)


class EarningsProcessor:
    """Processes and normalizes earnings data for ML models."""
    
    def __init__(self):
        """Initialize the earnings processor."""
        self.scalers = {}
        self.feature_names = []
        
    def process_earnings_history(
        self, 
        earnings_history: pd.DataFrame,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Process earnings history data and create ML features.
        
        Args:
            earnings_history: Raw earnings history DataFrame
            normalize: Whether to normalize the features
            
        Returns:
            Processed DataFrame with earnings features
        """
        if earnings_history.empty:
            logger.warning("Empty earnings history data provided")
            return pd.DataFrame()
        
        processed_data = earnings_history.copy()
        
        # Ensure Date column is datetime
        if 'Date' in processed_data.columns:
            processed_data['Date'] = pd.to_datetime(processed_data['Date'])
        
        # Calculate additional earnings features
        processed_data = self._calculate_earnings_features(processed_data)
        
        # Create temporal features
        processed_data = self._create_temporal_features(processed_data)
        
        # Create surprise and trend features
        processed_data = self._create_surprise_features(processed_data)
        
        # Normalize features if requested
        if normalize:
            processed_data = self._normalize_features(processed_data, 'earnings_history')
        
        # Sort by date for temporal consistency
        if 'Date' in processed_data.columns:
            processed_data = processed_data.sort_values('Date')
        
        logger.info(f"Processed earnings history: {len(processed_data)} records, {len(processed_data.columns)} features")
        return processed_data
    
    def process_financial_statements(
        self,
        financial_data: Dict[str, pd.DataFrame],
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Process financial statements and extract key metrics.
        
        Args:
            financial_data: Dictionary with financial statements
            normalize: Whether to normalize the features
            
        Returns:
            Combined DataFrame with financial metrics
        """
        if not financial_data:
            logger.warning("Empty financial data provided")
            return pd.DataFrame()
        
        combined_data = None
        
        # Process each financial statement type
        for stmt_type, stmt_data in financial_data.items():
            if stmt_data is None or stmt_data.empty:
                continue
                
            processed_stmt = self._process_single_statement(stmt_data, stmt_type)
            
            if combined_data is None:
                combined_data = processed_stmt
            else:
                # Merge on Date and Symbol
                merge_cols = ['Date', 'Symbol'] if 'Symbol' in processed_stmt.columns else ['Date']
                combined_data = pd.merge(
                    combined_data, processed_stmt, 
                    on=merge_cols, how='outer', suffixes=('', f'_{stmt_type}')
                )
        
        if combined_data is None:
            return pd.DataFrame()
        
        # Calculate financial ratios and metrics
        combined_data = self._calculate_financial_ratios(combined_data)
        
        # Create growth metrics
        combined_data = self._calculate_growth_metrics(combined_data)
        
        # Normalize features if requested
        if normalize:
            combined_data = self._normalize_features(combined_data, 'financial_statements')
        
        # Sort by date
        if 'Date' in combined_data.columns:
            combined_data = combined_data.sort_values('Date')
        
        logger.info(f"Processed financial statements: {len(combined_data)} records, {len(combined_data.columns)} features")
        return combined_data
    
    def create_earnings_events_features(
        self,
        earnings_dates: pd.DataFrame,
        price_data: pd.DataFrame,
        window_days: int = 5
    ) -> pd.DataFrame:
        """
        Create features around earnings announcement events.
        
        Args:
            earnings_dates: DataFrame with earnings dates
            price_data: Stock price DataFrame
            window_days: Number of days before/after earnings to analyze
            
        Returns:
            DataFrame with earnings event features
        """
        if earnings_dates.empty or price_data.empty:
            logger.warning("Empty data provided for earnings events processing")
            return pd.DataFrame()
        
        events_features = []
        
        for _, earnings_row in earnings_dates.iterrows():
            earnings_date = earnings_row['Date']
            
            # Get price data around earnings date
            start_date = earnings_date - timedelta(days=window_days)
            end_date = earnings_date + timedelta(days=window_days)
            
            # Filter price data for the window
            if 'Date' in price_data.columns:
                price_window = price_data[
                    (price_data['Date'] >= start_date) & 
                    (price_data['Date'] <= end_date)
                ].copy()
            else:
                # Assume Date is in index
                price_window = price_data[
                    (price_data.index >= start_date) & 
                    (price_data.index <= end_date)
                ].copy()
            
            if price_window.empty:
                continue
            
            # Calculate event features
            event_features = self._calculate_event_features(
                price_window, earnings_date, earnings_row, window_days
            )
            
            if event_features:
                events_features.append(event_features)
        
        if not events_features:
            return pd.DataFrame()
        
        events_df = pd.DataFrame(events_features)
        logger.info(f"Created earnings event features: {len(events_df)} events")
        return events_df
    
    def _calculate_earnings_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic earnings features."""
        if 'epsActual' in data.columns and 'epsEstimate' in data.columns:
            # Earnings surprise metrics
            data['eps_surprise'] = data['epsActual'] - data['epsEstimate']
            data['eps_surprise_pct'] = (data['eps_surprise'] / data['epsEstimate'].abs()) * 100
            
            # Beat/miss indicators
            data['earnings_beat'] = (data['eps_surprise'] > 0).astype(int)
            data['earnings_miss'] = (data['eps_surprise'] < 0).astype(int)
            
            # Absolute surprise magnitude
            data['eps_surprise_magnitude'] = data['eps_surprise'].abs()
        
        return data
    
    def _create_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create temporal features from earnings data."""
        if 'Date' not in data.columns:
            return data
        
        # Quarter and year features
        data['quarter'] = data['Date'].dt.quarter
        data['year'] = data['Date'].dt.year
        data['month'] = data['Date'].dt.month
        
        # Days since last earnings (within symbol)
        if 'Symbol' in data.columns:
            data = data.sort_values(['Symbol', 'Date'])
            data['days_since_last_earnings'] = data.groupby('Symbol')['Date'].diff().dt.days
        
        return data
    
    def _create_surprise_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create earnings surprise trend features."""
        if 'Symbol' not in data.columns or 'eps_surprise' not in data.columns:
            return data
        
        # Sort by symbol and date
        data = data.sort_values(['Symbol', 'Date'])
        
        # Rolling surprise metrics
        for window in [2, 4]:
            col_name = f'eps_surprise_trend_{window}q'
            data[col_name] = data.groupby('Symbol')['eps_surprise'].rolling(
                window=window, min_periods=1
            ).mean().reset_index(level=0, drop=True)
            
            # Surprise consistency
            consistency_col = f'surprise_consistency_{window}q'
            data[consistency_col] = data.groupby('Symbol')['earnings_beat'].rolling(
                window=window, min_periods=1
            ).mean().reset_index(level=0, drop=True)
        
        return data
    
    def _process_single_statement(self, stmt_data: pd.DataFrame, stmt_type: str) -> pd.DataFrame:
        """Process a single financial statement."""
        processed = stmt_data.copy()
        
        # Key metrics extraction based on statement type
        if stmt_type == 'income_stmt':
            processed = self._extract_income_metrics(processed)
        elif stmt_type == 'balance_sheet':
            processed = self._extract_balance_sheet_metrics(processed)
        elif stmt_type == 'cash_flow':
            processed = self._extract_cash_flow_metrics(processed)
        
        return processed
    
    def _extract_income_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract key metrics from income statement."""
        # Map common income statement metrics
        metric_mapping = {
            'Total Revenue': 'revenue',
            'Net Income': 'net_income',
            'Operating Income': 'operating_income',
            'Gross Profit': 'gross_profit',
            'EBITDA': 'ebitda',
            'EBIT': 'ebit'
        }
        
        for original_col, new_col in metric_mapping.items():
            if original_col in data.columns:
                data[new_col] = data[original_col]
        
        return data
    
    def _extract_balance_sheet_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract key metrics from balance sheet."""
        metric_mapping = {
            'Total Assets': 'total_assets',
            'Total Debt': 'total_debt',
            'Stockholders Equity': 'shareholders_equity',
            'Cash And Cash Equivalents': 'cash_and_equivalents',
            'Current Assets': 'current_assets',
            'Current Liabilities': 'current_liabilities'
        }
        
        for original_col, new_col in metric_mapping.items():
            if original_col in data.columns:
                data[new_col] = data[original_col]
        
        return data
    
    def _extract_cash_flow_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract key metrics from cash flow statement."""
        metric_mapping = {
            'Operating Cash Flow': 'operating_cash_flow',
            'Free Cash Flow': 'free_cash_flow',
            'Capital Expenditure': 'capex'
        }
        
        for original_col, new_col in metric_mapping.items():
            if original_col in data.columns:
                data[new_col] = data[original_col]
        
        return data
    
    def _calculate_financial_ratios(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate financial ratios from the combined data."""
        # Profitability ratios
        if 'net_income' in data.columns and 'revenue' in data.columns:
            data['profit_margin'] = data['net_income'] / data['revenue']
        
        if 'net_income' in data.columns and 'total_assets' in data.columns:
            data['roa'] = data['net_income'] / data['total_assets']  # Return on Assets
        
        if 'net_income' in data.columns and 'shareholders_equity' in data.columns:
            data['roe'] = data['net_income'] / data['shareholders_equity']  # Return on Equity
        
        # Liquidity ratios
        if 'current_assets' in data.columns and 'current_liabilities' in data.columns:
            data['current_ratio'] = data['current_assets'] / data['current_liabilities']
        
        # Leverage ratios
        if 'total_debt' in data.columns and 'total_assets' in data.columns:
            data['debt_to_assets'] = data['total_debt'] / data['total_assets']
        
        if 'total_debt' in data.columns and 'shareholders_equity' in data.columns:
            data['debt_to_equity'] = data['total_debt'] / data['shareholders_equity']
        
        return data
    
    def _calculate_growth_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate growth metrics."""
        if 'Symbol' not in data.columns or 'Date' not in data.columns:
            return data
        
        # Sort by symbol and date
        data = data.sort_values(['Symbol', 'Date'])
        
        # Calculate year-over-year growth for key metrics
        growth_metrics = ['revenue', 'net_income', 'operating_income', 'total_assets']
        
        for metric in growth_metrics:
            if metric in data.columns:
                # Calculate YoY growth (4 quarters ago)
                yoy_col = f'{metric}_yoy_growth'
                data[yoy_col] = data.groupby('Symbol')[metric].pct_change(periods=4) * 100
                
                # Calculate QoQ growth
                qoq_col = f'{metric}_qoq_growth'
                data[qoq_col] = data.groupby('Symbol')[metric].pct_change(periods=1) * 100
        
        return data
    
    def _calculate_event_features(
        self,
        price_window: pd.DataFrame,
        earnings_date: pd.Timestamp,
        earnings_row: pd.Series,
        window_days: int
    ) -> Dict[str, Any]:
        """Calculate features around earnings announcement events."""
        try:
            # Get pre and post earnings periods
            pre_earnings = price_window[price_window['Date'] < earnings_date]
            post_earnings = price_window[price_window['Date'] > earnings_date]
            
            if pre_earnings.empty or post_earnings.empty:
                return None
            
            # Calculate price movements
            pre_close = pre_earnings['Close'].iloc[-1] if not pre_earnings.empty else None
            post_close = post_earnings['Close'].iloc[0] if not post_earnings.empty else None
            
            features = {
                'Date': earnings_date,
                'Symbol': earnings_row.get('Symbol', ''),
                'earnings_date': earnings_date
            }
            
            if pre_close is not None and post_close is not None:
                # Price reaction
                features['price_reaction'] = (post_close - pre_close) / pre_close * 100
                features['price_reaction_abs'] = abs(features['price_reaction'])
            
            # Volume analysis if available
            if 'Volume' in price_window.columns:
                avg_volume_pre = pre_earnings['Volume'].mean()
                earnings_day_volume = price_window[
                    price_window['Date'] == earnings_date
                ]['Volume'].iloc[0] if not price_window[price_window['Date'] == earnings_date].empty else None
                
                if earnings_day_volume is not None and avg_volume_pre > 0:
                    features['volume_spike'] = earnings_day_volume / avg_volume_pre
            
            # Add earnings metrics if available
            for col in ['EPS Estimate', 'Reported EPS', 'Surprise(%)', 'Event Type']:
                if col in earnings_row:
                    clean_col = col.lower().replace('(', '').replace(')', '').replace('%', '_pct').replace(' ', '_')
                    features[clean_col] = earnings_row[col]
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating event features: {e}")
            return None
    
    def _normalize_features(self, data: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Normalize numerical features using robust scaling."""
        # Identify numerical columns to normalize
        exclude_cols = ['Date', 'Symbol', 'quarter', 'year', 'month', 'earnings_beat', 'earnings_miss']
        numerical_cols = [
            col for col in data.columns 
            if data[col].dtype in ['float64', 'int64'] and col not in exclude_cols
        ]
        
        if not numerical_cols:
            return data
        
        # Use RobustScaler to handle outliers better than StandardScaler
        scaler_key = f"{data_type}_scaler"
        if scaler_key not in self.scalers:
            self.scalers[scaler_key] = RobustScaler()
        
        # Fit and transform numerical features
        data_normalized = data.copy()
        
        # Handle missing values before scaling
        for col in numerical_cols:
            if data_normalized[col].isnull().any():
                # Fill with median for robust scaling
                median_val = data_normalized[col].median()
                data_normalized[col] = data_normalized[col].fillna(median_val)
        
        try:
            # Scale the features
            scaled_values = self.scalers[scaler_key].fit_transform(data_normalized[numerical_cols])
            data_normalized[numerical_cols] = scaled_values
            
            logger.debug(f"Normalized {len(numerical_cols)} features using RobustScaler")
            
        except Exception as e:
            logger.error(f"Error normalizing features: {e}")
            # Return original data if normalization fails
            return data
        
        return data_normalized
    
    def get_feature_importance_weights(self) -> Dict[str, float]:
        """
        Get suggested feature importance weights for ML models.
        
        Returns:
            Dictionary mapping feature types to importance weights
        """
        return {
            # Earnings surprise features (high importance)
            'eps_surprise': 1.0,
            'eps_surprise_pct': 1.0,
            'earnings_beat': 0.8,
            'surprise_consistency_4q': 0.9,
            
            # Financial health features (medium-high importance)
            'profit_margin': 0.7,
            'roa': 0.7,
            'roe': 0.7,
            'current_ratio': 0.6,
            'debt_to_equity': 0.6,
            
            # Growth features (medium importance)
            'revenue_yoy_growth': 0.6,
            'net_income_yoy_growth': 0.6,
            
            # Event features (medium importance)
            'price_reaction': 0.5,
            'volume_spike': 0.4,
            
            # Temporal features (low importance)
            'quarter': 0.2,
            'days_since_last_earnings': 0.3
        }