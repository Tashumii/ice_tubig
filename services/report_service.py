from typing import Dict, List, Any
from database import DatabaseManager

class ReportService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_revenue_summary(self) -> Dict[str, float]:
        """Get revenue summary: total, this month, this year."""
        return self._db.fetch_revenue_summary()

    def get_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get sales trend for specified number of days."""
        # Request the last `days` days from the DB. The DB method may return either
        # a list of dicts (new format) or a list of tuples (legacy). Be tolerant.
        sales = self._db.fetch_sales_by_date_range(None, None, days) or []

        trend_dict: Dict[str, Dict[str, Any]] = {}
        for sale in sales:
            # support dict rows
            if isinstance(sale, dict):
                sale_date = sale.get('date')
                qty = int(sale.get('quantity', 0) or 0)
                amount = float(sale.get('amount', 0) or 0.0)
            else:
                # legacy tuple formats: try common shapes
                try:
                    # (date, quantity, amount)
                    sale_date = sale[0]
                    qty = int(sale[1])
                    amount = float(sale[2] or 0)
                except Exception:
                    # fallback: stringify entire row
                    sale_date = str(sale)
                    qty = 0
                    amount = 0.0

            key = str(sale_date)
            if key not in trend_dict:
                trend_dict[key] = {'date': key, 'quantity': 0, 'amount': 0.0}
            trend_dict[key]['quantity'] += qty
            trend_dict[key]['amount'] += amount

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
        products = self._db.fetch_top_products(limit) or []
        out: List[Dict[str, Any]] = []
        for p in products:
            if isinstance(p, dict):
                out.append({
                    'product_name': p.get('product_name', 'Unknown'),
                    'sale_count': int(p.get('sale_count', 0) or 0),
                    'total_revenue': float(p.get('total_revenue', 0) or 0.0),
                })
            else:
                # tuple-like
                try:
                    out.append({
                        'product_name': p[0],
                        'sale_count': int(p[1]),
                        'total_revenue': float(p[2] or 0),
                    })
                except Exception:
                    out.append({'product_name': str(p), 'sale_count': 0, 'total_revenue': 0.0})
        return out

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
