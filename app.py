import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import numpy as np

# Set page config first (required by Streamlit)
st.set_page_config(page_title="Track my cash", page_icon="💰", layout="wide")

API_URL = "https://expense-backend-m2y7.onrender.com/expenses"

# Predefined options
CATEGORIES = ["Select a category", "Food", "Transport", "Entertainment", "Shopping", "Utilities", "Healthcare",
              "Education", "Others"]
PAYMENT_METHODS = ["Select a payment method", "Cash", "Credit Card", "Debit Card", "UPI", "Net Banking"]

# Responsive helper to stack or side-by-side
def responsive_columns(*args, mobile_threshold=600):
    width = st.experimental_get_query_params().get("width")
    # Simplified logic: if window width param < threshold, stack vertically
    if width and int(width[0]) < mobile_threshold:
        return [st.container() for _ in args]
    else:
        return st.columns(len(args))

tab1, tab2, tab3 = st.tabs([
    "📝 Add Expense",
    "📊 View Expenses",
    "📈 Analytics"
])

# --- TAB 1: Add or Edit Expense ---
with tab1:
    st.title("📝 Add or Edit Expense")
    selected_date = st.date_input("📅 Select Date to Add or Edit", max_value=date.today())

    # Fetch expenses for selected date
    response = requests.get(API_URL)
    edit_data = []
    if response.status_code == 200:
        all_expenses = response.json()
        edit_data = [exp for exp in all_expenses if exp["date"] == str(selected_date)]
    else:
        st.error("🚫 Failed to retrieve expenses for selected date.")

    if edit_data:
        st.subheader(f"📌 Existing Expenses on {selected_date.strftime('%d %B %Y')}")
        for i, exp in enumerate(edit_data, 1):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"**{i}. {exp['category']}** | ₹{exp['amount']} | {exp['payment_method']}  \n*{exp['description']}*")
            with col2:
                if st.button("✏️ Edit", key=f"edit_{exp['id']}"):
                    st.session_state.editing = True
                    st.session_state.edit_id = exp["id"]
                    st.session_state.category = exp["category"]
                    st.session_state.amount = exp["amount"]
                    st.session_state.payment_method = exp["payment_method"]
                    st.session_state.description = exp["description"]
                    st.experimental_rerun()
                if st.button("🗑️ Delete", key=f"del_{exp['id']}"):
                    del_resp = requests.delete(f"{API_URL}/{exp['id']}")
                    if del_resp.status_code == 200:
                        st.success("✅ Expense deleted!")
                        st.experimental_rerun()
                    else:
                        st.error("🚫 Failed to delete expense.")

    else:
        st.info("No expenses recorded for this date yet.")

    st.subheader("➕ Add or Edit Expense Entry")

    editing = st.session_state.get("editing", False)
    edit_id = st.session_state.get("edit_id", None)

    category = st.selectbox("Category", options=CATEGORIES,
                            index=CATEGORIES.index(st.session_state.get("category", "Select a category")),
                            key="category")
    default_amount = st.session_state.get("amount", 0.01)
    amount = st.number_input("Amount", min_value=0.01, format="%.2f", value=default_amount, key="amount")
    payment_method = st.selectbox("Payment Method", options=PAYMENT_METHODS,
                                  index=PAYMENT_METHODS.index(st.session_state.get("payment_method", "Select a payment method")),
                                  key="payment_method")
    description = st.text_area("Description", value=st.session_state.get("description", ""), key="description")

    if editing:
        if st.button("✅ Update Expense"):
            updated_data = {
                "date": str(selected_date),
                "category": category,
                "amount": amount,
                "payment_method": payment_method,
                "description": description
            }
            response = requests.put(f"{API_URL}/{edit_id}", json=updated_data)
            if response.status_code == 200:
                st.success("✅ Expense updated successfully!")
                # Clear edit session state
                for k in ["editing", "edit_id", "category", "amount", "payment_method", "description"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.experimental_rerun()
            else:
                st.error("🚫 Failed to update expense.")
    else:
        if st.button("➕ Add Expense"):
            if category == "Select a category" or payment_method == "Select a payment method":
                st.error("Please select valid category and payment method.")
            else:
                expense_data = {
                    "date": str(selected_date),
                    "category": category,
                    "amount": amount,
                    "payment_method": payment_method,
                    "description": description
                }
                response = requests.post(API_URL, json=expense_data)
                if response.status_code == 200:
                    st.success("✅ Expense added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("🚫 Failed to add expense.")

# --- TAB 2: View Expenses ---
with tab2:
    st.title("📊 View All Expenses")

    response = requests.get(API_URL)
    if response.status_code == 200:
        expenses = response.json()

        if expenses:
            df = pd.DataFrame(expenses)
            df['date'] = pd.to_datetime(df['date'])
            # Drop unneeded columns if present
            for col in ['Unnamed: 0', 'id']:
                if col in df.columns:
                    df.drop(columns=[col], inplace=True)

            st.subheader("📆 Filter by Date Range")
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

            if start_date > end_date:
                st.error("❌ Start date cannot be after end date.")
            else:
                filtered_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

                if not filtered_df.empty:
                    st.subheader(f"🗂️ Expenses from {start_date} to {end_date}")
                    # Show table in a scrollable container for mobile
                    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

                    @st.cache_data
                    def convert_df(df):
                        return df.to_csv(index=False).encode('utf-8')

                    csv = convert_df(filtered_df)
                    st.download_button(
                        label="💾 Download Filtered Data as CSV",
                        data=csv,
                        file_name=f'expenses_{start_date}_to_{end_date}.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning("No expenses found for the selected date range.")
        else:
            st.warning("No expenses found.")
    else:
        st.error("🚫 Failed to retrieve expenses.")

# --- TAB 3: Analytics ---
with tab3:
    st.title("📈 Expense Analytics")

    response = requests.get(API_URL)
    if response.status_code == 200:
        expenses = response.json()

        if expenses:
            df = pd.DataFrame(expenses)
            df['date'] = pd.to_datetime(df['date'])

            # Monthly Expense Bar Chart
            st.subheader("📅 Monthly Expense Analysis")
            df['month'] = df['date'].dt.to_period('M')
            monthly_expenses = df.groupby(df['month'])['amount'].sum().sort_index()
            monthly_expenses.index = monthly_expenses.index.strftime('%B %Y')

            fig, ax = plt.subplots(figsize=(10, 5))
            months = monthly_expenses.index.tolist()
            values = monthly_expenses.values
            colors = plt.cm.viridis(np.linspace(0, 1, len(months)))
            x_pos = np.arange(len(months))
            bars = ax.bar(x_pos, values, color=colors)

            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, yval + 10, f"₹{yval:.0f}", ha='center', va='bottom', fontsize=9)

            ax.set_title("Monthly Expenses", fontsize=14)
            ax.set_ylabel("Amount (₹)")
            ax.set_xlabel("Month")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(months, rotation=45, ha='right')
            st.pyplot(fig)

            # Pie Charts for Category & Payment Method for selected month
            st.subheader("🧭 Detailed Category & Payment Method Analysis")
            df['month_str'] = df['date'].dt.strftime('%B %Y')
            unique_months = sorted(df['month_str'].unique(), key=lambda x: pd.to_datetime(x))
            current_month = pd.Timestamp.now().strftime('%B %Y')
            default_index = unique_months.index(current_month) if current_month in unique_months else 0

            selected_month = st.selectbox("📆 Select Month for Pie Chart Analysis", unique_months, index=default_index)

            filtered_df = df[df['month_str'] == selected_month]

            if filtered_df.empty:
                st.warning(f"No data available for {selected_month}.")
            else:
                total_amount = filtered_df['amount'].sum()
                st.markdown(f"**Total Expense in {selected_month}: ₹{total_amount:.2f}**")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**By Category**")
                    cat_data = filtered_df.groupby('category')['amount'].sum()
                    fig1, ax1 = plt.subplots()
                    ax1.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%', startangle=140)
                    ax1.axis('equal')
                    st.pyplot(fig1)
                with col2:
                    st.markdown("**By Payment Method**")
                    pay_data = filtered_df.groupby('payment_method')['amount'].sum()
                    fig2, ax2 = plt.subplots()
                    ax2.pie(pay_data, labels=pay_data.index, autopct='%1.1f%%', startangle=140)
                    ax2.axis('equal')
                    st.pyplot(fig2)

        else:
            st.warning("No expense data found to analyze.")
    else:
        st.error("🚫 Failed to retrieve expenses.")

# --- Footer spacing ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
