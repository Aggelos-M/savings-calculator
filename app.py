import streamlit as st           # Εισάγουμε τη βιβλιοθήκη Streamlit για να φτιάξουμε το web app
import io                        # Για να χτίσουμε το CSV στη μνήμη πριν το download (Προσαρμογή 10)
import csv                       # Για σωστή μορφοποίηση CSV (χειρίζεται κόμματα, ειδικούς χαρακτήρες)
import pandas as pd              # Για το γράφημα 12 μηνών με άξονα Χ 1-12 (Προσαρμογή 9)

# Ρύθμιση της σελίδας
st.set_page_config(page_title="SAVINGS-CALCULATOR", layout="centered")

# Τίτλος σελίδας
st.title("SAVINGS-CALCULATOR")
st.write(
    "Συμπληρώστε τα παρακάτω στοιχεία για να δείτε πόσες ώρες και πόσα χρήματα "
    "μπορεί να εξοικονομήσει η εταιρεία σας χρησιμοποιώντας έναν AI Voice Agent!!!."
)



def compute_scenario(pct, calls_per_day, avg_duration, hourly_cost, working_days, F, u, r):
    # Ώρες εργασίας τον μήνα που θα χρειάζονταν ΟΛΕΣ οι κλήσεις αν τις έκανε άνθρωπος
    hours_per_month = calls_per_day * avg_duration * working_days / 60

    # Πόσες κλήσεις/μήνα αναλαμβάνει ο agent, με βάση το ποσοστό pct
    agent_calls_per_month = calls_per_day * (pct / 100) * working_days

    # Ώρες που αντιστοιχούν σε αυτές τις κλήσεις (σαν να τις έκανε άνθρωπος)
    agent_hours = hours_per_month * pct / 100

    # Προσαρμογή 3: χρόνος ανθρώπινου ελέγχου (r λεπτά ανά κλήση agent),
    # μετατρέπεται σε ώρες και αφαιρείται από τις εξοικονομούμενες ώρες
    oversight_hours = agent_calls_per_month * r / 60
    net_saved_hours = agent_hours - oversight_hours  # πάντα >= 0 αφού r <= avg_duration

    # Ακαθάριστη εξοικονόμηση σε ευρώ = καθαρές εξοικονομούμενες ώρες × ωριαίο κόστος
    gross_savings = net_saved_hours * hourly_cost

    # Προσαρμογή 2: κόστος χρήσης = χρέωση ανά λεπτό (u) × συνολικά λεπτά
    # κλήσεων που αναλαμβάνει ο agent (όλη η διάρκεια, όχι μειωμένη κατά r)
    usage_cost = u * agent_calls_per_month * avg_duration

    # Καθαρό μηνιαίο αποτέλεσμα = ακαθάριστη εξοικονόμηση μείον πάγιο (F) και κόστος χρήσης
    net_monthly = gross_savings - F - usage_cost

    # Καθαρό ετήσιο (ΧΩΡΙΣ το εφάπαξ κόστος εγκατάστασης S -> αυτό αφαιρείται
    # μόνο στο "πρώτου έτους" αποτέλεσμα, βλ. Προσαρμογή 4)
    net_annual = net_monthly * 12

    return {
        "hours_per_month": hours_per_month,
        "agent_calls_per_month": agent_calls_per_month,
        "agent_hours": agent_hours,
        "oversight_hours": oversight_hours,
        "net_saved_hours": net_saved_hours,
        "gross_savings": gross_savings,
        "usage_cost": usage_cost,
        "net_monthly": net_monthly,
        "net_annual": net_annual,
    }


def find_breakeven_percentage(calls_per_day, avg_duration, hourly_cost, working_days, F, u, r):
    """
    Προσαρμογή 6: βρίσκει το ΕΛΑΧΙΣΤΟ ποσοστό ανάληψης κλήσεων (0-100%) για το
    οποίο το καθαρό ΜΗΝΙΑΙΟ αποτέλεσμα γίνεται >= 0. Επιστρέφει None αν αυτό
    δεν είναι εφικτό μέσα στο εύρος 0-100%.

    Το net_monthly(pct) είναι ΓΡΑΜΜΙΚΗ συνάρτηση του pct (όλοι οι όροι είναι
    αναλογικοί του pct, εκτός από το σταθερό πάγιο F). Άρα αρκεί να υπολογίσουμε
    την τιμή σε δύο σημεία (0% και 100%) για να βρούμε την κλίση.
    """
    at_0 = compute_scenario(0, calls_per_day, avg_duration, hourly_cost, working_days, F, u, r)
    at_100 = compute_scenario(100, calls_per_day, avg_duration, hourly_cost, working_days, F, u, r)

    net_at_0 = at_0["net_monthly"]      
    net_at_100 = at_100["net_monthly"]
    slope = (net_at_100 - net_at_0) / 100  

    if slope > 0:
        pct = max(0.0, -net_at_0 / slope)  
        return pct if pct <= 100 else None
    else:
        
        return 0.0 if net_at_0 >= 0 else None


