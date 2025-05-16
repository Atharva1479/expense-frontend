import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import numpy as np


# ✅ This MUST be the first Streamlit command
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

# ✅ App Title after set_page_config
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💰 Track My Cash</h1>", unsafe_allow_html=True)

# FastAPI base URL
API_URL = "https://expense-backend-m2y7.onrender.com/expenses"


# Predefined options
CATEGORIES = ["Select a category", "Food", "Transport", "Entertainment", "Shopping", "Utilities", "Healthcare",
              "Education", "Others"]
PAYMENT_METHODS = ["Select a payment method", "Cash", "Credit Card", "Debit Card", "UPI", "Net Banking"]

tab1, tab2, tab3 = st.tabs([
    "📝 Add Expense",
    "📊 View Expenses",
    "📈 Analytics"
])

active_tab = st.session_state.get("active_tab", "Add Expense")

with tab1:
    st.title("📝 Add or Edit Expense")

    selected_date = st.date_input("📅 Select Date to Add or Edit", max_value=date.today())

    response = requests.get(API_URL)
    edit_data = []
    if response.status_code == 200:
        all_expenses = response.json()
        edit_data = [exp for exp in all_expenses if exp["date"] == str(selected_date)]
    else:
        st.error("🚫 Failed to retrieve expenses for selected date.")

    # Show existing entries with Edit buttons
    if edit_data:
        st.subheader(f"📌 Existing Expenses on {selected_date.strftime('%d %B %Y')}")
        for i, exp in enumerate(edit_data, 1):
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
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
                st.rerun()
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{exp['id']}"):
                delete_response = requests.delete(f"{API_URL}/{exp['id']}")
                if delete_response.status_code == 200:
                    st.success("🗑️ Expense deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete expense.")

    else:
        st.info("No expenses recorded for this date yet.")

    st.subheader("➕ Add or Edit Expense Entry")

    # Detect whether editing or adding
    editing = st.session_state.get("editing", False)
    edit_id = st.session_state.get("edit_id", None)

    category = st.selectbox("Category", options=CATEGORIES, index=CATEGORIES.index(st.session_state.get("category", "Select a category")), key="category")
    default_amount = st.session_state.get("amount", 0.01)
    amount = st.number_input("Amount", min_value=0.01, format="%.2f", value=default_amount, key="amount")
    payment_method = st.selectbox("Payment Method", options=PAYMENT_METHODS, index=PAYMENT_METHODS.index(st.session_state.get("payment_method", "Select a payment method")), key="payment_method")
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
                # Reset session state
                for k in ["editing", "edit_id", "category", "amount", "payment_method", "description"]:
                    st.session_state.pop(k, None)
                st.rerun()
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
                    st.rerun()
                else:
                    st.error("🚫 Failed to add expense.")

# ✅ Tab 2: View Expenses (NO ANALYTICS HERE)
with tab2:
    st.title("📊 View All Expenses")

    response = requests.get(API_URL)
    if response.status_code == 200:
        expenses = response.json()

        if expenses:
            df = pd.DataFrame(expenses)
            df['date'] = pd.to_datetime(df['date'])

            # Drop unnecessary columns
            df.drop(columns=[col for col in ['Unnamed: 0', 'id'] if col in df.columns], inplace=True)

            # 📅 Add Date Filters
            st.subheader("📆 Filter by Date Range")
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()

            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

            if start_date > end_date:
                st.error("❌ Start date cannot be after end date.")
            else:
                # Filter DataFrame
                filtered_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

                if not filtered_df.empty:
                    st.subheader(f"🗂️ Expenses from {start_date} to {end_date}")
                    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

                    # Download button
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

# ✅ Tab 3: Analytics (ALL ANALYTICS HERE)
with tab3:
    st.title("📈 Expense Analytics")

    response = requests.get(API_URL)
    if response.status_code == 200:
        expenses = response.json()

        if expenses:
            df = pd.DataFrame(expenses)
            df['date'] = pd.to_datetime(df['date'])

            # ✅ Monthly Expense Bar Chart
            st.subheader("📅 Monthly Expense Analysis")
            df['month'] = df['date'].dt.to_period('M')
            monthly_expenses = df.groupby(df['month'])['amount'].sum().sort_index()
            monthly_expenses.index = monthly_expenses.index.strftime('%B %Y')

            # Plot bar chart
            fig, ax = plt.subplots(figsize=(10, 5))
            months = monthly_expenses.index.tolist()
            values = monthly_expenses.values
            colors = plt.cm.viridis(np.linspace(0, 1, len(months)))
            x_pos = np.arange(len(months))
            bars = ax.bar(x_pos, values, color=colors)

            for bar in bars:
                yval = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    yval + (0.01 * max(values)),  # dynamic spacing based on chart height
                    f"₹{yval:.0f}",
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold'
            )


            ax.set_title("Monthly Expenses", fontsize=14)
            ax.set_ylabel("Amount (₹)")
            ax.set_xlabel("Month")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(months, rotation=45, ha='right')
            st.pyplot(fig)

            # ✅ Pie Chart Filtering by Month
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
                st.markdown(f"**💰 Total Expenses for {selected_month}: ₹{total_amount:.2f}**")

                col1, col2 = st.columns(2)

                # 🏷️ Category-wise Pie
                with col1:
                    st.markdown("#### 🏷️ Category-wise")
                    category_expenses = filtered_df.groupby('category')['amount'].sum().sort_values(ascending=False)
                    explode_cat = [0.1 if i < 2 else 0 for i in range(len(category_expenses))]
                    fig1, ax1 = plt.subplots()
                    ax1.pie(
                        category_expenses,
                        labels=category_expenses.index,
                        autopct='%1.1f%%',
                        startangle=90,
                        explode=explode_cat
                    )
                    ax1.axis('equal')
                    st.pyplot(fig1)

                # 💳 Payment Method-wise Pie
                with col2:
                    st.markdown("#### 💳 Payment Method-wise")
                    payment_expenses = filtered_df.groupby('payment_method')['amount'].sum().sort_values(
                        ascending=False)
                    explode_pay = [0.1 if i < 2 else 0 for i in range(len(payment_expenses))]
                    fig2, ax2 = plt.subplots()
                    ax2.pie(
                        payment_expenses,
                        labels=payment_expenses.index,
                        autopct='%1.1f%%',
                        startangle=90,
                        explode=explode_pay
                    )
                    ax2.axis('equal')
                    st.pyplot(fig2)

        else:
            st.warning("No data available for analytics.")
    else:
        st.error("🚫 Failed to retrieve data for analytics.")

st.markdown("""
    <div style="text-align: center; color: grey; font-size: 0.9em;">
        Made with ❤️ by <strong>AJ</strong>
    </div>
""", unsafe_allow_html=True)

