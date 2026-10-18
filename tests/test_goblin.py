import pathlib
import pytest
from goblin.ahledger import parse_pricetable, max_age
from goblin.calc import (net_profit, vendor_floor_profit, inflation_index,
                         real_discount, reliability, CUT_NEUTRAL)

FIX = pathlib.Path(__file__).parent / "fixtures" / "pricetable_sample.txt"


def test_parse_pricetable():
    t = parse_pricetable(FIX.read_text())
    assert t.market == "forever/pvp/horde/us" and len(t.rows) == 5
    assert t.rows[1].sales_per_day == 107.4
    assert t.rows[4].median_30d is None and t.rows[4].sales_per_day is None


def test_parse_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_pricetable("AHL1|m|1|2\n1:2:3")
    with pytest.raises(ValueError):
        parse_pricetable("AHL1|m|1|2\n1:2:3:4:5:6:7:8:9")


def test_max_age():
    assert max_age("public, max-age=60") == 60 and max_age(None, 30) == 30


def test_net_profit_matches_ahledger_netvalue():
    # AHledger: resultPrice 62300 -> netValue 59185 (5% cut)
    assert net_profit(62300, 0) == pytest.approx(59185)
    assert net_profit(62300, 13750) == pytest.approx(45435)


def test_neutral_cut_and_deposit():
    assert net_profit(10000, 5000, CUT_NEUTRAL, 100) == pytest.approx(3400)


def test_vendor_floor():
    assert vendor_floor_profit(80, 100, 20) == 400
    assert vendor_floor_profit(120, 100) < 0


def test_inflation_index_and_real_discount():
    idx = inflation_index({1: 200, 2: 400}, {1: 100, 2: 200})
    assert idx == pytest.approx(2.0)
    # median was 100 when index was 1.0; prices doubled, so real value is 200; listing at 150 = 25% under
    assert real_discount(150, 100, 1.0, 2.0) == pytest.approx(0.25)
    with pytest.raises(ValueError):
        inflation_index({1: 5}, {2: 5})


def test_reliability():
    assert reliability(80, 20, 500, True, 0.3) == "High"
    assert reliability(2, 0.5, 3, False, None) == "Low"