def build_csv_bytes(data):
    """Προσαρμογή 10: χτίζει το CSV σε μνήμη, με σωστή κωδικοποίηση για Ελληνικά."""
    buffer = io.StringIO()
    # delimiter=";" -> το ελληνικό Excel χρησιμοποιεί ερωτηματικό ως διαχωριστικό
    writer = csv.writer(buffer, delimiter=";")

    writer.writerow(["ΔΕΔΟΜΕΝΑ ΕΙΣΟΔΟΥ"])
    for label, value in data["inputs"]:
        writer.writerow([label, value])
    writer.writerow([])

    writer.writerow(["ΕΝΔΙΑΜΕΣΟΙ ΥΠΟΛΟΓΙΣΜΟΙ"])
    for label, value in data["calc_rows"]:
        writer.writerow([label, value])
    writer.writerow([])

    writer.writerow(["ΤΡΙΑ ΣΕΝΑΡΙΑ"])
    writer.writerow(["Σενάριο", "Ποσοστό (%)", "Καθαρό Μηνιαίο (€)", "Καθαρό Ετήσιο (€)"])
    for row in data["scenario_rows"]:
        writer.writerow(row)
    writer.writerow([])

    writer.writerow(["ΠΡΟΒΟΛΗ 12 ΜΗΝΩΝ"])
    writer.writerow(["Μήνας", "Σωρευτικό Καθαρό Αποτέλεσμα (€)"])
    for month, value in enumerate(data["projection"], start=1):
        writer.writerow([month, f"{value:.2f}"])

   
    return buffer.getvalue().encode("utf-8-sig")



with st.form("savings_form"):
    calls_per_day = st.number_input(
        "Αριθμός κλήσεων ανά ημέρα", min_value=0, value=100, step=1
    )

    avg_duration = st.number_input(
        "Μέση διάρκεια κλήσης (λεπτά)", min_value=0.0, value=5.0, step=0.5
    )

    hourly_cost = st.number_input(
        "Ωριαίο κόστος υπαλλήλου (€)", min_value=0.0, value=15.0, step=0.5
    )

    agent_percentage = st.slider(
        "Ποσοστό κλήσεων που αναλαμβάνει ο agent (%)", min_value=0, max_value=100, value=60
    )

    working_days = st.number_input(
        "Εργάσιμες ημέρες ανά μήνα", min_value=1, value=22, step=1
    )

    st.markdown("---")
    st.markdown("**Κόστη του AI Voice Agent**")

    F = st.number_input(
        "Μηνιαίο πάγιο κόστος agent (€)", min_value=0.0, value=0.0, step=10.0
    )

   
    u = st.number_input(
        "Χρέωση χρήσης agent ανά λεπτό κλήσης (€ / λεπτό)", min_value=0.0, value=0.0, step=0.01
    )

 
   
    r = st.number_input(
        "Χρόνος ανθρώπινου ελέγχου ανά κλήση agent (λεπτά)",
        min_value=0.0, value=0.0, step=0.5
    )

    # Προσαρμογή 4: εφάπαξ κόστος εγκατάστασης
    S = st.number_input(
        "Εφάπαξ κόστος εγκατάστασης (€)", min_value=0.0, value=0.0, step=50.0
    )

    st.markdown("---")
    st.markdown("**Τρία Σενάρια (Προσαρμογή 8)** — ξεχωριστό ποσοστό ανάληψης το καθένα")

    conservative_pct = st.slider("Συντηρητικό σενάριο — ποσοστό ανάληψης (%)", 0, 100, 40)
    basic_pct = st.slider("Βασικό σενάριο — ποσοστό ανάληψης (%)", 0, 100, 60)
    optimistic_pct = st.slider("Αισιόδοξο σενάριο — ποσοστό ανάληψης (%)", 0, 100, 80)

    # Το κουμπί υποβολής της φόρμας
    submitted = st.form_submit_button("Υπολογισμός")



