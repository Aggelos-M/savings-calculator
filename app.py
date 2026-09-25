import csv
import io
from typing import Dict, List

import streamlit as st


st.set_page_config(
    page_title="AI Voice Agent Savings Calculator",
    page_icon="💰",
    layout="wide",
)


# -----------------------------
# Βοηθητικές συναρτήσεις
# -----------------------------

def euro(value: float) -> str:
    """Εμφάνιση ποσού με μορφοποίηση ευρώ."""
    return f"€ {value:,.2f}"


def calculate_savings(
    calls_per_day: float,
    avg_duration: float,
    hourly_cost: float,
    agent_percentage: float,
    working_days: float,
    subscription_cost: float,
    cost_per_minute: float,
    human_review_minutes: float,
    setup_cost: float,
) -> Dict[str, float]:
    """Υπολογίζει το οικονομικό αποτέλεσμα για ένα ποσοστό ανάληψης.

    N = κλήσεις/ημέρα × εργάσιμες ημέρες/μήνα
    d = μέση διάρκεια κλήσης σε λεπτά
    p = ποσοστό ανάληψης agent ως δεκαδικός αριθμός
    r = ανθρώπινος έλεγχος ανά κλήση σε λεπτά
    w = ωριαίο κόστος ανθρώπινου δυναμικού
    F = μηνιαία συνδρομή agent
    u = κόστος agent ανά λεπτό
    S = εφάπαξ κόστος εγκατάστασης
    """
    calls_per_month = calls_per_day * working_days
    percentage = agent_percentage / 100.0

    total_human_hours = calls_per_month * avg_duration / 60.0
    saved_hours = (
        calls_per_month * percentage * (avg_duration - human_review_minutes) / 60.0
    )

    gross_monthly_savings = saved_hours * hourly_cost
    usage_cost = calls_per_month * percentage * avg_duration * cost_per_minute
    agent_monthly_cost = subscription_cost + usage_cost

    cost_before = total_human_hours * hourly_cost
    cost_after = cost_before - gross_monthly_savings + agent_monthly_cost
    net_monthly_savings = gross_monthly_savings - agent_monthly_cost
    net_first_year_savings = net_monthly_savings * 12.0 - setup_cost

    total_first_year_agent_cost = agent_monthly_cost * 12.0 + setup_cost
    first_year_roi = (
        net_first_year_savings / total_first_year_agent_cost * 100.0
        if total_first_year_agent_cost > 0
        else None
    )

    # Καθαρή συνεισφορά ανά κλήση που αναλαμβάνει ο agent.
    contribution_per_handled_call = (
        (avg_duration - human_review_minutes) * hourly_cost / 60.0
        - avg_duration * cost_per_minute
    )
    contribution_at_100_percent = calls_per_month * contribution_per_handled_call

    if subscription_cost == 0:
        break_even_percentage = 0.0
        break_even_message = "Επιτυγχάνεται από 0% ανάληψης."
    elif contribution_at_100_percent <= 0:
        break_even_percentage = None
        break_even_message = "Δεν επιτυγχάνεται στο εύρος 0–100%."
    else:
        break_even_percentage = subscription_cost / contribution_at_100_percent * 100.0
        break_even_message = (
            f"Απαιτείται τουλάχιστον {break_even_percentage:.2f}% ανάληψης."
            if break_even_percentage <= 100
            else "Δεν επιτυγχάνεται στο εύρος 0–100%."
        )

    return {
        "calls_per_month": calls_per_month,
        "total_human_hours": total_human_hours,
        "saved_hours": saved_hours,
        "gross_monthly_savings": gross_monthly_savings,
        "usage_cost": usage_cost,
        "agent_monthly_cost": agent_monthly_cost,
        "cost_before": cost_before,
        "cost_after": cost_after,
        "net_monthly_savings": net_monthly_savings,
        "net_first_year_savings": net_first_year_savings,
        "total_first_year_agent_cost": total_first_year_agent_cost,
        "first_year_roi": first_year_roi,
        "break_even_percentage": break_even_percentage,
        "break_even_message": break_even_message,
    }


def create_forecast(monthly_net_savings: float, setup_cost: float) -> List[Dict[str, float]]:
    """Πρόβλεψη 12 μηνών, με το setup cost να αφαιρείται στον 1ο μήνα."""
    forecast = []
    cumulative = 0.0

    for month in range(1, 13):
        setup_for_month = setup_cost if month == 1 else 0.0
        net_for_month = monthly_net_savings - setup_for_month
        cumulative += net_for_month
        forecast.append(
            {
                "Μήνας": month,
                "Καθαρό αποτέλεσμα μήνα (€)": round(net_for_month, 2),
                "Σωρευτικό καθαρό αποτέλεσμα (€)": round(cumulative, 2),
            }
        )

    return forecast


