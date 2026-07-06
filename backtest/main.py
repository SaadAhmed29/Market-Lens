import argparse
import sys
from pathlib import Path


def _ensure_import_path():
	# Ensure project root is on sys.path when running the script directly
	root = Path(__file__).resolve().parent.parent
	if str(root) not in sys.path:
		sys.path.insert(0, str(root))


def main():
	_ensure_import_path()
	try:
		from backtest.backtest import BacktestEngine
	except Exception:
		# As a fallback, try importing using relative path
		from backtest.backtest import BacktestEngine

	parser = argparse.ArgumentParser(description="Run backtest pipeline")
	parser.add_argument("--config", "-c", default="backtest/config.yaml", help="config.yaml")
	args = parser.parse_args()

	engine = BacktestEngine(args.config)
	results = engine.run()
	print(results.get('trade_ledger'))
	print("Final balance:", results.get('final_balance'))
	print("Total net profit:", results.get('total_net_profit'))
	print(f"Trades: {results.get('total_trades')} | Wins: {results.get('win_count')} | Losses: {results.get('loss_count')}")
	print("HTML report written to:", results['html_report_path'])

if __name__ == "__main__":
	main()

