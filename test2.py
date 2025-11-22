import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional

class FundingArbitrageAnalyzer:
    """
    Анализатор арбитражных возможностей фандинга между биржами
    """
    
    def __init__(self, exchanges: List[str] = None):
        """
        Инициализация анализатора с поддержкой нескольких бирж
        
        Args:
            exchanges: Список бирж для анализа (по умолчанию основные биржи)
        """
        if exchanges is None:
            exchanges = ['mexc', 'gate', 'bybit', 'bingx', 'okx','bitget']
        
        self.exchanges = {}
        for exchange_id in exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'enableRateLimit': True,
                    # 'apiKey': 'your_key',  # опционально
                    # 'secret': 'your_secret',
                })
                print(f"✅ {exchange_id} инициализирован")
            except Exception as e:
                print(f"❌ Ошибка инициализации {exchange_id}: {e}")
    
    async def fetch_funding_data(self, symbol: str, days_history: int = 7) -> Dict:
        """
        Сбор всех данных по монете с разных бирж
        
        Args:
            symbol: Название монеты (например, 'BTC')
            days_history: Количество дней истории фандинга
            
        Returns:
            Словарь с данными по биржам
        """
        symbol = symbol.upper() + '/USDT:USDT'  # Форматируем для perpetual
        results = {}
        
        tasks = []
        for exchange_id, exchange in self.exchanges.items():
            tasks.append(self._fetch_single_exchange_data(exchange_id, exchange, symbol, days_history))
        
        # Параллельный сбор данных
        exchange_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        for data in exchange_data:
            if isinstance(data, dict) and data.get('success'):
                results[data['exchange']] = data

        for i,b in results.items():
            print(i)
            print(b)
            print('**************************')
        
        return results
    
    async def _fetch_single_exchange_data(self, exchange_id: str, exchange: ccxt.Exchange, 
                                        symbol: str, days_history: int) -> Dict:
        """
        Сбор данных с одной биржи
        """
        try:
            # Загружаем рынки для проверки доступности символа
            markets = exchange.load_markets()
            if symbol not in markets:
                return {'success': False, 'exchange': exchange_id, 'error': 'Symbol not available'}
            
            # Получаем текущие данные
            ticker = exchange.fetch_ticker(symbol)
            funding_rate = exchange.fetch_funding_rate(symbol)

            print(exchange_id)
            print(funding_rate)
            print('.......................................')
            
            # Получаем историю фандинга
            since_time = exchange.parse8601(
                (datetime.now() - timedelta(days=days_history)).isoformat())
            funding_history = exchange.fetch_funding_rate_history(symbol, since=since_time)
            
            # Получаем информацию об объемах и лимитах
            order_book = exchange.fetch_order_book(symbol)
            daily_volume = ticker.get('baseVolume', 0)
            
            coin_data =  {
                'success': True,
                'exchange': exchange_id,
                'symbol': symbol,
                'current_funding': float(funding_rate.get('fundingRate'))*100 if funding_rate else 0,
                'next_funding_time': funding_rate['info'].get('nextFundingTime') if funding_rate else None,
                #'funding_history': funding_history,
                'bid_price': ticker['bid'],
                'ask_price': ticker['ask'],
                'daily_volume': daily_volume,
                'bid_volume': order_book['bids'][0][1] if order_book['bids'] else 0,
                'ask_volume': order_book['asks'][0][1] if order_book['asks'] else 0,
                'timestamp': datetime.now()
            }
            #print(coin_data)
            return coin_data
            
        except Exception as e:
            return {'success': False, 'exchange': exchange_id, 'error': str(e)}
    
    def calculate_stability_metrics(self, funding_history: List, current_rate: float) -> Dict:
        """
        Расчет метрик стабильности фандинга
        
        Args:
            funding_history: История ставок фандинга
            current_rate: Текущая ставка
            
        Returns:
            Словарь с метриками стабильности
        """
        if not funding_history:
            return {
                'stability_1d': 0, 
                'stability_3d': 0, 
                'stability_7d': 0, 
                'flip_count': 0,
                'rate_std': 0
            }
        
        # Преобразуем историю в DataFrame для анализа
        df = pd.DataFrame([{
            'rate': entry['fundingRate'],
            'timestamp': entry['timestamp']
        } for entry in funding_history])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Анализ стабильности по периодам
        now = datetime.now()
        periods = {
            '1d': now - timedelta(days=1),
            '3d': now - timedelta(days=3), 
            '7d': now - timedelta(days=7)
        }
        
        stability_metrics = {}
        total_flip_count = 0
        
        for period_name, period_date in periods.items():
            period_data = df[df['timestamp'] >= period_date]
            if len(period_data) < 2:
                stability_metrics[f'stability_{period_name}'] = 0
                continue
            
            # Считаем изменения знака (флипы)
            signs = np.sign(period_data['rate'])
            flips = (signs != signs.shift()).sum() - 1  # Исключаем первый NaN
            total_flip_count = max(total_flip_count, flips)
            
            # Коэффициент стабильности (1 - нормализованное стандартное отклонение)
            std_dev = period_data['rate'].std()
            mean_abs_rate = abs(period_data['rate']).mean()
            stability = 1 - (std_dev / (mean_abs_rate + 0.0001))  # Защита от деления на 0
            
            stability_metrics[f'stability_{period_name}'] = max(0, min(1, stability))
        
        stability_metrics['flip_count'] = total_flip_count
        stability_metrics['current_rate'] = current_rate
        stability_metrics['rate_std'] = df['rate'].std()
        
        return stability_metrics
    
    def find_arbitrage_opportunities(self, data: Dict, min_volume: float = 10000, 
                                   min_stability: float = 0.7) -> List[Dict]:
        """
        Поиск арбитражных возможностей с фильтрацией
        
        Args:
            data: Данные по биржам
            min_volume: Минимальный суточный объем
            min_stability: Минимальный коэффициент стабильности
            
        Returns:
            Список арбитражных возможностей
        """
        opportunities = []
        exchanges = list(data.keys())
        
        # Создаем все возможные пары бирж
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                exch1, exch2 = exchanges[i], exchanges[j]
                
                opp = self._analyze_pair(data[exch1], data[exch2], min_volume, min_stability)
                if opp:
                    opportunities.append(opp)
        
        return opportunities
    
    def _analyze_pair(self, data1: Dict, data2: Dict, min_volume: float, min_stability: float) -> Optional[Dict]:
        """
        Анализ конкретной пары бирж
        """
        # Проверка минимального объема
        if data1['daily_volume'] < min_volume or data2['daily_volume'] < min_volume:
            return None
        
        # Расчет спредов
        price_spread_percent = abs(data1['bid_price'] - data2['ask_price']) / min(data1['bid_price'], data2['ask_price']) * 100
        funding_spread = data1['current_funding'] - data2['current_funding']
        
        # Определение направления арбитража
        if data1['bid_price'] > data2['ask_price']:
            direction = "BUY_AT_EXCH2_SELL_AT_EXCH1"
            net_spread = price_spread_percent - abs(funding_spread)
        elif data2['bid_price'] > data1['ask_price']:
            direction = "BUY_AT_EXCH1_SELL_AT_EXCH2" 
            net_spread = price_spread_percent - abs(funding_spread)
        else:
            return None
        
        # Анализ стабильности
        stability1 = self.calculate_stability_metrics(data1['funding_history'], data1['current_funding'])
        stability2 = self.calculate_stability_metrics(data2['funding_history'], data2['current_funding'])
        
        # Фильтр по стабильности
        min_pair_stability = min(stability1['stability_7d'], stability2['stability_7d'])
        if min_pair_stability < min_stability:
            return None
        
        # Фильтр по флипам
        if stability1['flip_count'] > 2 or stability2['flip_count'] > 2:
            return None
        
        return {
            'exchange_pair': f"{data1['exchange']} - {data2['exchange']}",
            'direction': direction,
            'price_spread_percent': price_spread_percent,
            'funding_spread': funding_spread,
            'net_spread_percent': net_spread,
            'stability_7d': min_pair_stability,
            'flip_count': max(stability1['flip_count'], stability2['flip_count']),
            'volume_data': {
                data1['exchange']: {
                    'daily_volume': data1['daily_volume'],
                    'bid_volume': data1['bid_volume'],
                    'ask_volume': data1['ask_volume']
                },
                data2['exchange']: {
                    'daily_volume': data2['daily_volume'],
                    'bid_volume': data2['bid_volume'], 
                    'ask_volume': data2['ask_volume']
                }
            },
            'funding_rates': {
                data1['exchange']: data1['current_funding'],
                data2['exchange']: data2['current_funding']
            },
            'timestamp': datetime.now()
        }
    
    def rank_opportunities(self, opportunities: List[Dict], rank_by: str = 'net_spread') -> List[Dict]:
        """
        Ранжирование возможностей по разным критериям
        
        Args:
            opportunities: Список возможностей
            rank_by: Критерий сортировки:
                    'net_spread' - по совокупному спреду
                    'price_spread' - по спреду цен
                    'funding_spread' - по спреду фандинга
                    'stability' - по стабильности
                    
        Returns:
            Отсортированный список возможностей
        """
        if not opportunities:
            return []
            
        if rank_by == 'net_spread':
            return sorted(opportunities, key=lambda x: x['net_spread_percent'], reverse=True)
        elif rank_by == 'price_spread':
            return sorted(opportunities, key=lambda x: x['price_spread_percent'], reverse=True)
        elif rank_by == 'funding_spread':
            return sorted(opportunities, key=lambda x: abs(x['funding_spread']), reverse=True)
        elif rank_by == 'stability':
            return sorted(opportunities, key=lambda x: x['stability_7d'], reverse=True)
        else:
            return opportunities
    
    def format_opportunity_output(self, opportunity: Dict) -> str:
        """
        Форматирование вывода одной возможности
        
        Args:
            opportunity: Данные возможности
            
        Returns:
            Отформатированная строка
        """
        color = "🟢" if opportunity['net_spread_percent'] > 0 else "🔴"
        
        output = f"{color} {opportunity['exchange_pair']}\n"
        output += f"   Направление: {opportunity['direction']}\n"
        output += f"   Совокупный спред: {opportunity['net_spread_percent']:.4f}%\n"
        output += f"   Спред цены: {opportunity['price_spread_percent']:.4f}%\n"
        output += f"   Спред фандинга: {opportunity['funding_spread']:.6f}\n"
        output += f"   Стабильность (7д): {opportunity['stability_7d']:.1%}\n"
        output += f"   Флипов: {opportunity['flip_count']}\n"
        
        # Добавляем информацию об объемах
        for exch, vol_data in opportunity['volume_data'].items():
            output += f"   {exch}: Объем ${vol_data['daily_volume']:,.0f}\n"
        
        return output


