import time
import datetime
print("Script started at:", datetime.datetime.now())
import pyotp
from api_helper import ShoonyaApiPy

TOTP_SECRET = "A435644437VR523W3EV7K7AM76647YCZ"
TICK_SIZE = 0.05

class ShoonyaApp:
    def __init__(self):
        self.api = None

    def login(self):
        """Login function."""
        self.api = ShoonyaApiPy()
        otp = self.generate_totp()
        response = self.api.login(
            userid='FA54835',
            password='Galia@123',
            twoFA=otp,
            imei='abc1234',
            vendor_code='FA54835_U',
            api_secret='4064583afd28447250b9bc13a8aefb71'
        )
        if response and response.get('stat') == 'Ok':
            print("Login successful!")
        else:
            print("Login failed!")

    def generate_totp(self):
        """Generate TOTP for 2FA authentication."""
        totp = pyotp.TOTP(TOTP_SECRET)
        return totp.now()

    def show_position(self):
        """Check for open positions and place orders automatically."""
        while True:  # Infinite loop
            now = datetime.datetime.now()
            print("Current Local Time:", now)
            market_open = now.replace(hour=9, minute=15, second=0)
            market_close = now.replace(hour=15, minute=14, second=0)

            if market_open <= now <= market_close:  # Only run during market hours
                print(f"Checking positions at {now.strftime('%H:%M:%S')}...")

                try:
                    response = self.api.get_positions()
                    if response and response[0].get('stat') == 'Ok':
                        positions = response
                        for pos in positions:
                            symbol = pos['tsym']
                            quantity = int(pos['netqty'])
                            avg_price = float(pos['netavgprc'])

                            if quantity != 0:
                                print(f"Position found for {symbol}. Placing limit order...")

                                if quantity > 0:
                                    limit_price = self.round_to_tick_size(avg_price * 1.01)
                                    self.place_order(symbol, 'S', quantity, limit_price)
                                elif quantity < 0:
                                    limit_price = self.round_to_tick_size(avg_price * 0.99)
                                    self.place_order(symbol, 'B', abs(quantity), limit_price)
                            else:
                                print(f"No open position for {symbol}. No order placed.")
                    else:
                        print("No positions available.")
                except Exception as e:
                    print(f"Error while fetching positions: {e}")
            else:
                print("Market closed. Exiting script.")
                break  # Exit loop after market hours

            time.sleep(60)  # Wait 1 minute before checking again

    def round_to_tick_size(self, price):
        """Round price to nearest tick size."""
        return round(price / TICK_SIZE) * TICK_SIZE

    def place_order(self, symbol, action, quantity, limit_price):
        """Place a limit order."""
        print(f"Placing {action} order for {symbol} at {limit_price} with quantity {quantity}.")
        try:
            order_response = self.api.place_order(
                tradingsymbol=symbol,
                quantity=quantity,
                price=limit_price,
                price_type='LMT',
                product_type='I',
                buy_or_sell=action,
                exchange='NSE',
                discloseqty=0,
                retention='DAY'
            )
            if order_response and order_response.get('stat') == 'Ok':
                print(f"Order placed successfully for {symbol} at {limit_price}.")
            else:
                print("Failed to place order.")
        except Exception as e:
            print(f"Error while placing order: {e}")

# Run the script
app = ShoonyaApp()
app.login()
app.show_position()
