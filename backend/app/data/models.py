from dataclasses import dataclass, field


@dataclass
class RawFinancials:
    market: str = ""
    ticker: str = ""
    currency: str = ""
    unit_scale: float = 1.0
    income: dict = field(default_factory=dict)
    balance: dict = field(default_factory=dict)
    price: float = None
    period_labels: list = None
    source: str = "manual"
    # 升级新增字段
    analyst_estimates: dict = field(default_factory=dict)
    sector: str = ""
    industry: str = ""
    market_data: dict = field(default_factory=dict)


@dataclass
class QualityReport:
    missing: dict = field(default_factory=dict)
    degraded_models: list = field(default_factory=list)
    derived_accounts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    health: str = "partial"


@dataclass
class StandardFinancials:
    market: str = ""
    ticker: str = ""
    currency: str = ""
    source: str = "manual"
    periods: list = field(default_factory=list)
    income: dict = field(default_factory=dict)
    balance: dict = field(default_factory=dict)
    price: float = None
    derived: list = field(default_factory=list)
    quality: QualityReport = None

    @property
    def net_debt(self) -> float:
        return self.balance.get("debt", 0.0) - self.balance.get("cash", 0.0)

    def latest(self, account: str):
        series = self.income.get(account)
        if not series:
            return None
        for value in reversed(series):
            if value is not None:
                return value
        return None

    def history(self, account: str) -> list:
        return [v for v in self.income.get(account, []) if v is not None]