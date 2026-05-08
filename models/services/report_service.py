from typing import Dict, List, Any
from database import DatabaseManager


class ReportService:
    def __init__(self, database_manager: DatabaseManager):
        # Initializes object
        self._db = database_manager

    def get_revenue_summary(self) -> Dict[str, float]:
        # Gets summary
        """Get revenue summary: total, this month, this year."""
        return self._db.fetch_revenue_summary()

    def get_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        # Gets trend
        """Get daily sales trend aggregated by date, sorted ascending."""
        sales = self._db.fetch_sales_by_date_range(None, None, days) or []

        trend_dict: Dict[str, Dict[str, Any]] = {}
        for sale in sales:
            if isinstance(sale, dict):
                sale_date = sale.get('date')
                qty = int(sale.get('quantity', 0) or 0)
                amount = float(sale.get('amount', 0) or 0.0)
            else:
                try:
                    sale_date, qty, amount = str(sale[0]), int(sale[1]), float(sale[2] or 0)
                except Exception:
                    sale_date, qty, amount = str(sale), 0, 0.0

            key = str(sale_date)
            if key not in trend_dict:
                trend_dict[key] = {'date': key, 'quantity': 0, 'amount': 0.0}
            trend_dict[key]['quantity'] += qty
            trend_dict[key]['amount'] += amount

        return sorted(trend_dict.values(), key=lambda x: x['date'])

    def get_stock_status_report(self) -> Dict[str, int]:
        # Gets report
        """Get stock status breakdown."""
        breakdown = self._db.fetch_stock_status_breakdown()
        total = breakdown['available'] + breakdown['freezing'] + breakdown['sold']
        return {**breakdown, 'total': total}

    def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Gets products
        """Get top products by sales."""
        products = self._db.fetch_top_products(limit) or []
        result: List[Dict[str, Any]] = []
        for product in products:
            if isinstance(product, dict):
                result.append({
                    'product_name': product.get('product_name', 'No product name'),
                    'sale_count': int(product.get('sale_count', 0) or 0),
                    'total_revenue': float(product.get('total_revenue', 0) or 0.0),
                })
            else:
                try:
                    result.append({
                        'product_name': product[0],
                        'sale_count': int(product[1]),
                        'total_revenue': float(product[2] or 0),
                    })
                except Exception:
                    result.append({'product_name': str(product), 'sale_count': 0, 'total_revenue': 0.0})
        return result

    def get_activity_summary(self) -> Dict[str, Any]:
        # Gets summary
        """Get activity summary combining events, revenue, and stock status."""
        total_events = self._db.fetch_activity_event_count()
        revenue = self.get_revenue_summary()
        stock = self.get_stock_status_report()
        return {
            'total_events': total_events,
            'total_revenue': revenue['total'],
            'this_month_revenue': revenue['this_month'],
            'this_year_revenue': revenue['this_year'],
            'available_stock': stock['available'],
            'freezing_stock': stock['freezing'],
            'sold_stock': stock['sold'],
            'total_stock': stock['total'],
        }
