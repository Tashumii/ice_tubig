from typing import Dict, List, Any
from database import DatabaseManager

class ReportService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_revenue_summary(self) -> Dict[str, float]:
        """Get revenue summary: total, this month, this year."""
        return self._db.fetch_revenue_summary()

    def get_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily sales trend aggregated by date.

        Args:
            days: Number of past days to include. Defaults to 30.

        Returns:
            List of dicts sorted ascending by date, each with keys:
            'date' (str), 'quantity' (int), 'amount' (float).

        Note:
            Tolerates both dict rows (current DB driver) and tuple rows
            (legacy driver pre-v2 migration). Malformed rows are silently
            skipped to avoid breaking the chart over a single bad record.
        """
        # fetch_sales_by_date_range returns tuples on legacy DB driver (pre-v2 migration)
        # TODO: Remove tuple support after migration complete - see JIRA-ICE-001
        sales = self._db.fetch_sales_by_date_range(None, None, days) or []

        trend_dict: Dict[str, Dict[str, Any]] = {}
        for sale in sales:
            if isinstance(sale, dict):
                sale_date = sale.get('date')
                qty = int(sale.get('quantity', 0) or 0)
                amount = float(sale.get('amount', 0) or 0.0)
            else:
                # Legacy DB driver returns raw tuples before v2 schema migration
                try:
                    sale_date = sale[0]
                    qty = int(sale[1])
                    amount = float(sale[2] or 0)
                except Exception:
                    # Silently skip malformed rows to avoid breaking entire trend chart
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
                    'product_name': p.get('product_name', 'No product name'),
                    'sale_count': int(p.get('sale_count', 0) or 0),
                    'total_revenue': float(p.get('total_revenue', 0) or 0.0),
                })
            else:
                # Legacy DB driver returns raw tuples before v2 schema migration
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
