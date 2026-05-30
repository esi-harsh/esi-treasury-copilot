"""Seed the database with demo data for CIBC Treasury."""
from datetime import date, timedelta
from app.core.database import engine, SessionLocal, Base
from app.models import Currency, CurrencyPair, Counterparty, BankAccount, CreditLimit, MarketRate, Deal
from app.services.deal_service import create_deal_with_cashflows


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # --- Currencies ---
    ccys = [
        Currency(iso_code="USD", name="US Dollar", decimal_places=2, settlement_days=2),
        Currency(iso_code="CAD", name="Canadian Dollar", decimal_places=2, settlement_days=1),
        Currency(iso_code="EUR", name="Euro", decimal_places=2, settlement_days=2),
        Currency(iso_code="GBP", name="British Pound", decimal_places=2, settlement_days=2),
        Currency(iso_code="JPY", name="Japanese Yen", decimal_places=0, settlement_days=2),
        Currency(iso_code="CHF", name="Swiss Franc", decimal_places=2, settlement_days=2),
    ]
    if db.query(Currency).count() == 0:
        db.add_all(ccys)
        db.commit()

    usd = db.query(Currency).filter(Currency.iso_code == "USD").first()
    cad = db.query(Currency).filter(Currency.iso_code == "CAD").first()
    eur = db.query(Currency).filter(Currency.iso_code == "EUR").first()
    gbp = db.query(Currency).filter(Currency.iso_code == "GBP").first()
    jpy = db.query(Currency).filter(Currency.iso_code == "JPY").first()

    # --- Currency Pairs ---
    if db.query(CurrencyPair).count() == 0:
        pairs = [
            CurrencyPair(base_currency_id=usd.id, quote_currency_id=cad.id, pair_code="USD/CAD", spot_days=2, pip_size=0.0001),
            CurrencyPair(base_currency_id=eur.id, quote_currency_id=usd.id, pair_code="EUR/USD", spot_days=2, pip_size=0.0001),
            CurrencyPair(base_currency_id=gbp.id, quote_currency_id=usd.id, pair_code="GBP/USD", spot_days=2, pip_size=0.0001),
            CurrencyPair(base_currency_id=usd.id, quote_currency_id=jpy.id, pair_code="USD/JPY", spot_days=2, pip_size=0.01),
            CurrencyPair(base_currency_id=eur.id, quote_currency_id=cad.id, pair_code="EUR/CAD", spot_days=2, pip_size=0.0001),
        ]
        db.add_all(pairs)
        db.commit()

    # --- Counterparties ---
    if db.query(Counterparty).count() == 0:
        cps = [
            Counterparty(short_name="GS", legal_name="Goldman Sachs International", counterparty_type="bank", credit_rating="A+", rating_agency="S&P", country="US", swift_code="GOLDUS33"),
            Counterparty(short_name="JPM", legal_name="JP Morgan Chase", counterparty_type="bank", credit_rating="AA-", rating_agency="S&P", country="US", swift_code="CHASUS33"),
            Counterparty(short_name="DB", legal_name="Deutsche Bank AG", counterparty_type="bank", credit_rating="A-", rating_agency="Fitch", country="DE", swift_code="DEUTDEFF"),
            Counterparty(short_name="BARC", legal_name="Barclays Capital", counterparty_type="bank", credit_rating="A", rating_agency="Moody's", country="GB", swift_code="BARCGB2L"),
            Counterparty(short_name="RBC", legal_name="Royal Bank of Canada", counterparty_type="bank", credit_rating="AA-", rating_agency="S&P", country="CA", swift_code="ROYCCAT2"),
            Counterparty(short_name="BMO", legal_name="Bank of Montreal", counterparty_type="bank", credit_rating="A+", rating_agency="S&P", country="CA", swift_code="BOFMCAM2"),
            Counterparty(short_name="BOC", legal_name="Bank of Canada", counterparty_type="central_bank", credit_rating="AAA", country="CA"),
            Counterparty(short_name="ENB", legal_name="Enbridge Inc", counterparty_type="corporate", credit_rating="BBB+", rating_agency="S&P", country="CA"),
        ]
        db.add_all(cps)
        db.commit()

    # --- Bank Accounts ---
    if db.query(BankAccount).count() == 0:
        accounts = [
            BankAccount(account_number="CA001-USD-001", account_name="CIBC USD Nostro - NY", account_type="nostro", currency_id=usd.id, swift_code="CIBCUS33", current_balance=50_000_000),
            BankAccount(account_number="CA001-CAD-001", account_name="CIBC CAD Main", account_type="internal", currency_id=cad.id, swift_code="CIBCCATT", current_balance=75_000_000),
            BankAccount(account_number="CA001-EUR-001", account_name="CIBC EUR Nostro - Frankfurt", account_type="nostro", currency_id=eur.id, swift_code="CIBCDEF2", current_balance=20_000_000),
            BankAccount(account_number="CA001-GBP-001", account_name="CIBC GBP Nostro - London", account_type="nostro", currency_id=gbp.id, swift_code="CIBCGB2L", current_balance=15_000_000),
            BankAccount(account_number="CA001-JPY-001", account_name="CIBC JPY Nostro - Tokyo", account_type="nostro", currency_id=jpy.id, swift_code="CIBCJPJT", current_balance=2_000_000_000),
        ]
        db.add_all(accounts)
        db.commit()

    # --- Credit Limits ---
    if db.query(CreditLimit).count() == 0:
        cps = db.query(Counterparty).all()
        for cp in cps:
            db.add(CreditLimit(counterparty_id=cp.id, limit_type="total", limit_currency_id=usd.id, limit_amount=50_000_000, utilized_amount=0, available_amount=50_000_000, approved_by="Risk Committee", expiry_date=date.today() + timedelta(days=365)))
            db.add(CreditLimit(counterparty_id=cp.id, limit_type="settlement", limit_currency_id=usd.id, limit_amount=25_000_000, utilized_amount=0, available_amount=25_000_000, approved_by="Risk Committee", expiry_date=date.today() + timedelta(days=365)))
        db.commit()

    # --- Market Rates ---
    if db.query(MarketRate).count() == 0:
        today = date.today()
        usdcad = db.query(CurrencyPair).filter(CurrencyPair.pair_code == "USD/CAD").first()
        eurusd = db.query(CurrencyPair).filter(CurrencyPair.pair_code == "EUR/USD").first()
        gbpusd = db.query(CurrencyPair).filter(CurrencyPair.pair_code == "GBP/USD").first()
        usdjpy = db.query(CurrencyPair).filter(CurrencyPair.pair_code == "USD/JPY").first()
        rates = [
            MarketRate(rate_type="fx_spot", currency_pair_id=usdcad.id, tenor="SPOT", bid_rate=1.3718, ask_rate=1.3722, mid_rate=1.3720, rate_date=today, source="Reuters"),
            MarketRate(rate_type="fx_spot", currency_pair_id=eurusd.id, tenor="SPOT", bid_rate=1.0848, ask_rate=1.0852, mid_rate=1.0850, rate_date=today, source="Reuters"),
            MarketRate(rate_type="fx_spot", currency_pair_id=gbpusd.id, tenor="SPOT", bid_rate=1.2708, ask_rate=1.2712, mid_rate=1.2710, rate_date=today, source="Reuters"),
            MarketRate(rate_type="fx_spot", currency_pair_id=usdjpy.id, tenor="SPOT", bid_rate=156.78, ask_rate=156.82, mid_rate=156.80, rate_date=today, source="Reuters"),
            MarketRate(rate_type="fx_forward", currency_pair_id=usdcad.id, tenor="1M", mid_rate=1.3735, rate_date=today, source="Reuters"),
            MarketRate(rate_type="fx_forward", currency_pair_id=usdcad.id, tenor="3M", mid_rate=1.3780, rate_date=today, source="Reuters"),
            MarketRate(rate_type="interest_rate", currency_id=usd.id, tenor="ON", mid_rate=5.25, rate_date=today, source="Fed"),
            MarketRate(rate_type="interest_rate", currency_id=cad.id, tenor="ON", mid_rate=4.50, rate_date=today, source="BoC"),
            MarketRate(rate_type="interest_rate", currency_id=usd.id, tenor="3M", mid_rate=5.35, rate_date=today, source="Fed"),
        ]
        db.add_all(rates)
        db.commit()

    # --- Sample Deals ---
    if db.query(Deal).count() == 0:
        gs = db.query(Counterparty).filter(Counterparty.short_name == "GS").first()
        jpm = db.query(Counterparty).filter(Counterparty.short_name == "JPM").first()
        rbc = db.query(Counterparty).filter(Counterparty.short_name == "RBC").first()
        db_cp = db.query(Counterparty).filter(Counterparty.short_name == "DB").first()

        deals = [
            Deal(deal_type="fx_spot", counterparty_id=gs.id, trade_date=date.today(), value_date=date.today() + timedelta(days=2), buy_currency_id=usd.id, buy_amount=10_000_000, sell_currency_id=cad.id, sell_amount=13_720_000, rate=1.3720, direction="buy", trader="T.Shah"),
            Deal(deal_type="fx_forward", counterparty_id=jpm.id, trade_date=date.today(), value_date=date.today() + timedelta(days=30), buy_currency_id=eur.id, buy_amount=5_000_000, sell_currency_id=usd.id, sell_amount=5_425_000, rate=1.0850, direction="buy", trader="T.Shah"),
            Deal(deal_type="fx_spot", counterparty_id=db_cp.id, trade_date=date.today(), value_date=date.today() + timedelta(days=2), buy_currency_id=gbp.id, buy_amount=3_000_000, sell_currency_id=usd.id, sell_amount=3_813_000, rate=1.2710, direction="buy", trader="H.Patel"),
            Deal(deal_type="deposit", counterparty_id=rbc.id, trade_date=date.today(), value_date=date.today(), maturity_date=date.today() + timedelta(days=90), principal_currency_id=cad.id, principal_amount=25_000_000, interest_rate=0.045, day_count_convention="ACT/365", buy_currency_id=cad.id, buy_amount=25_000_000, sell_currency_id=cad.id, sell_amount=25_000_000, rate=4.50, direction="buy", trader="S.Kumar"),
        ]
        for d in deals:
            create_deal_with_cashflows(db, d)

    db.close()
    print("Done: Database seeded with 14 tables")


if __name__ == "__main__":
    seed()
