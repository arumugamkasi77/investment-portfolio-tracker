import asyncio
import yfinance as yf
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class MarketDataService:
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.cache = {}
        self.cache_duration = timedelta(seconds=3)  # Cache for 3 seconds so auto-refresh every 5 seconds gets fresh data
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache:
            return False
        
        cached_time = self.cache[symbol].get('timestamp')
        if not cached_time:
            return False
            
        return datetime.now() - cached_time < self.cache_duration
    
    async def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """Get current stock price using Yahoo Finance with proper caching"""
        symbol = symbol.upper()
        
        # Check cache first (unless force refresh is requested)
        if not force_refresh and self._is_cache_valid(symbol):
            return self.cache[symbol]['data']
        
        # Handle CASH_USD specially - always return 1.0
        if symbol == "CASH_USD":
            cash_data = {
                'symbol': 'CASH_USD',
                'price': 1.0,
                'change': 0.0,
                'change_percent': '0.00',
                'volume': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Cash Position (Fixed Value)',
                'currency': 'USD'
            }
            self._cache_data(symbol, cash_data)
            return cash_data
        
        # Check if this is an option symbol
        if self._is_option_symbol(symbol):
            price_data = await self._get_option_price(symbol)
            if price_data:
                self._cache_data(symbol, price_data)
                return price_data
        
        # Try Alpha Vantage first (if API key available)
        if self.alpha_vantage_key:
            price_data = await self._get_alpha_vantage_price(symbol)
            if price_data:
                self._cache_data(symbol, price_data)
                return price_data
        
        # Use Yahoo Finance (primary method)
        price_data = await self._get_yahoo_finance_price(symbol)
        if price_data:
            self._cache_data(symbol, price_data)
            return price_data
        
        # If all methods fail, log the error and return None
        print(f"WARNING: All market data methods failed for {symbol}. Using fallback price.")
        return None
    
    async def get_stock_price_fresh(self, symbol: str) -> Optional[Dict]:
        """Get current stock price with force refresh (bypasses cache) - for auto-refresh scenarios"""
        return await self.get_stock_price(symbol, force_refresh=True)
    
    async def get_best_available_price(self, symbol: str) -> Optional[Dict]:
        """Get the best available price prioritizing extended hours data"""
        symbol = symbol.upper()
        
        # Handle CASH_USD specially
        if symbol == "CASH_USD":
            return {
                'symbol': 'CASH_USD',
                'price': 1.0,
                'change': 0.0,
                'change_percent': '0.00',
                'volume': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Cash Position (Fixed Value)',
                'currency': 'USD',
                'price_type': 'cash'
            }
        
        # Try to get fresh data with extended hours priority
        try:
            price_data = await self._get_yahoo_finance_price(symbol)
            if price_data:
                return price_data
        except Exception as e:
            print(f"Error fetching extended hours data for {symbol}: {e}")
        
        # Fallback to regular method
        return await self.get_stock_price(symbol, force_refresh=True)
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Get prices for multiple symbols concurrently - FIXED to avoid race conditions"""
        results = {}
        
        # Handle CASH_USD specially
        if "CASH_USD" in symbols:
            results["CASH_USD"] = {
                'symbol': 'CASH_USD',
                'price': 1.0,
                'change': 0.0,
                'change_percent': '0.00',
                'volume': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Cash Position (Fixed Value)',
                'currency': 'USD',
                'price_type': 'cash'
            }
            symbols = [s for s in symbols if s != "CASH_USD"]
        
        # Batch fetch all other symbols using yfinance directly to avoid race conditions
        if symbols:
            try:
                loop = asyncio.get_event_loop()
                
                def batch_fetch_prices():
                    import yfinance as yf
                    batch_results = {}
                    
                    for symbol in symbols:
                        try:
                            ticker = yf.Ticker(symbol)
                            info = ticker.info
                            
                            if info and 'regularMarketPrice' in info and info['regularMarketPrice']:
                                # Priority order: Pre-market > Post-market > Regular market
                                current_price = None
                                price_source = "Regular Market"
                                
                                # Check for pre-market price
                                if 'preMarketPrice' in info and info['preMarketPrice'] and info['preMarketPrice'] > 0:
                                    current_price = float(info['preMarketPrice'])
                                    price_source = "Pre-Market"
                                # Check for post-market price
                                elif 'postMarketPrice' in info and info['postMarketPrice'] and info['postMarketPrice'] > 0:
                                    current_price = float(info['postMarketPrice'])
                                    price_source = "Post-Market"
                                # Use regular market price
                                else:
                                    current_price = float(info['regularMarketPrice'])
                                    price_source = "Regular Market"
                                
                                previous_close = float(info.get('previousClose', current_price))
                                change = current_price - previous_close
                                change_percent = (change / previous_close * 100) if previous_close else 0
                                
                                batch_results[symbol] = {
                                    'symbol': symbol,
                                    'price': current_price,
                                    'change': change,
                                    'change_percent': f"{change_percent:.2f}",
                                    'volume': int(info.get('volume', 0)),
                                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                                    'source': f'Yahoo Finance ({price_source})',
                                    'currency': 'USD',
                                    'price_type': price_source.lower().replace('-', '_')
                                }
                            else:
                                batch_results[symbol] = None
                                
                        except Exception as e:
                            print(f"Error fetching price for {symbol} in batch: {e}")
                            batch_results[symbol] = None
                    
                    return batch_results
                
                # Execute batch fetch in thread pool
                batch_results = await loop.run_in_executor(None, batch_fetch_prices)
                results.update(batch_results)
                
            except Exception as e:
                print(f"Error in batch price fetch: {e}")
                # Fallback: set None for failed symbols
                for symbol in symbols:
                    if symbol not in results:
                        results[symbol] = None
        
        print(f"🔧 DEBUG: Batch fetch completed for {len(symbols)} symbols: {list(results.keys())}")
        return results
    
    async def _get_alpha_vantage_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price from Alpha Vantage API"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('Global Quote', {})
                        
                        if quote and '05. price' in quote:
                            return {
                                'symbol': symbol,
                                'price': float(quote['05. price']),
                                'change': float(quote['09. change']),
                                'change_percent': quote['10. change percent'].replace('%', ''),
                                'volume': int(quote['06. volume']) if quote['06. volume'].isdigit() else 0,
                                'last_updated': quote['07. latest trading day'],
                                'source': 'Alpha Vantage'
                            }
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {e}")
        
        return None
    
    async def _get_yahoo_finance_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price from Yahoo Finance using yfinance library with extended hours priority"""
        try:
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def get_stock_data():
                ticker = yf.Ticker(symbol)
                # Use info method which is more reliable
                info = ticker.info
                
                if info and 'regularMarketPrice' in info and info['regularMarketPrice']:
                    # Priority order: Pre-market > Post-market > Regular market > Previous close
                    current_price = None
                    price_source = "Regular Market"
                    
                    # Check for pre-market price (4:00 AM - 9:30 AM ET)
                    if 'preMarketPrice' in info and info['preMarketPrice'] and info['preMarketPrice'] > 0:
                        current_price = float(info['preMarketPrice'])
                        price_source = "Pre-Market"
                    # Check for post-market price (4:00 PM - 8:00 PM ET)
                    elif 'postMarketPrice' in info and info['postMarketPrice'] and info['postMarketPrice'] > 0:
                        current_price = float(info['postMarketPrice'])
                        price_source = "Post-Market"
                    # Use regular market price
                    else:
                        current_price = float(info['regularMarketPrice'])
                        price_source = "Regular Market"
                    
                    previous_close = float(info.get('previousClose', current_price))
                    
                    change = current_price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close else 0
                    
                    return {
                        'symbol': symbol,
                        'price': current_price,
                        'change': change,
                        'change_percent': f"{change_percent:.2f}",
                        'volume': int(info.get('volume', 0)),
                        'last_updated': datetime.now().strftime('%Y-%m-%d'),
                        'source': f'Yahoo Finance ({price_source})',
                        'currency': 'USD',
                        'price_type': price_source.lower().replace('-', '_')  # pre_market, post_market, regular_market
                    }
                return None
            
            return await loop.run_in_executor(None, get_stock_data)
            
        except Exception as e:
            print(f"Yahoo Finance error for {symbol}: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
        return None
    
    def _is_option_symbol(self, symbol: str) -> bool:
        """Check if symbol is an option (e.g., YHOO150416C00030000)"""
        # Option symbols have format: SYMBOL + YYMMDD + TYPE + STRIKE
        # Examples: YHOO150416C00030000, AAPL250822C00227500
        import re
        option_pattern = r'^[A-Z]{1,5}\d{6}[CP]\d{8}$'
        return bool(re.match(option_pattern, symbol))
    
    async def _get_option_price(self, symbol: str) -> Optional[Dict]:
        """Get option price using Yahoo Finance"""
        try:
            # Parse option symbol to get underlying and option details
            option_info = self._parse_option_symbol(symbol)
            if not option_info:
                return None
            
            underlying_symbol = option_info['underlying']
            expiration_date = option_info['expiration']
            option_type = option_info['type']
            strike_price = option_info['strike']
            
            # Check if option is expired
            if self._is_option_expired(expiration_date):
                return {
                    'symbol': symbol,
                    'price': 0.0,  # Expired options have no value
                    'change': 0.0,
                    'change_percent': '0.00',
                    'volume': 0,
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'Expired Option (No Value)',
                    'currency': 'USD',
                    'option_details': {
                        'underlying': underlying_symbol,
                        'strike': strike_price,
                        'expiration': expiration_date.strftime('%Y-%m-%d'),
                        'type': option_type.upper(),
                        'status': 'EXPIRED'
                    }
                }
            
            print(f"Fetching option price for {symbol}: {underlying_symbol} {option_type} {strike_price} exp {expiration_date}")
            
            # Use Yahoo Finance to get option chain
            loop = asyncio.get_event_loop()
            
            def get_option_data():
                try:
                    ticker = yf.Ticker(underlying_symbol)
                    # Get options chain for the expiration date
                    options = ticker.options
                    
                    if expiration_date.strftime('%Y-%m-%d') in options:
                        option_chain = ticker.option_chain(expiration_date.strftime('%Y-%m-%d'))
                        
                        # Find the specific option with proper strike price comparison
                        print(f"DEBUG: Searching for {option_type.upper()} options at strike ${strike_price}")
                        
                        # Use approximate comparison for floating point precision
                        tolerance = 0.01  # $0.01 tolerance
                        
                        # Search in both calls and puts, then filter by contract symbol
                        # This is a workaround for Yahoo Finance API bug
                        all_options = []
                        
                        # Search calls
                        calls_at_strike = option_chain.calls[
                            (option_chain.calls['strike'] >= strike_price - tolerance) & 
                            (option_chain.calls['strike'] <= strike_price + tolerance)
                        ]
                        print(f"DEBUG: Found {len(calls_at_strike)} options in calls array at strike ${strike_price} (±${tolerance})")
                        
                        # Search puts
                        puts_at_strike = option_chain.puts[
                            (option_chain.puts['strike'] >= strike_price - tolerance) & 
                            (option_chain.puts['strike'] <= strike_price + tolerance)
                        ]
                        print(f"DEBUG: Found {len(puts_at_strike)} options in puts array at strike ${strike_price} (±${tolerance})")
                        
                        # Combine and filter by exact strike and correct option type
                        all_options = []
                        print(f"DEBUG: Checking calls array options:")
                        for _, option in calls_at_strike.iterrows():
                            contract_symbol = option.get('contractSymbol', 'N/A')
                            print(f"  Strike: ${option['strike']}, Contract: {contract_symbol}, Type: {'CALL' if 'C' in contract_symbol else 'PUT' if 'P' in contract_symbol else 'UNKNOWN'}")
                            if option['strike'] == strike_price and 'C' in contract_symbol:
                                all_options.append(option)
                                print(f"    ✅ Added CALL option")
                        
                        print(f"DEBUG: Checking puts array options:")
                        for _, option in puts_at_strike.iterrows():
                            contract_symbol = option.get('contractSymbol', 'N/A')
                            print(f"  Strike: ${option['strike']}, Contract: {contract_symbol}, Type: {'CALL' if 'C' in contract_symbol else 'PUT' if 'P' in contract_symbol else 'UNKNOWN'}")
                            if option['strike'] == strike_price and 'P' in contract_symbol:
                                all_options.append(option)
                                print(f"    ✅ Added PUT option")
                        
                        print(f"DEBUG: Found {len(all_options)} options with correct type and exact strike ${strike_price}")
                        
                        if all_options:
                            # Find the option with the correct type
                            target_option = None
                            for option in all_options:
                                contract_symbol = option.get('contractSymbol', '')
                                print(f"DEBUG: Checking option {contract_symbol} against target type {option_type.upper()}")
                                print(f"DEBUG: contract_symbol type: {type(contract_symbol)}, value: '{contract_symbol}'")
                                print(f"DEBUG: 'C' in contract_symbol: {'C' in contract_symbol}")
                                print(f"DEBUG: 'P' in contract_symbol: {'P' in contract_symbol}")
                                
                                # Check if this option matches our target type
                                # option_type is 'call' or 'put', but we need to check the symbol
                                if option_type.upper() == 'CALL' and 'C' in contract_symbol:
                                    target_option = option
                                    print(f"    ✅ Found CALL option")
                                    break
                                elif option_type.upper() == 'PUT' and 'P' in contract_symbol:
                                    target_option = option
                                    print(f"    ✅ Found PUT option")
                                    break
                            
                            if target_option:
                                print(f"DEBUG: Found target option: {target_option.get('contractSymbol', 'N/A')}")
                                # Create a simple dict-like object
                                option_data = type('OptionData', (), {
                                    'empty': False, 
                                    'iloc': lambda x: [target_option] if x == 0 else None
                                })()
                            else:
                                print(f"DEBUG: No target option found with correct type")
                                option_data = type('OptionData', (), {'empty': True})()
                        else:
                            option_data = type('OptionData', (), {'empty': True})()
                        
                        # Double-check we got the right option type
                        if not option_data.empty:
                            first_option = option_data.iloc[0]
                            print(f"DEBUG: Selected option contract symbol: {first_option.get('contractSymbol', 'N/A')}")
                            print(f"DEBUG: Option type from contract: {'CALL' if 'C' in first_option.get('contractSymbol', '') else 'PUT' if 'P' in first_option.get('contractSymbol', '') else 'UNKNOWN'}")
                            
                            # Verify we got the right option type
                            if option_type.upper() == 'C' and 'P' in first_option.get('contractSymbol', ''):
                                print(f"ERROR: Got PUT option when searching for CALL!")
                                print(f"ERROR: Expected CALL but found: {first_option.get('contractSymbol', 'N/A')}")
                            elif option_type.upper() == 'P' and 'C' in first_option.get('contractSymbol', ''):
                                print(f"ERROR: Got CALL option when searching for PUT!")
                                print(f"ERROR: Expected PUT but found: {first_option.get('contractSymbol', 'N/A')}")
                        
                        if not option_data.empty:
                            option_row = option_data.iloc[0]
                            
                            # Get all available price fields
                            last_price = option_row.get('lastPrice', 0)
                            bid = option_row.get('bid', 0)
                            ask = option_row.get('ask', 0)
                            mark_price = option_row.get('mark', 0)  # Mark price (mid-price)
                            
                            # Log all available price data for debugging
                            print(f"DEBUG: Found option with strike ${strike_price}")
                            print(f"DEBUG: lastPrice: ${last_price}, bid: ${bid}, ask: ${ask}, mark: ${mark_price}")
                            
                            # Use mark price if available, otherwise calculate mid-price, fallback to last price
                            if mark_price > 0:
                                current_price = mark_price
                                print(f"DEBUG: Using mark price: ${current_price}")
                            elif bid > 0 and ask > 0:
                                current_price = (bid + ask) / 2
                                print(f"DEBUG: Using calculated mid-price: ${current_price}")
                            else:
                                current_price = last_price
                                print(f"DEBUG: Using last price: ${current_price}")
                            
                            # Show all available columns for debugging
                            print(f"DEBUG: All available columns: {list(option_row.index)}")
                            print(f"DEBUG: Option row data: {option_row.to_dict()}")
                            
                            return {
                                'symbol': symbol,
                                'price': float(current_price),
                                'change': 0.0,  # Option change not easily available
                                'change_percent': '0.00',
                                'volume': int(option_row.get('volume', 0)),
                                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'Yahoo Finance Options',
                                'currency': 'USD',
                                'option_details': {
                                    'underlying': underlying_symbol,
                                    'strike': strike_price,
                                    'expiration': expiration_date.strftime('%Y-%m-%d'),
                                    'type': option_type.upper(),
                                    'status': 'ACTIVE'
                                }
                            }
                        else:
                            # Option not found in chain - might be expired or invalid
                            return {
                                'symbol': symbol,
                                'price': 0.0,
                                'change': 0.0,
                                'change_percent': '0.00',
                                'volume': 0,
                                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'Option Not Found in Chain',
                                'currency': 'USD',
                                'option_details': {
                                    'underlying': underlying_symbol,
                                    'strike': strike_price,
                                    'expiration': expiration_date.strftime('%Y-%m-%d'),
                                    'type': option_type.upper(),
                                    'status': 'NOT_FOUND'
                                }
                            }
                except Exception as e:
                    print(f"Error fetching option data: {e}")
                    return None
            
            return await loop.run_in_executor(None, get_option_data)
            
        except Exception as e:
            print(f"Option pricing error for {symbol}: {e}")
            return None
    
    def _is_option_expired(self, expiration_date: datetime) -> bool:
        """Check if option is expired"""
        return expiration_date.date() < datetime.now().date()
    
    def _get_option_expiration_status(self, expiration_date: datetime) -> str:
        """Get option expiration status"""
        if self._is_option_expired(expiration_date):
            return "EXPIRED"
        elif expiration_date.date() == datetime.now().date():
            return "EXPIRES_TODAY"
        else:
            return "ACTIVE"
    
    def _parse_option_symbol(self, symbol: str) -> Optional[Dict]:
        """Parse option symbol to extract components"""
        try:
            # Example: YHOO150416C00030000
            # YHOO = underlying symbol
            # 150416 = date (YYMMDD format)
            # C = call type
            # 00030000 = strike price (decimal 3 places from right, so 00030000 = $30.00)
            
            # Find the date part (6 digits after the symbol)
            import re
            match = re.match(r'^([A-Z]{1,5})(\d{6})([CP])(\d{8})$', symbol)
            if not match:
                return None
            
            underlying = match.group(1)
            date_str = match.group(2)
            option_type = match.group(3)
            strike_cents = match.group(4)
            
            # Parse date in YYMMDD format (as per user's option symbols)
            year_part = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            # Convert year to full year (assuming 20XX for recent options)
            year = 2000 + year_part
            
            print(f"Date {date_str} interpreted as YYMMDD: {year}-{month:02d}-{day:02d}")
            
            # Parse strike price (decimal point is 3 places from the right)
            # Example: 00030000 → 00030.000 → $30.00
            strike_price = float(strike_cents) / 1000
            
            print(f"Strike price: {strike_cents} = ${strike_price:.2f}")
            
            return {
                'underlying': underlying,
                'expiration': datetime(year, month, day),
                'type': 'call' if option_type == 'C' else 'put',
                'strike': strike_price
            }
            
        except Exception as e:
            print(f"Error parsing option symbol {symbol}: {e}")
            return None
    

    

    
    def _cache_data(self, symbol: str, data: Dict):
        """Cache the price data"""
        self.cache[symbol] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def get_cache_info(self) -> Dict:
        """Get information about cached data"""
        return {
            'cached_symbols': list(self.cache.keys()),
            'cache_count': len(self.cache),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }

# Global instance
market_data_service = MarketDataService()
