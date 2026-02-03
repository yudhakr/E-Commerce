import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard Analisis E-Commerce", layout="wide")

# ======================
# Load Data
# ======================
dataset_path = "main_data.csv"

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["revenue"] = df["price"].fillna(0) + df["freight_value"].fillna(0)
    return df

df = load_data(dataset_path)

st.title("📊 Dashboard Analisis E-Commerce")
st.caption(
    "Dashboard ini menyajikan visualisasi untuk menjawab tiga pertanyaan bisnis utama "
    "berdasarkan data transaksi e-commerce."
)

# ======================
# Sidebar Filter
# ======================
st.sidebar.header("🔎 Filter")

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()

start_date = st.sidebar.date_input(
    "Tanggal Mulai",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "Tanggal Akhir",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Validasi range
if start_date > end_date:
    st.sidebar.error("Tanggal Mulai tidak boleh lebih besar dari Tanggal Akhir.")
    st.stop()

# Terapkan filter
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

df_filtered = df[df["order_purchase_timestamp"].between(start_date, end_date)].copy()

state_options = sorted(df["customer_state"].dropna().unique())
selected_states = st.sidebar.multiselect(
    "Filter State Pelanggan (opsional)",
    state_options
)

if selected_states:
    df_filtered = df_filtered[df_filtered["customer_state"].isin(selected_states)]

st.info(f"Menampilkan data dari {start_date.date()} sampai {end_date.date()}")


# ======================================================
# PERTANYAAN 1
# Tren Pesanan & Revenue (Jan–Des 2017)
# ======================================================
st.subheader(
    "1️⃣ Bagaimana tren jumlah pesanan dan total revenue perusahaan "
    "pada periode Januari–Desember 2017?"
)

df_2017 = df_filtered[
    df_filtered["order_purchase_timestamp"].dt.year == 2017
]

trend_2017 = (
    df_2017.set_index("order_purchase_timestamp")
    .resample("M")
    .agg(
        total_orders=("order_id", "nunique"),
        total_revenue=("revenue", "sum")
    )
)

fig, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(trend_2017.index, trend_2017["total_orders"], marker="o")
ax1.set_ylabel("Total Pesanan")

ax2 = ax1.twinx()
ax2.plot(trend_2017.index, trend_2017["total_revenue"], marker="s", linestyle="--")
ax2.set_ylabel("Total Revenue (R$)")

plt.title("Tren Bulanan Pesanan & Revenue ")
st.pyplot(fig)

st.divider()

# ======================================================
# PERTANYAAN 2
# Produk Paling Banyak & Sedikit Terjual (2017)
# ======================================================
st.subheader(
    "2️⃣ Kategori produk apa yang paling banyak dan paling sedikit terjual "
    "sepanjang tahun 2017?"
)

product_sales_2017 = (
    df_2017.dropna(subset=["product_category_name"])
    .groupby("product_category_name")["order_item_id"]
    .count()
    .sort_values(ascending=False)
)

top5 = product_sales_2017.head(5)
bottom5 = product_sales_2017.sort_values().head(5)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top 5 Kategori Produk Terlaris**")
    fig1, ax = plt.subplots(figsize=(6, 4))
    ax.barh(top5.index[::-1], top5.values[::-1])
    ax.set_xlabel("Jumlah Terjual")
    st.pyplot(fig1)

with col2:
    st.markdown("**5 Kategori Produk Paling Sedikit Terjual**")
    fig2, ax = plt.subplots(figsize=(6, 4))
    ax.barh(bottom5.index[::-1], bottom5.values[::-1])
    ax.set_xlabel("Jumlah Terjual")
    st.pyplot(fig2)

st.divider()

# ======================================================
# PERTANYAAN 3
# Demografi Pelanggan 2018
# ======================================================
st.subheader(
    "3️⃣ Bagaimana demografi pelanggan pada tahun 2018?"
)

df_2018 = df_filtered[
    df_filtered["order_purchase_timestamp"].dt.year == 2018
]

customer_state_2018 = (
    df_2018.groupby("customer_state")["customer_unique_id"]
    .nunique()
    .sort_values(ascending=False)
    .head(10)
)

fig3, ax = plt.subplots(figsize=(10, 4))
ax.bar(customer_state_2018.index, customer_state_2018.values)
ax.set_xlabel("State")
ax.set_ylabel("Jumlah Pelanggan (unik)")
ax.set_title("Top 10 Distribusi Pelanggan Berdasarkan State")
st.pyplot(fig3)