async def analyze_coin(coin: str, min_volume: float = 10000, min_stability: float = 0.7) -> Dict:
    """
    Основная функция анализа монеты
    
    Args:
        coin: Название монеты (например, 'BTC')
        min_volume: Минимальный объем
        min_stability: Минимальная стабильность
        
    Returns:
        Словарь с результатами анализа
    """
    analyzer = FundingArbitrageAnalyzer()
    
    print(f"🔍 Сканирую {coin}...")
    data = await analyzer.fetch_funding_data(coin, days_history=7)
    
    if not data:
        return {'success': False, 'error': 'Не удалось собрать данные'}
    
    print(f"✅ Получены данные с {len(data)} бирж")
    
    # Ищем возможности
    opportunities = analyzer.find_arbitrage_opportunities(
        data, 
        min_volume=min_volume,
        min_stability=min_stability
    )
    
    if not opportunities:
        return {'success': False, 'error': 'Арбитражные возможности не найдены'}
    
    # Ранжируем по разным критериям
    ranked_by_net = analyzer.rank_opportunities(opportunities, 'net_spread')
    ranked_by_price = analyzer.rank_opportunities(opportunities, 'price_spread')
    ranked_by_funding = analyzer.rank_opportunities(opportunities, 'funding_spread')
    ranked_by_stability = analyzer.rank_opportunities(opportunities, 'stability')
    
    return {
        'success': True,
        'coin': coin,
        'total_opportunities': len(opportunities),
        'ranked_by_net': ranked_by_net[:5],
        'ranked_by_price': ranked_by_price[:5],
        'ranked_by_funding': ranked_by_funding[:5],
        'ranked_by_stability': ranked_by_stability[:5],
        'all_opportunities': opportunities
    }


async def main():
    """
    Пример использования анализатора
    """
    result = await analyze_coin('BTC', min_volume=10000, min_stability=0.7)
    
    if not result['success']:
        print(f"❌ {result['error']}")
        return
    
    analyzer = FundingArbitrageAnalyzer()
    
    print(f"\n🎯 Найдено {result['total_opportunities']} возможностей")
    
    print("\n📊 ТОП-3 по совокупному спреду:")
    for opp in result['ranked_by_net'][:3]:
        print(analyzer.format_opportunity_output(opp))
    
    print("\n💰 ТОП-3 по спреду цен:")
    for opp in result['ranked_by_price'][:3]:
        print(analyzer.format_opportunity_output(opp))
    
    print("\n🛡️ ТОП-3 по стабильности:")
    for opp in result['ranked_by_stability'][:3]:
        print(analyzer.format_opportunity_output(opp))


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(main())
