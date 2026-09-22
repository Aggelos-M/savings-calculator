import streamlit as st           # Εισάγουμε τη βιβλιοθήκη Streamlit για να φτιάξουμε το web app

# Ρύθμιση της σελίδας
st.set_page_config(page_title="SAVINGS-CALCULATOR", layout="centered")

#  Τίτλος σελιδάς
st.title("SAVINGS-CALCULATOR")
st.write(
    "Συμπληρώστε τα παρακάτω στοιχεία για να δείτε πόσες ώρες και πόσα χρήματα "
    "μπορεί να εξοικονομήσει η εταιρεία σας χρησιμοποιώντας έναν AI Voice Agent."
)



# Χρησιμοποιούμε st.form ώστε ο υπολογισμός να τρέχει μόνο όταν ο χρήστης
# πατάει το κουμπί ΥΠΟΛΟΓΙΣΜΟΣ.

with st.form("savings_form"):
    # number_input με min_value=0,δεν πέρνει αρνητικές τιμές.
    calls_per_day = st.number_input(
        "Αριθμός κλήσεων ανά ημέρα", min_value=0, value=100, step=1
    )

    avg_duration = st.number_input(
        "Μέση διάρκεια κλήσης (λεπτά)", min_value=0.0, value=5.0, step=0.5
    )

    hourly_cost = st.number_input(
        "Ωριαίο κόστος υπαλλήλου (€)", min_value=0.0, value=15.0, step=0.5
    )

    # slider εγγυάται τιμή ανάμεσα σε 0 και 100 -> καλύπτει το κριτήριο αποδοχής
    agent_percentage = st.slider(
        "Ποσοστό κλήσεων που αναλαμβάνει ο agent (%)", min_value=0, max_value=100, value=60
    )

    working_days = st.number_input(
        "Εργάσιμες ημέρες ανά μήνα", min_value=1, value=22, step=1
    )

    #Το κουμπί υποβολής της φόρμας
    submitted = st.form_submit_button("Υπολογισμός")


# ΥΠΟΛΟΓΙΣΜΟΙ (εκτελούνται μόνο αφού πατηθεί το κουμπί ΥΠΟΛΟΓΙΣΜΟΣ).
if submitted:
    # Επιπλέον έλεγχος εγκυρότητας: αν όλες οι τιμές δεν βγάζουν νόημα,
    # ενημερώνουμε τον χρήστη αντί να δείξουμε λάθος/παράλογα αποτελέσματα.
    if calls_per_day <= 0 or avg_duration <= 0 or hourly_cost <= 0:
        st.error("Οι τιμές πρέπει να είναι θετικές .")
    else:
        # Ώρες εργασίας τον μήνα που απαιτούνται για ΟΛΕΣ τις κλήσεις:
        # κλήσεις/ημέρα × διάρκεια (λεπτά) × εργάσιμες ημέρες / 60 (μετατροπή λεπτών σε ώρες)
        hours_per_month = calls_per_day * avg_duration * working_days / 60

        # Ώρες που αναλαμβάνει ο agent, με βάση το ποσοστό που δώσαμε
        agent_hours = hours_per_month * agent_percentage / 100

        # Μηνιαία εξοικονόμηση σε ευρώ = ώρες που γλιτώνει ο agent × ωριαίο κόστος υπαλλήλου
        monthly_savings = agent_hours * hourly_cost

        # Ετήσια εξοικονόμηση = μηνιαία εξοικονόμηση × 12 μήνες
        annual_savings = monthly_savings * 12

        # Συνολικό μηνιαίο κόστος ΠΡΙΝ τον agent (αν όλες τις κλήσεις τις έκανε άνθρωπος)
        cost_before = hours_per_month * hourly_cost

        #Συνολικό μηνιαίο κόστος ΜΕΤΑ τον agent (μόνο οι ώρες που ΔΕΝ ανέλαβε ο agent)
        cost_after = cost_before - monthly_savings

        #Εμφάνιση αποτελεσμάτων
        st.subheader("Αποτελέσματα")

        #st.metric δείχνει μια τιμή σε "κάρτα"  εδώ μορφοποιούμε με 2 δεκαδικά
        col1, col2 = st.columns(2)
        col1.metric("Ώρες που εξοικονομούνται / μήνα", f"{agent_hours:.2f} ώρες")
        col2.metric("Μηνιαία εξοικονόμηση", f"€ {monthly_savings:,.2f}")

        st.metric("Ετήσια εξοικονόμηση", f"€ {annual_savings:,.2f}")

        # Γράφημα σύγκρισης μηνιαίου κόστους πριν/μετά 
        st.subheader("Σύγκριση Μηνιαίου Κόστους")

        # Το st.bar_chart θέλει λίστα τιμών ανά "στήλη" -> βάζουμε κάθε τιμή σε λίστα του ενός στοιχείου
        chart_data = {"Πριν τον Agent": [cost_before], "Μετά τον Agent": [cost_after]}
        st.bar_chart(chart_data)
        