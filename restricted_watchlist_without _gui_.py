import pyotp
from api_helper import ShoonyaApiPy
import yfinance as yf

TOTP_SECRET = "A435644437VR523W3EV7K7AM76647YCZ"

class ShoonyaApp:
    def __init__(self):
        self.api = None

    def generate_totp(self):
        totp = pyotp.TOTP(TOTP_SECRET)
        return totp.now()

    def login(self):
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
            self.place_order()  # Automatically place the order after successful login
        else:
            error_msg = response.get('emsg', 'Login failed') if response else "No response from server."
            print(f"Login Failed: {error_msg}")

    def fetch_quotes(self, tradingsymbol):
        if not self.api:
            print("You must log in first!")
            return None
        try:
            data = self.api.get_quotes('NSE', tradingsymbol)
            if data and data.get('stat') == 'Ok':
                return data
            else:
                print("Failed to fetch quotes.")
                return None
        except Exception as e:
            print(f"Error fetching quotes: {e}")
            return None

    def fetch_nasdaq_composite_data(self):
        try:
            nasdaq = yf.Ticker('^IXIC')
            hist = nasdaq.history(period='2d')
            hist = hist.iloc[::-1]

            today_data = hist.iloc[0]
            yesterday_data = hist.iloc[1]

            today_open = round(today_data['Open'], 2)
            today_high = round(today_data['High'], 2)
            today_close = round(today_data['Close'], 2)
            prev_high = round(yesterday_data['High'], 2)
            prev_close = round(yesterday_data['Close'], 2)

            return today_open, today_high, today_close, prev_high, prev_close
        except Exception as e:
            print(f"Failed to fetch Nasdaq data: {e}")
            return "N/A", "N/A", "N/A", "N/A", "N/A"

    def fetch_infy_adr_data(self):
        try:
            infy_adr = yf.Ticker('INFY')
            hist = infy_adr.history(period='2d')
            hist = hist.iloc[::-1]

            today_data = hist.iloc[0]
            yesterday_data = hist.iloc[1]

            today_open = round(today_data['Open'], 2)
            today_high = round(today_data['High'], 2)
            today_close = round(today_data['Close'], 2)
            prev_high = round(yesterday_data['High'], 2)
            prev_close = round(yesterday_data['Close'], 2)

            return today_open, today_high, today_close, prev_high, prev_close
        except Exception as e:
            print(f"Failed to fetch Infy ADR data: {e}")
            return "N/A", "N/A", "N/A", "N/A", "N/A"

    def get_available_margin(self):
        """Fetch the available margin from the API."""
        if not self.api:
            print("You must log in first!")
            return None
        data = self.api.get_limits()
        if data and data.get('stat') == 'Ok':
            cash = float(data.get('cash', 0))
            payin = float(data.get('payin', 0))
            return cash + payin
        else:
            print("Failed to fetch margin data.")
            return None

    def place_order(self):
        if not self.api:
            print("You must log in first!")
            return

        coforge_data = self.fetch_quotes("COFORGE-EQ")
        wipro_data = self.fetch_quotes("WIPRO-EQ")
        icici_data = self.fetch_quotes("ICICIBANK-EQ")

        if not coforge_data or not wipro_data or not icici_data:
            return

        try:
            coforge_price = float(coforge_data.get('lp', '0'))
            wipro_price = float(wipro_data.get('lp', '0'))
            icici_price = float(icici_data.get('lp', '0'))
        except ValueError:
            print("Invalid price data received.")
            return

        nasdaq_open, nasdaq_high, nasdaq_close, nasdaq_prev_high, nasdaq_prev_close = self.fetch_nasdaq_composite_data()
        infy_adr_open, infy_adr_high, infy_adr_close, infy_adr_prev_high, infy_adr_prev_close = self.fetch_infy_adr_data()

        available_margin = self.get_available_margin()
        if not available_margin:
            print("Failed to fetch available margin.")
            return

        print(f"Available Margin: {available_margin}")

        decisions = [
            (nasdaq_high > nasdaq_prev_high and nasdaq_close > nasdaq_open and nasdaq_close > nasdaq_prev_close, "BUY COFORGE", "COFORGE-EQ", coforge_price),
            (nasdaq_high < nasdaq_prev_high and nasdaq_close < nasdaq_open and nasdaq_close < nasdaq_prev_close, "SELL WIPRO", "WIPRO-EQ", wipro_price),
            (infy_adr_high > infy_adr_prev_high and infy_adr_close > infy_adr_open and infy_adr_close > infy_adr_prev_close, "BUY COFORGE", "COFORGE-EQ", coforge_price),
            (infy_adr_close < infy_adr_open and infy_adr_close > infy_adr_prev_close, "SELL WIPRO", "WIPRO-EQ", wipro_price),
            (infy_adr_close < infy_adr_open and infy_adr_close < infy_adr_prev_close, "SELL WIPRO", "WIPRO-EQ", wipro_price)
        ]

        for condition, decision, symbol, price in decisions:
            if condition:
                tradingsymbol = symbol
                order_price = price
                buy_or_sell = 'B' if 'BUY' in decision else 'S'
                break
        else:
            decision = "BUY ICICI"
            tradingsymbol = "ICICIBANK-EQ"
            order_price = icici_price
            buy_or_sell = 'B'

        quantity = int((available_margin * 4.9) / order_price) if order_price > 0 else 0

        order_response = self.api.place_order(
            tradingsymbol=tradingsymbol,
            quantity=quantity,
            price=order_price,
            price_type='LMT',
            product_type='I',
            buy_or_sell=buy_or_sell,
            exchange='NSE',
            discloseqty=0,
            retention='DAY'
        )

        if order_response and order_response.get('stat') == 'Ok':
            print(f"Order placed successfully!")
            print(f"Tradingsymbol: {tradingsymbol}")
            print(f"Buy or Sell: {'BUY' if buy_or_sell == 'B' else 'SELL'}")
            print(f"Quantity: {quantity}")
        else:
            print(f"Order failed: {order_response}")

# Run the application
if __name__ == "__main__":
    app = ShoonyaApp()
    app.login()  # Automatically trigger login and place the order