def create_csv(
    inputs: Dict[str, float],
    results: Dict[str, float],
    scenarios: List[Dict[str, float]],
    forecast: List[Dict[str, float]],
) -> bytes:
    """Δημιουργεί CSV UTF-8 με ελληνικούς χαρακτήρες, συμβατό με Excel."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow(["ΕΙΣΟΔΟΙ"])
    for key, value in inputs.items():
        writer.writerow([key, value])

    writer.writerow([])
    writer.writerow(["ΑΠΟΤΕΛΕΣΜΑΤΑ"])
    for key, value in results.items():
        writer.writerow([key, value])

    writer.writerow([])
    writer.writerow(["ΣΕΝΑΡΙΑ"])
    if scenarios:
        writer.writerow(list(scenarios[0].keys()))
        for row in scenarios:
            writer.writerow(list(row.values()))

    writer.writerow([])
    writer.writerow(["ΠΡΟΒΛΕΨΗ 12 ΜΗΝΩΝ"])
    if forecast:
        writer.writerow(list(forecast[0].keys()))
        for row in forecast:
            writer.writerow(list(row.values()))

    return ("\ufeff" + output.getvalue()).encode("utf-8")


# -----------------------------
# Εφαρμογή
# -----------------------------

st.title("💰 AI Voice Agent Savings Calculator")
st.write(
    "Συμπλήρωσε τα στοιχεία για να υπολογίσεις τη μεικτή και καθαρή "
    "εξοικονόμηση από τη χρήση AI Voice Agent."
)
st.caption("Οι υπολογισμοί είναι ενδεικτικοί και βασίζονται στις εισόδους σου.")

with st.form("savings_form"):
    st.header("1. Στοιχεία λειτουργίας")
    col1, col2 = st.columns(2)

    with col1:
        calls_per_day = st.number_input(
            "Κλήσεις ανά ημέρα", min_value=0.0, value=100.0, step=1.0
        )
        avg_duration = st.number_input(
            "Μέση διάρκεια κλήσης (λεπτά)", min_value=0.0, value=5.0, step=0.5
        )
        hourly_cost = st.number_input(
            "Ωριαίο κόστος ανθρώπινου ελέγχου (€)",
            min_value=0.0,
            value=15.0,
            step=0.5,
        )
        working_days = st.number_input(
            "Εργάσιμες ημέρες ανά μήνα", min_value=0.0, value=22.0, step=1.0
        )

    with col2:
        agent_percentage = st.slider(
            "Ποσοστό κλήσεων που αναλαμβάνει ο agent (%)",
            min_value=0,
            max_value=100,
            value=60,
        )
        human_review_minutes = st.number_input(
            "Χρόνος ανθρώπινου ελέγχου ανά κλήση (λεπτά)",
            min_value=0.0,
            max_value=float(avg_duration),
            value=0.0,
            step=0.5,
            help="Πρέπει να είναι από 0 έως τη μέση διάρκεια της κλήσης.",
        )
        subscription_cost = st.number_input(
            "Μηνιαία συνδρομή agent (€)", min_value=0.0, value=0.0, step=10.0
        )
        cost_per_minute = st.number_input(
            "Χρέωση χρήσης agent ανά λεπτό (€)",
            min_value=0.0,
            value=0.0,
            step=0.01,
        )
        setup_cost = st.number_input(
            "Εφάπαξ κόστος εγκατάστασης (€)",
            min_value=0.0,
            value=0.0,
            step=50.0,
        )

    st.header("2. Τρία σενάρια")
    scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
    with scenario_col1:
        conservative_percentage = st.slider(
            "Συντηρητικό σενάριο (%)", 0, 100, 30
        )
    with scenario_col2:
        base_percentage = st.slider("Βασικό σενάριο (%)", 0, 100, 60)
    with scenario_col3:
        optimistic_percentage = st.slider(
            "Αισιόδοξο σενάριο (%)", 0, 100, 90
        )

    submitted = st.form_submit_button("Υπολογισμός", type="primary")


if submitted:
    result = calculate_savings(
        calls_per_day,
        avg_duration,
        hourly_cost,
        agent_percentage,
        working_days,
        subscription_cost,
        cost_per_minute,
        human_review_minutes,
        setup_cost,
    )

    st.header("3. Αποτελέσματα")
    c1, c2, c3 = st.columns(3)
    c1.metric("Εξοικονομούμενες ώρες / μήνα", f"{result['saved_hours']:.2f}")
    c2.metric("Μεικτή εξοικονόμηση / μήνα", euro(result["gross_monthly_savings"]))
    c3.metric("Καθαρή εξοικονόμηση / μήνα", euro(result["net_monthly_savings"]))

    c4, c5, c6 = st.columns(3)
    c4.metric("Κόστος agent / μήνα", euro(result["agent_monthly_cost"]))
    c5.metric("Καθαρή εξοικονόμηση 1ου έτους", euro(result["net_first_year_savings"]))
    roi = result["first_year_roi"]
    c6.metric("ROI πρώτου έτους", "Δεν υπολογίζεται" if roi is None else f"{roi:.2f}%")

    if result["net_monthly_savings"] < 0:
        st.warning("Η καθαρή εξοικονόμηση είναι αρνητική — αποτελεί πρόσθετο κόστος.")
    elif result["net_monthly_savings"] == 0:
        st.info("Η καθαρή εξοικονόμηση είναι μηδενική.")
    else:
        st.success("Η καθαρή εξοικονόμηση είναι θετική.")

    st.subheader("4. Ανάλυση κόστους")
    st.dataframe(
        [
            {"Κατηγορία": "Κόστος πριν τον agent", "Ποσό (€)": round(result["cost_before"], 2)},
            {"Κατηγορία": "Κόστος μετά τον agent", "Ποσό (€)": round(result["cost_after"], 2)},
            {"Κατηγορία": "Μεικτή εξοικονόμηση", "Ποσό (€)": round(result["gross_monthly_savings"], 2)},
            {"Κατηγορία": "Μηνιαία συνδρομή", "Ποσό (€)": round(subscription_cost, 2)},
            {"Κατηγορία": "Κόστος χρήσης agent", "Ποσό (€)": round(result["usage_cost"], 2)},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("5. Όριο οικονομικής ισορροπίας")
    st.write(result["break_even_message"])
    if result["break_even_percentage"] is not None and result["break_even_percentage"] <= 100:
        st.progress(result["break_even_percentage"] / 100)
    elif result["break_even_percentage"] is not None:
        st.error("Το απαιτούμενο ποσοστό ξεπερνά το 100%.")
    else:
        st.error("Δεν υπάρχει εφικτό όριο ισορροπίας με τις συγκεκριμένες τιμές.")

    st.subheader("6. Σύγκριση τριών σεναρίων")
    scenario_rows = []
    for name, percentage in [
        ("Συντηρητικό", conservative_percentage),
        ("Βασικό", base_percentage),
        ("Αισιόδοξο", optimistic_percentage),
    ]:
        scenario_result = calculate_savings(
            calls_per_day,
            avg_duration,
            hourly_cost,
            percentage,
            working_days,
            subscription_cost,
            cost_per_minute,
            human_review_minutes,
            setup_cost,
        )
        scenario_rows.append(
            {
                "Σενάριο": name,
                "Ανάληψη (%)": percentage,
                "Ώρες εξοικονόμησης / μήνα": round(scenario_result["saved_hours"], 2),
                "Μεικτή εξοικονόμηση / μήνα (€)": round(scenario_result["gross_monthly_savings"], 2),
                "Καθαρή εξοικονόμηση / μήνα (€)": round(scenario_result["net_monthly_savings"], 2),
                "Καθαρό ποσό 1ου έτους (€)": round(scenario_result["net_first_year_savings"], 2),
            }
        )
    st.dataframe(scenario_rows, use_container_width=True, hide_index=True)

    st.subheader("7. Πρόβλεψη 12 μηνών")
    forecast = create_forecast(result["net_monthly_savings"], setup_cost)
    st.line_chart(
        forecast,
        x="Μήνας",
        y="Σωρευτικό καθαρό αποτέλεσμα (€)",
    )
    st.dataframe(forecast, use_container_width=True, hide_index=True)

    st.subheader("8. Εξαγωγή CSV")
    inputs = {
        "Κλήσεις ανά ημέρα": calls_per_day,
        "Μέση διάρκεια κλήσης": avg_duration,
        "Ωριαίο κόστος": hourly_cost,
        "Ποσοστό agent": agent_percentage,
        "Εργάσιμες ημέρες": working_days,
        "Μηνιαία συνδρομή": subscription_cost,
        "Κόστος agent ανά λεπτό": cost_per_minute,
        "Χρόνος ανθρώπινου ελέγχου": human_review_minutes,
        "Κόστος εγκατάστασης": setup_cost,
    }
    csv_data = create_csv(inputs, result, scenario_rows, forecast)
    st.download_button(
        "📥 Λήψη αποτελεσμάτων CSV",
        data=csv_data,
        file_name="savings_calculator_results.csv",
        mime="text/csv",
    )
