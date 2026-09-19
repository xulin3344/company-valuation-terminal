from .base import FinancialProvider
from ..models import RawFinancials


class ManualProvider(FinancialProvider):
    name = "manual"

    def __init__(self, data: dict):
        self.data = data

    def fetch(self, ticker: str) -> RawFinancials:
        return RawFinancials(
            market=self.data.get("market", ""),
            ticker=ticker,
            currency=self.data.get("currency", ""),
            unit_scale=self.data.get("unit_scale", 1.0),
            income=dict(self.data.get("income", {})),
            balance=dict(self.data.get("balance", {})),
            price=self.data.get("price"),
            period_labels=self.data.get("period_labels"),
            source="manual",
        )