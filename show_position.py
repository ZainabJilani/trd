import pyotp
from api_helper import ShoonyaApiPy

TOTP_SECRET = "A435644437VR523W3EV7K7AM76647YCZ"
TICK_SIZE = 0.05  # Tick size for rounding prices

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
        """Check for open positions and place a limit order if any position exists."""
        if not self.api:
            print("You must log in first!")
            return

        try:
            print("Fetching positions...")
            response = self.api.get_positions()

            # Check if the response is valid
            if response and response[0].get('stat') == 'Ok':
                positions = response
                for pos in positions:
                    symbol = pos['tsym']
                    quantity = int(pos['netqty'])
                    avg_price = float(pos['netavgprc'])
                    current_price = float(pos['lp'])

                    # If there is an open position, place a limit order
                    if quantity != 0:  # If there's a position (long or short)
                        print(f"Position found for {symbol}. Placing limit order...")

                        # If the position is long (buy order), place a sell order
                        if quantity > 0:
                            limit_price = avg_price * 1.05  # 1% above average price for sell
                            limit_price = self.round_to_tick_size(limit_price)
                            self.place_order(symbol, 'S', quantity, limit_price)
                        # If the position is short (sell order), place a buy order
                        elif quantity < 0:
                            limit_price = avg_price * 0.99  # 1% below average price for buy
                            limit_price = self.round_to_tick_size(limit_price)
                            self.place_order(symbol, 'B', abs(quantity), limit_price)

                    else:
                        print(f"No open position for {symbol}. No order placed.")
            else:
                print("No positions available.")
        except Exception as e:
            print(f"Error while fetching positions: {e}")

    def round_to_tick_size(self, price):
        """Round the price to the nearest multiple of the tick size."""
        return round(price / TICK_SIZE) * TICK_SIZE

    def place_order(self, symbol, action, quantity, limit_price):
        """Place a limit order."""
        print(f"Placing {action} order for {symbol} at price {limit_price} with quantity {quantity}.")

        try:
            # Replace 'symbol' with 'tradingsymbol' to match the correct parameter name for place_order
            order_response = self.api.place_order(
                tradingsymbol=symbol,  # Changed from 'symbol' to 'tradingsymbol'
                quantity=quantity,
                price=limit_price,
                price_type='LMT',
                product_type='I',  # Assuming 'I' for Intraday
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

# Example usage:
app = ShoonyaApp()
app.login()  # Perform login
app.show_position()  # Check positions and place order if any
