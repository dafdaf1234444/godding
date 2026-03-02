"""
Output management component for the investor analysis system.
Handles file I/O, directory management, git workflow, and report generation.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime
import json
import pandas as pd

from .config import InvestorConfig
from .exceptions import OutputError, GitWorkflowError

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages all output operations including files, directories, and git workflow."""
    
    def __init__(self, config: InvestorConfig, timestamp: str):
        """Initialize the output manager."""
        self.config = config
        self.timestamp = timestamp
        
        # Set up paths
        self.base_dir = Path.cwd()
        self.output_dir = self.base_dir / config.output.base_dir
        self.run_dir = self.output_dir / f"run_{timestamp}"
        
        logger.info("OutputManager initialized")
    
    def setup_output_directories(self) -> Path:
        """
        Set up output directories for the current run.
        
        Returns:
            Path to the run directory
            
        Raises:
            OutputError: If directory creation fails
        """
        try:
            logger.info("Setting up output directories")
            
            # Clean up old outputs first
            self._cleanup_old_outputs()
            
            # Create directories with legacy structure compatibility
            self.run_dir.mkdir(parents=True, exist_ok=True)
            (self.run_dir / "charts").mkdir(exist_ok=True)
            (self.run_dir / "data").mkdir(exist_ok=True)
            (self.run_dir / "reports").mkdir(exist_ok=True)
            (self.run_dir / "events").mkdir(exist_ok=True)
            (self.run_dir / "logs").mkdir(exist_ok=True)
            
            # Legacy forecasting subdirectories for compatibility
            forecasting_dir = self.run_dir / "forecasting"
            forecasting_dir.mkdir(exist_ok=True)
            (forecasting_dir / "charts").mkdir(exist_ok=True)
            (forecasting_dir / "models").mkdir(exist_ok=True)
            (forecasting_dir / "predictions").mkdir(exist_ok=True)
            (forecasting_dir / "anomalies").mkdir(exist_ok=True)
            
            # Create latest run symlink
            self._create_latest_run_link()
            
            logger.info(f"Created output directories in: {self.run_dir}")
            return self.run_dir
            
        except Exception as e:
            logger.error(f"Error setting up output directories: {e}")
            raise OutputError(f"Failed to setup output directories: {e}")
    
    def _cleanup_old_outputs(self):
        """Clean up old output directories."""
        try:
            if not self.output_dir.exists():
                return
            
            # Get all run directories
            run_dirs = [d for d in self.output_dir.iterdir() 
                       if d.is_dir() and d.name.startswith("run_")]
            
            # Sort by creation time (newest first)
            run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old runs beyond the limit
            max_runs = self.config.output.max_old_runs
            for old_dir in run_dirs[max_runs:]:
                logger.info(f"Removing old run directory: {old_dir.name}")
                shutil.rmtree(old_dir)
        
        except Exception as e:
            logger.error(f"Error cleaning up old outputs: {e}")
    
    def _create_latest_run_link(self):
        """Create a symlink to the latest run."""
        try:
            latest_link = self.output_dir / "latest_run"
            
            # Remove existing symlink
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            
            # Create new symlink
            latest_link.symlink_to(self.run_dir.name)
            logger.info(f"Created latest_run symlink to {self.run_dir.name}")
            
        except Exception as e:
            logger.error(f"Error creating latest run symlink: {e}")
    
    def save_analysis_results(self, data: Dict[str, pd.DataFrame], 
                            predictions: Dict[str, pd.DataFrame],
                            investment_signals: List[Dict[str, Any]],
                            visualizations: Dict[str, str],
                            holiday_analysis: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Save analysis results to files.
        
        Args:
            data: Raw data
            predictions: Forecast results
            investment_signals: Anomaly detection results
            visualizations: Visualization file paths
            
        Returns:
            Dictionary of saved file paths
        """
        logger.info("Saving analysis results")
        saved_files = {}
        
        try:
            data_dir = self.run_dir / "data"
            
            # Save raw data
            for symbol, symbol_data in data.items():
                data_file = data_dir / f"{symbol}_data.csv"
                symbol_data.to_csv(data_file, index=True)
                saved_files[f"{symbol}_data"] = str(data_file)
            
            # Save predictions
            if predictions:
                # Create predictions directory
                predictions_dir = self.run_dir / "forecasting" / "predictions"
                predictions_dir.mkdir(parents=True, exist_ok=True)
                
                for symbol, pred_data in predictions.items():
                    # Save to data directory (for backward compatibility)
                    pred_file_data = data_dir / f"{symbol}_predictions.csv"
                    pred_data.to_csv(pred_file_data, index=True)
                    saved_files[f"{symbol}_predictions_data"] = str(pred_file_data)
                    
                    # Save to forecasting/predictions directory (for consistency)
                    pred_file_forecasting = predictions_dir / f"{symbol}_predictions.csv"
                    pred_data.to_csv(pred_file_forecasting, index=True)
                    saved_files[f"{symbol}_predictions"] = str(pred_file_forecasting)
            
            # Save investment signals
            if investment_signals:
                signals_file = data_dir / "investment_signals.json"
                
                # Convert AnomalySignal objects to dictionaries for JSON serialization
                serializable_signals = []
                for signal in investment_signals:
                    if hasattr(signal, '__dict__'):
                        # Convert AnomalySignal to dict
                        signal_dict = {
                            'symbol': signal.symbol,
                            'date': signal.date.isoformat() if hasattr(signal.date, 'isoformat') else str(signal.date),
                            'anomaly_type': signal.anomaly_type,
                            'severity': signal.severity,
                            'confidence': signal.confidence,
                            'signal': signal.signal,
                            'description': signal.description,
                            'time_frame': signal.time_frame,
                            'expected_duration': signal.expected_duration,
                            'potential_return': signal.potential_return,
                            'risk_level': signal.risk_level
                        }
                        serializable_signals.append(signal_dict)
                    elif isinstance(signal, dict):
                        serializable_signals.append(signal)
                    else:
                        # Fallback for unknown types
                        serializable_signals.append(str(signal))
                
                # Save to main data directory (for backward compatibility)
                with open(signals_file, 'w') as f:
                    json.dump(serializable_signals, f, indent=2, default=str)
                saved_files['investment_signals'] = str(signals_file)
                
                # Also save detailed anomaly files to forecasting/anomalies/
                self._save_anomaly_analysis(serializable_signals, saved_files)
            
            # Save holiday analysis results
            if holiday_analysis:
                holiday_file = data_dir / "holiday_analysis.json"
                
                # Convert holiday effects and seasonal patterns to serializable format
                serializable_holiday_data = {}
                
                for symbol, symbol_data in holiday_analysis.items():
                    if symbol in ['holiday_effects', 'seasonal_patterns', 'reports']:
                        symbol_results = {}
                        
                        for subsymbol, effects_or_patterns in symbol_data.items():
                            if isinstance(effects_or_patterns, list):
                                # Convert HolidayEffect or SeasonalPattern objects to dicts
                                serializable_list = []
                                for item in effects_or_patterns:
                                    if hasattr(item, '__dict__'):
                                        item_dict = {
                                            key: value.isoformat() if hasattr(value, 'isoformat') else value
                                            for key, value in item.__dict__.items()
                                        }
                                        serializable_list.append(item_dict)
                                    else:
                                        serializable_list.append(item)
                                symbol_results[subsymbol] = serializable_list
                            else:
                                symbol_results[subsymbol] = effects_or_patterns
                        
                        serializable_holiday_data[symbol] = symbol_results
                    else:
                        serializable_holiday_data[symbol] = symbol_data
                
                with open(holiday_file, 'w') as f:
                    json.dump(serializable_holiday_data, f, indent=2, default=str)
                saved_files['holiday_analysis'] = str(holiday_file)
            
            # Copy visualization paths to saved_files
            saved_files.update(visualizations)
            
            logger.info(f"Saved {len(saved_files)} result files")
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            return saved_files
    
    def generate_html_report(self, data: Dict[str, pd.DataFrame], 
                           predictions: Dict[str, pd.DataFrame],
                           investment_signals: List[Dict[str, Any]],
                           visualizations: Dict[str, str],
                           analysis_duration: float) -> str:
        """
        Generate comprehensive HTML report.
        
        Args:
            data: Raw data
            predictions: Forecast results  
            investment_signals: Investment signals
            visualizations: Visualization file paths
            analysis_duration: Analysis execution time
            
        Returns:
            Path to the generated HTML report
        """
        if not self.config.output.generate_html_report:
            logger.info("HTML report generation disabled")
            return ""
        
        logger.info("Generating HTML report")
        
        try:
            report_path = self.run_dir / "reports" / "analysis_report.html"
            
            # Calculate summary statistics
            total_signals = len(investment_signals)
            signal_breakdown = {}
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
                signal_breakdown[signal_type] = signal_breakdown.get(signal_type, 0) + 1
            
            # Generate HTML content
            html_content = self._generate_html_content(
                data, predictions, investment_signals, visualizations,
                analysis_duration, total_signals, signal_breakdown
            )
            
            # Write HTML file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return ""
    
    def _generate_html_content(self, data: Dict[str, pd.DataFrame], 
                             predictions: Dict[str, pd.DataFrame],
                             investment_signals: List[Dict[str, Any]],
                             visualizations: Dict[str, str],
                             analysis_duration: float,
                             total_signals: int,
                             signal_breakdown: Dict[str, int]) -> str:
        """Generate the HTML content for the report."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Investment Analysis Report - {self.timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary-item {{ display: inline-block; margin: 10px 20px; }}
                .summary-label {{ font-weight: bold; color: #2c3e50; }}
                .summary-value {{ color: #27ae60; font-size: 1.2em; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .section {{ margin-bottom: 30px; }}
                .visualization {{ text-align: center; margin: 20px 0; }}
                .visualization img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Investment Analysis Report</h1>
                <p style="text-align: center; color: #7f8c8d;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="summary">
                    <h2>Executive Summary</h2>
                    <div class="summary-item">
                        <span class="summary-label">Symbols Analyzed:</span>
                        <span class="summary-value">{len(data)}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Total Signals:</span>
                        <span class="summary-value">{total_signals}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Analysis Duration:</span>
                        <span class="summary-value">{analysis_duration:.1f}s</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Forecasts Generated:</span>
                        <span class="summary-value">{len(predictions)}</span>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Investment Signals Breakdown</h2>
                    <table>
                        <tr><th>Signal Type</th><th>Count</th><th>Percentage</th></tr>
        """
        
        for signal_type, count in signal_breakdown.items():
            percentage = (count / total_signals * 100) if total_signals > 0 else 0
            html_content += f"<tr><td>{signal_type.title()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Data Overview</h2>
                <table>
                    <tr><th>Symbol</th><th>Data Points</th><th>Date Range</th><th>Latest Price</th></tr>
        """
        
        for symbol, df in data.items():
            latest_price = df['Close'].iloc[-1] if 'Close' in df.columns and not df.empty else "N/A"
            try:
                if 'Date' in df.columns:
                    start_date = pd.to_datetime(df['Date'].min()).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(df['Date'].max()).strftime('%Y-%m-%d')
                elif hasattr(df.index, 'min') and pd.api.types.is_datetime64_any_dtype(df.index):
                    start_date = pd.to_datetime(df.index.min()).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(df.index.max()).strftime('%Y-%m-%d')
                else:
                    start_date = "Unknown"
                    end_date = "Unknown"
            except Exception:
                start_date = "Unknown"
                end_date = "Unknown"
            
            price_str = f"${latest_price:.2f}" if isinstance(latest_price, (int, float)) else "N/A"
            html_content += f"<tr><td>{symbol}</td><td>{len(df)}</td><td>{start_date} to {end_date}</td><td>{price_str}</td></tr>"
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Generated Visualizations</h2>
                <ul>
        """
        
        for viz_name, viz_path in visualizations.items():
            if viz_path and Path(viz_path).exists():
                # Convert absolute path to relative path for HTML
                relative_path = Path(viz_path).relative_to(self.run_dir)
                html_content += f'<li><a href="{relative_path}">{viz_name.replace("_", " ").title()}</a></li>'
        
        html_content += """
                </ul>
            </div>
            
            <div class="footer">
                <p>Generated by Investor Analysis System v{version}</p>
                <p>Report ID: {timestamp}</p>
            </div>
        </div>
        </body>
        </html>
        """.format(version=self.config.system.version, timestamp=self.timestamp)
        
        return html_content
    
    def manage_git_workflow(self) -> bool:
        """
        Manage git workflow for the analysis results.
        
        Returns:
            True if git operations succeeded, False otherwise
        """
        if not self.config.output.enable_git_integration:
            logger.info("Git integration disabled")
            return True
        
        logger.info("Managing git workflow")
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            if result.returncode != 0:
                logger.warning("Not in a git repository, skipping git workflow")
                return False
            
            # Add files to git (force add if ignored)
            subprocess.run(['git', 'add', '-f', str(self.output_dir)], 
                          cwd=self.base_dir, check=True)
            
            # Create commit message
            commit_message = f"""analysis: Add analysis results from {self.timestamp}

Automated analysis run completed:
- Run ID: {self.timestamp}
- Output directory: {self.run_dir.name}
- Generated comprehensive investment analysis

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"""
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', commit_message], 
                          cwd=self.base_dir, check=True)
            
            # Push to remote (optional)
            try:
                subprocess.run(['git', 'push'], 
                              cwd=self.base_dir, check=True, timeout=30)
                logger.info("Successfully pushed to remote repository")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.warning(f"Could not push to remote: {e}")
            
            logger.info("Git workflow completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            raise GitWorkflowError(f"Git workflow failed: {e}")
        except Exception as e:
            logger.error(f"Error in git workflow: {e}")
            return False
    
    def _save_anomaly_analysis(self, signals: List[dict], saved_files: dict) -> None:
        """Save detailed anomaly analysis files to forecasting/anomalies/ directory."""
        try:
            import pandas as pd
            from datetime import datetime
            
            anomalies_dir = self.run_dir / "forecasting" / "anomalies"
            anomalies_dir.mkdir(parents=True, exist_ok=True)
            
            if not signals:
                return
            
            # Convert signals to DataFrame
            df = pd.DataFrame(signals)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save comprehensive anomaly signals CSV
            anomaly_csv = anomalies_dir / f"anomaly_signals_{timestamp}.csv"
            df.to_csv(anomaly_csv, index=False)
            saved_files['anomaly_signals_csv'] = str(anomaly_csv)
            
            # Save anomaly summary by type
            if 'anomaly_type' in df.columns:
                type_summary = df.groupby('anomaly_type').agg({
                    'severity': 'count',
                    'confidence': 'mean'
                }).rename(columns={'severity': 'count', 'confidence': 'avg_confidence'})
                
                summary_file = anomalies_dir / f"anomaly_type_summary_{timestamp}.csv"
                type_summary.to_csv(summary_file)
                saved_files['anomaly_type_summary'] = str(summary_file)
            
            # Save signals by symbol
            if 'symbol' in df.columns:
                for symbol in df['symbol'].unique():
                    symbol_signals = df[df['symbol'] == symbol]
                    symbol_file = anomalies_dir / f"{symbol}_anomalies_{timestamp}.csv"
                    symbol_signals.to_csv(symbol_file, index=False)
                    saved_files[f'{symbol}_anomalies'] = str(symbol_file)
            
            # Save severity analysis
            if 'severity' in df.columns:
                severity_counts = df['severity'].value_counts()
                severity_file = anomalies_dir / f"severity_analysis_{timestamp}.json"
                
                import json
                with open(severity_file, 'w') as f:
                    json.dump(severity_counts.to_dict(), f, indent=2)
                saved_files['severity_analysis'] = str(severity_file)
            
            logger.info(f"Saved {len(signals)} anomaly signals to {anomalies_dir}")
            
        except Exception as e:
            logger.error(f"Error saving anomaly analysis: {e}")