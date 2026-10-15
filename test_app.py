# test_app.py
import pytest
from app import compute_scenario, find_breakeven_percentage

def test_basic_scenario():
    # Έλεγχος βασικού σεναρίου με τυπικές τιμές
    # calls_per_day=100, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=0, u=0, r=0
    res = compute_scenario(pct=60, calls_per_day=100, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=0.0, u=0.0, r=0.0)
    
    # Ώρες μήνα: 100 * 5 * 22 / 60 = 183.333...
    assert pytest.approx(res["hours_per_month"], 0.01) == 183.33
    # Ώρες agent (60%): 183.333 * 0.6 = 110.0
    assert pytest.approx(res["agent_hours"], 0.01) == 110.0
    # Ακαθάριστη εξοικονόμηση: 110 * 15 = 1650.0
    assert pytest.approx(res["gross_savings"], 0.01) == 1650.0

def test_zero_and_hundred_percentages():
    # 0% ποσοστό ανάληψης -> μηδενική εξοικονόμηση
    res_0 = compute_scenario(pct=0, calls_per_day=100, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=0.0, u=0.0, r=0.0)
    assert res_0["agent_calls_per_month"] == 0
    assert res_0["gross_savings"] == 0.0

    # 100% ποσοστό ανάληψης -> πλήρης εξοικονόμηση ανθρωπίνων ωρών
    res_100 = compute_scenario(pct=100, calls_per_day=100, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=0.0, u=0.0, r=0.0)
    assert pytest.approx(res_100["net_saved_hours"], 0.001) == res_100["hours_per_month"]

def test_zero_calls():
    # Μηδενικές κλήσεις ανά ημέρα
    res = compute_scenario(pct=60, calls_per_day=0, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=100.0, u=0.05, r=1.0)
    assert res["hours_per_month"] == 0.0
    assert res["net_saved_hours"] == 0.0
    assert res["gross_savings"] == 0.0
    assert res["net_monthly"] == -100.0  # Μόνο το πάγιο παραμένει ως κόστος

def test_breakeven_calculation():
    # Με μηνιαίο πάγιο F=500 και χωρίς άλλα κόστη
    breakeven = find_breakeven_percentage(calls_per_day=100, avg_duration=5.0, hourly_cost=15.0, working_days=22, F=500.0, u=0.0, r=0.0)
    assert breakeven is not None
    assert 0 <= breakeven <= 100

def test_oversight_constraint():
    # Έλεγχος ότι ο χρόνος ανθρώπινου ελέγχου αφαιρείται σωστά από τις καθαρές ώρες
    res = compute_scenario(pct=100, calls_per_day=10, avg_duration=5.0, hourly_cost=20.0, working_days=22, F=0.0, u=0.0, r=1.0)
    # Συνολικές κλήσεις μήνα = 10 * 22 = 220
    # oversight_hours = 220 * 1 / 60 = 3.666...
    assert res["oversight_hours"] > 0
    assert res["net_saved_hours"] < res["agent_hours"]