if submitted:
    # Προσαρμογή 3: έλεγχος 0 <= r <= μέση διάρκεια κλήσης
    if r > avg_duration:
        st.error("Ο χρόνος ανθρώπινου ελέγχου δεν μπορεί να ξεπερνά τη μέση διάρκεια κλήσης.")
    else:
        main = compute_scenario(agent_percentage, calls_per_day, avg_duration, hourly_cost,
                                working_days, F, u, r)

        # Καθαρό αποτέλεσμα πρώτου έτους: εδώ, και ΜΟΝΟ εδώ, αφαιρείται το S (Προσαρμογή 4)
        net_first_year = main["net_annual"] - S

        # Προσαρμογή 7: ROI πρώτου έτους = καθαρό πρώτου έτους / συνολικό κόστος agent πρώτου έτους × 100
        total_agent_cost_first_year = F * 12 + main["usage_cost"] * 12 + S
        roi_first_year = (
            net_first_year / total_agent_cost_first_year * 100
            if total_agent_cost_first_year != 0 else None
        )

        # Προσαρμογή 6: όριο οικονομικής ισορροπίας
        breakeven_pct = find_breakeven_percentage(calls_per_day, avg_duration, hourly_cost,
                                                  working_days, F, u, r)

        # Συνολικό μηνιαίο κόστος ΠΡΙΝ/ΜΕΤΑ τον agent, για το γράφημα σύγκρισης
        cost_before = main["hours_per_month"] * hourly_cost
        cost_after = cost_before - main["gross_savings"] + F + main["usage_cost"]

        # Προσαρμογή 8: τα τρία σενάρια, το καθένα με το δικό του ποσοστό
        scenarios = {
            "Συντηρητικό": compute_scenario(conservative_pct, calls_per_day, avg_duration,
                                            hourly_cost, working_days, F, u, r),
            "Βασικό": compute_scenario(basic_pct, calls_per_day, avg_duration,
                                       hourly_cost, working_days, F, u, r),
            "Αισιόδοξο": compute_scenario(optimistic_pct, calls_per_day, avg_duration,
                                          hourly_cost, working_days, F, u, r),
        }
        scenario_pcts = {"Συντηρητικό": conservative_pct, "Βασικό": basic_pct,
                         "Αισιόδοξο": optimistic_pct}

        
        projection = []
        cumulative = 0.0
        for month in range(1, 13):
            monthly_amount = main["net_monthly"] - S if month == 1 else main["net_monthly"]
            cumulative += monthly_amount
            projection.append(cumulative)

        # Μαζεύουμε ό,τι χρειάζεται η εμφάνιση ΚΑΙ το CSV, σε ένα dict στο session_state
        st.session_state["results"] = {
            "main": main,
            "net_first_year": net_first_year,
            "total_agent_cost_first_year": total_agent_cost_first_year,
            "roi_first_year": roi_first_year,
            "breakeven_pct": breakeven_pct,
            "cost_before": cost_before,
            "cost_after": cost_after,
            "scenarios": scenarios,
            "scenario_pcts": scenario_pcts,
            "projection": projection,
            "F": F, "u": u, "r": r, "S": S,
            "inputs": [
                ("Κλήσεις ανά ημέρα", calls_per_day),
                ("Μέση διάρκεια κλήσης (λεπτά)", avg_duration),
                ("Ωριαίο κόστος υπαλλήλου (€)", hourly_cost),
                ("Ποσοστό ανάληψης agent (%)", agent_percentage),
                ("Εργάσιμες ημέρες/μήνα", working_days),
                ("Μηνιαίο πάγιο agent (€)", F),
                ("Χρέωση χρήσης agent (€/λεπτό)", u),
                ("Χρόνος ανθρώπινου ελέγχου (λεπτά/κλήση)", r),
                ("Εφάπαξ κόστος εγκατάστασης (€)", S),
            ],
        }


