from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from database import DatabaseManager, DatabaseError

class ReportService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_revenue_summary(self) -> Dict[str, float]:
        """Get revenue summary: total, this month, this year."""
        return self._db.fetch_revenue_summary()

    def get_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get sales trend for specified number of days."""
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        sales = self._db.fetch_sales_by_date_range(start_date, end_date)
        
        # Group by date
        trend_dict = {}
        for sale in sales:
            sale_date = sale[4].date() if hasattr(sale[4], 'date') else sale[4]
            if sale_date not in trend_dict:
                trend_dict[sale_date] = {'date': str(sale_date), 'quantity': 0, 'amount': 0.0}
            trend_dict[sale_date]['quantity'] += 1
            trend_dict[sale_date]['amount'] += float(sale[3] or 0)
        
        return sorted(trend_dict.values(), key=lambda x: x['date'])

    def get_stock_status_report(self) -> Dict[str, int]:
        """Get stock status breakdown."""
        breakdown = self._db.fetch_stock_status_breakdown()
        total = breakdown['available'] + breakdown['freezing'] + breakdown['sold']
        return {
            **breakdown,
            'total': total,
        }

    def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top products by sales."""
        products = self._db.fetch_top_products(limit)
        return [
            {
                'product_name': p[0],
                'sale_count': int(p[1]),
                'total_revenue': float(p[2] or 0),
            }
            for p in products
        ]

    def get_activity_summary(self) -> Dict[str, Any]:
        """Get activity summary."""
        total_events = self._db.fetch_activity_event_count()
        revenue = self.get_revenue_summary()
        stock_status = self.get_stock_status_report()
        
        return {
            'total_events': total_events,
            'total_revenue': revenue['total'],
            'this_month_revenue': revenue['this_month'],
            'this_year_revenue': revenue['this_year'],
            'available_stock': stock_status['available'],
            'freezing_stock': stock_status['freezing'],
            'sold_stock': stock_status['sold'],
            'total_stock': stock_status['total'],
        }
