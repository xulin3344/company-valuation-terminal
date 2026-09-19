from collections import defaultdict

from ..engine.errors import InvalidAssumptionError
from .accounts import BALANCE_ACCOUNTS, INCOME_ACCOUNTS
from .models import RawFinancials, StandardFinancials

PER_SHARE_ACCOUNTS = {"eps_diluted"}

DERIVATION_RULES = (
    ("gross_profit", ("revenue", "cogs"), lambda r: r["revenue"] - r["cogs"]),
    ("ebit", ("gross_profit", "selling_expense", "admin_expense"),
     lambda r: r["gross_profit"] - r["selling_expense"] - r["admin_expense"] - (r.get("rd_expense") or 0.0)),
    ("ebitda", ("ebit", "da"), lambda r: r["ebit"] + r["da"]),
    ("da", ("ebitda", "ebit"), lambda r: r["ebitda"] - r["ebit"]),
    ("net_income", ("pretax_profit", "tax_expense"), lambda r: r["pretax_profit"] - r["tax_expense"]),
    ("pretax_profit", ("net_income", "tax_expense"), lambda r: r["net_income"] + r["tax_expense"]),
)


def normalize_name(name: str) -> str:
    if name is None:
        return ""
    text = str(name)
    translated = text.translate(str.maketrans(
        "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ（）",
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz()"))
    return "".join(translated.split()).lower()


def _series_has_value(series) -> bool:
    return any(v is not None for v in series)


def _merge_series(existing, incoming) -> list:
    if existing is None:
        return list(incoming)
    length = max(len(existing), len(incoming))
    out = []
    for i in range(length):
        a = existing[i] if i < len(existing) else None
        b = incoming[i] if i < len(incoming) else None
        if a is None:
            out.append(b)
        elif b is None:
            out.append(a)
        else:
            out.append(a + b)
    return out


class AccountMapper:
    def __init__(self, config: dict):
        if not config or "accounts" not in config:
            raise InvalidAssumptionError("mapper config must contain accounts section")
        self.market = config.get("market", "")
        self.debt_includes_lease = bool(config.get("debt_includes_lease", False))
        self.lease_names = {normalize_name(l) for l in config.get("lease_accounts", [])}
        self._index = {}
        for standard, synonyms in config["accounts"].items():
            for synonym in synonyms:
                self._index[normalize_name(synonym)] = standard

    def map_name(self, raw_name: str):
        return self._index.get(normalize_name(raw_name))

    def is_lease_account(self, raw_name: str) -> bool:
        return normalize_name(raw_name) in self.lease_names

    def standardize(self, raw: RawFinancials) -> StandardFinancials:
        scale = raw.unit_scale or 1.0
        income = {}
        balance = defaultdict(float)
        balance_seen = set()

        for raw_name, series in raw.income.items():
            standard = self.map_name(raw_name)
            if standard is None or standard not in INCOME_ACCOUNTS:
                continue
            if standard in PER_SHARE_ACCOUNTS:
                scaled = [None if v is None else float(v) for v in series]
            else:
                scaled = [None if v is None else float(v) * scale for v in series]
            income[standard] = _merge_series(income.get(standard), scaled)

        for raw_name, value in raw.balance.items():
            standard = self.map_name(raw_name)
            if standard is None or standard not in BALANCE_ACCOUNTS:
                continue
            balance[standard] += float(value) * scale
            balance_seen.add(standard)

        if self.debt_includes_lease:
            lease_total = 0.0
            lease_found = False
            for raw_name, value in raw.balance.items():
                if self.is_lease_account(raw_name):
                    lease_total += float(value) * scale
                    lease_found = True
            if lease_found:
                balance["debt"] += lease_total
                balance_seen.add("debt")

        derived = []
        self._derive_series(income, derived)
        self._derive_shares_from_eps(income, balance, derived)

        length = max((len(s) for s in income.values()), default=0)
        if raw.period_labels and len(raw.period_labels) == length:
            periods = list(raw.period_labels)
        else:
            periods = [f"FY-{length - i}" for i in range(length)]

        return StandardFinancials(
            market=raw.market or self.market,
            ticker=raw.ticker,
            currency=raw.currency,
            source=raw.source,
            periods=periods,
            income=income,
            balance=dict(balance),
            price=raw.price,
            derived=derived,
        )

    def _derive_series(self, income: dict, derived_log: list) -> None:
        for _ in range(3):
            added = []
            for target, deps, fn in DERIVATION_RULES:
                if target in income and _series_has_value(income[target]):
                    continue
                if not all(d in income and _series_has_value(income[d]) for d in deps):
                    continue
                length = min(len(income[d]) for d in deps)
                series = []
                for i in range(length):
                    row = {name: income[name][i] for name in income
                           if len(income[name]) > i and income[name][i] is not None}
                    if all(d in row for d in deps):
                        try:
                            series.append(float(fn(row)))
                        except (TypeError, KeyError):
                            series.append(None)
                    else:
                        series.append(None)
                if _series_has_value(series):
                    income[target] = series
                    added.append(target)
            if not added:
                break
            derived_log.extend(added)

    @staticmethod
    def _latest_value(income: dict, account: str):
        for value in reversed(income.get(account, [])):
            if value is not None:
                return value
        return None

    def _derive_shares_from_eps(self, income: dict, balance: dict, derived_log: list) -> None:
        if "shares_diluted" in balance and balance["shares_diluted"]:
            return
        eps = self._latest_value(income, "eps_diluted")
        net_income = self._latest_value(income, "net_income")
        if eps is None or eps <= 0 or net_income is None:
            return
        balance["shares_diluted"] = net_income / eps
        derived_log.append("shares_diluted")