if "results" in st.session_state:
    res = st.session_state["results"]
    main = res["main"]

    st.subheader("Αποτελέσματα")
    col1, col2 = st.columns(2)
    col1.metric("Ώρες που εξοικονομούνται / μήνα", f"{main['net_saved_hours']:.2f} ώρες")
    col2.metric("Ακαθάριστη εξοικονόμηση / μήνα", f"€ {main['gross_savings']:,.2f}")
    st.metric("Ακαθάριστη εξοικονόμηση / έτος", f"€ {main['gross_savings'] * 12:,.2f}")

    # Προσαρμογή 5: χωριστά ακαθάριστη εξοικονόμηση, πάγιο, κόστος χρήσης,
    # καθαρό/μήνα και καθαρό πρώτου έτους. Αρνητικό καθαρό = πρόσθετο κόστος.
    st.subheader("Καθαρή Εξοικονόμηση")
    col3, col4, col5 = st.columns(3)
    col3.metric("Πάγιο (€/μήνα)", f"€ {res['F']:,.2f}")
    col4.metric("Κόστος χρήσης (€/μήνα)", f"€ {main['usage_cost']:,.2f}")
    col5.metric("Καθαρό / μήνα", f"€ {main['net_monthly']:,.2f}")
    st.metric("Καθαρό αποτέλεσμα πρώτου έτους", f"€ {res['net_first_year']:,.2f}")
    if main["net_monthly"] < 0:
        st.warning("Το καθαρό μηνιαίο αποτέλεσμα είναι αρνητικό — ο agent κοστίζει "
                   "περισσότερο από όσο εξοικονομεί με τις τρέχουσες τιμές.")

    # Προσαρμογή 6
    st.subheader("Όριο Οικονομικής Ισορροπίας")
    if res["breakeven_pct"] is None:
        st.metric("Ελάχιστο ποσοστό ανάληψης για καθαρό ≥ 0", "Δεν επιτυγχάνεται")
    else:
        st.metric("Ελάχιστο ποσοστό ανάληψης για καθαρό ≥ 0", f"{res['breakeven_pct']:.1f}%")

    # Προσαρμογή 7
    st.subheader("ROI Πρώτου Έτους")
    if res["roi_first_year"] is None:
        st.metric("Απόδοση επένδυσης (ROI)", "Δεν υπολογίζεται")
    else:
        st.metric("Απόδοση επένδυσης (ROI)", f"{res['roi_first_year']:.1f}%")

    # Γράφημα σύγκρισης μηνιαίου κόστους πριν/μετά
    st.subheader("Σύγκριση Μηνιαίου Κόστους")
    chart_data = {"Πριν τον Agent": [res["cost_before"]], "Μετά τον Agent": [res["cost_after"]]}
    st.bar_chart(chart_data)

    # Προσαρμογή 8
    st.subheader("Τρία Σενάρια")
    scen_cols = st.columns(3)
    for col, (name, data) in zip(scen_cols, res["scenarios"].items()):
        pct = res["scenario_pcts"][name]
        col.markdown(f"**{name}** ({pct}%)")
        col.metric("Καθαρό / μήνα", f"€ {data['net_monthly']:,.2f}")
        col.metric("Καθαρό / έτος", f"€ {data['net_annual']:,.2f}")

    # Προσαρμογή 9: ο άξονας Χ δείχνει τους μήνες 1-12 (index = range(1, 13))
    st.subheader("Προβολή 12 Μηνών")
    projection_df = pd.DataFrame(
        {"Σωρευτικό Καθαρό Αποτέλεσμα (€)": res["projection"]},
        index=range(1, 13),
    )
    projection_df.index.name = "Μήνας"
    st.line_chart(projection_df)

    # Προσαρμογή 10
    st.subheader("Εξαγωγή Αποτελεσμάτων")
    calc_rows = [
        ("Ώρες εργασίας / μήνα (χωρίς agent)", f"{main['hours_per_month']:.2f}"),
        ("Κλήσεις agent / μήνα", f"{main['agent_calls_per_month']:.2f}"),
        ("Ώρες ανθρώπινου ελέγχου / μήνα", f"{main['oversight_hours']:.2f}"),
        ("Καθαρές εξοικονομούμενες ώρες / μήνα", f"{main['net_saved_hours']:.2f}"),
        ("Ακαθάριστη εξοικονόμηση / μήνα (€)", f"{main['gross_savings']:.2f}"),
        ("Κόστος χρήσης / μήνα (€)", f"{main['usage_cost']:.2f}"),
        ("Καθαρό / μήνα (€)", f"{main['net_monthly']:.2f}"),
        ("Καθαρό πρώτου έτους (€)", f"{res['net_first_year']:.2f}"),
        ("Συνολικό κόστος agent πρώτου έτους (€)", f"{res['total_agent_cost_first_year']:.2f}"),
        ("Όριο οικονομικής ισορροπίας (%)",
         "Δεν επιτυγχάνεται" if res["breakeven_pct"] is None else f"{res['breakeven_pct']:.1f}"),
        ("ROI πρώτου έτους (%)",
         "Δεν υπολογίζεται" if res["roi_first_year"] is None else f"{res['roi_first_year']:.1f}"),
    ]
    scenario_rows = [
        (name, res["scenario_pcts"][name], f"{data['net_monthly']:.2f}", f"{data['net_annual']:.2f}")
        for name, data in res["scenarios"].items()
    ]
    csv_bytes = build_csv_bytes({
        "inputs": res["inputs"],
        "calc_rows": calc_rows,
        "scenario_rows": scenario_rows,
        "projection": res["projection"],
    })
    st.download_button(
        label="⬇️ Λήψη Αποτελεσμάτων (CSV)",
        data=csv_bytes,
        file_name="savings_calculator_results.csv",
        mime="text/csv",
    )

    # Σημείωση εκπαιδευτικού χαρακτήρα
    st.caption(
        "Σημείωση: Ο υπολογισμός είναι εκπαιδευτικός. Η ακαθάριστη εξοικονόμηση δεν "
        "περιλαμβάνει τα κόστη του agent (πάγιο, χρήση, εγκατάσταση) — το καθαρό "
        "αποτέλεσμα τα αφαιρεί."
    )
