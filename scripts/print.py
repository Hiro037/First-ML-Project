import time
from datetime import datetime

timestamp = datetime.now()
cumulative_epsilon = -0.01104368
threshold = 0.01
beta = 1.5482213
alert_message = (
    f"\n{'=' * 80}\n"
    f"🚨 ALERT: ETH independent movement detected!\n"
    f"Time: {timestamp.isoformat()}\n"
    f"Cumulative epsilon: {cumulative_epsilon:.6f}"
    f" ({cumulative_epsilon * 100:.2f}%)\n"
    f"Threshold: {threshold * 100:.2f}%\n"
    f"Beta: {beta:.6f}\n"
    f"{'=' * 80}"
)

print(alert_message)