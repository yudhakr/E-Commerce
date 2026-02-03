import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# Optional Plotly (fallback)
# =========================
try:
    import plotly.express as px
    PLOTLY_OK = True
except ModuleNotFoundError:
    PLOTLY_OK = False

st.set_page_config(page_title="Dashboard Analisis E-Commerce", layout="wide")

# ======================
# Load Data
# ======================
# Coba beberapa kemungkinan path agar jalan di local & cloud
CANDIDATE_PATHS = [
    "main_data.csv",                 # kalau CSV di root repo
    "dashboard/main_data.csv",        # kalau CSV di folder dashboard
    "./main_data.csv",
    "./dashboard/main_data.csv"
]

dataset_path = next((p for p in CANDIDATE_PATHS if os.path.exists(p)), None)

if dataset_path is None:
    st.error("File main_data.csv tidak ditemukan. Pastikan file ada di repo (root atau folder dashboard).")
    st.stop()

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce")

    # Revenue dari dataset kamu: price + freight_value
    df["revenue"] = df["price"].fillna(0) + df["freight_value"].fillna(0)

    # buang baris timestamp invalid
    df = df.dropna(subset=["order_purchase_timestamp"])
    return df

df = load_data(dataset_path)

# ======================
# Header
# ======================
st.title("📊 Dashboard Analisis E-Commerce")
st.caption(
    "Dashboard ini menyajikan visualisasi untuk menjawab tiga pertanyaan bisnis utama "
    "berdasarkan data transaksi e-commerce."
)

if not PLOTLY_OK:
    st.warning("Plotly tidak terpasang di environment ini. Dashboard akan menggunakan Matplotlib (non-interaktif).")

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

if start_date > end_date:
    st.sidebar.error("Tanggal Mulai tidak boleh lebih besar dari Tanggal Akhir.")
    st.stop()

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

df_filtered = df[df["order_purchase_timestamp"].between(start_date, end_date)].copy()

# --- State filter (kode + nama)
STATE_NAME_MAP = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins"
}

available_states = sorted(df_filtered["customer_state"].dropna().unique())
state_labels = {code: f"{STATE_NAME_MAP.get(code, code)} ({code})" for code in available_states}

selected_labels = st.sidebar.multiselect(
    "Filter State Pelanggan (opsional)",
    options=list(state_labels.values()),
    default=[]
)

selected_states = [code for code, label in state_labels.items() if label in selected_labels]
if selected_states:
    df_filtered = df_filtered[df_filtered["customer_state"].isin(selected_states)]

# --- Kategori produk (satu saja, tidak dobel)
cat_options = sorted(df_filtered["product_category_name"].dropna().unique())
selected_cats = st.sidebar.multiselect(
    "Filter Kategori Produk (opsional)",
    options=cat_options,
    default=[]
)
if selected_cats:
    df_filtered = df_filtered[df_filtered["product_category_name"].isin(selected_cats)]

top_n = st.sidebar.slider("Top/Bottom N", 3, 15, 5)

# ======================
# KPI
# ======================
total_orders = df_filtered["order_id"].nunique()
total_revenue = df_filtered["revenue"].sum()
total_customers = df_filtered["customer_unique_id"].nunique()

k1, k2, k3 = st.columns(3)
k1.metric("Total Pesanan", f"{total_orders:,}")
k2.metric("Total Revenue (price+freight) (R$)", f"{total_revenue:,.2f}")
k3.metric("Pelanggan Unik", f"{total_customers:,}")

st.divider()

# ======================================================
# PERTANYAAN 1: Tren Pesanan & Revenue (Jan–Des 2017)
# ======================================================
st.subheader(
    "1️⃣ Bagaimana tren jumlah pesanan dan total revenue perusahaan "
    "pada periode Januari–Desember 2017?"
)

df_2017 = df_filtered[df_filtered["order_purchase_timestamp"].dt.year == 2017].copy()

if df_2017.empty:
    st.warning("Data tahun 2017 tidak tersedia untuk filter yang dipilih.")
else:
    trend_2017 = (
        df_2017.set_index("order_purchase_timestamp")
        .resample("M")
        .agg(total_orders=("order_id", "nunique"),
             total_revenue=("revenue", "sum"))
        .reset_index()
    )

    c1, c2 = st.columns(2)

    if PLOTLY_OK:
        with c1:
            fig_orders = px.line(
                trend_2017, x="order_purchase_timestamp", y="total_orders",
                markers=True, title="Tren Jumlah Pesanan per Bulan "
            )
            fig_orders.update_layout(xaxis_title="Bulan", yaxis_title="Total Pesanan")
            st.plotly_chart(fig_orders, use_container_width=True)

        with c2:
            fig_rev = px.line(
                trend_2017, x="order_purchase_timestamp", y="total_revenue",
                markers=True, title="Tren Total Revenue per Bulan "
            )
            fig_rev.update_layout(xaxis_title="Bulan", yaxis_title="Total Revenue (R$)")
            st.plotly_chart(fig_rev, use_container_width=True)
    else:
        with c1:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(trend_2017["order_purchase_timestamp"], trend_2017["total_orders"], marker="o")
            ax.set_title("Tren Jumlah Pesanan per Bulan ")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Total Pesanan")
            st.pyplot(fig)

        with c2:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(trend_2017["order_purchase_timestamp"], trend_2017["total_revenue"], marker="o")
            ax.set_title("Tren Total Revenue per Bulan")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Total Revenue (R$)")
            st.pyplot(fig)

st.divider()

# ======================================================
# PERTANYAAN 2: Top/Bottom Kategori Produk (2017)
# ======================================================
st.subheader(
    "2️⃣ Kategori produk apa yang paling banyak dan paling sedikit terjual "
    "sepanjang tahun 2017 berdasarkan total item yang terjual?"
)

if df_2017.empty:
    st.warning("Data tahun 2017 tidak tersedia untuk analisis kategori produk.")
else:
    product_sales_2017 = (
        df_2017.dropna(subset=["product_category_name"])
        .groupby("product_category_name")["order_item_id"]
        .count()
        .sort_values(ascending=False)
    )

    if product_sales_2017.empty:
        st.warning("Tidak ada kategori produk pada data yang difilter.")
    else:
        topN = product_sales_2017.head(top_n).reset_index()
        topN.columns = ["product_category_name", "total_item_sold"]

        bottomN = product_sales_2017.sort_values().head(top_n).reset_index()
        bottomN.columns = ["product_category_name", "total_item_sold"]

        col1, col2 = st.columns(2)

        if PLOTLY_OK:
            with col1:
                st.markdown(f"**Top {top_n} Kategori Produk Terlaris**")
                fig_top = px.bar(
                    topN.sort_values("total_item_sold"),
                    x="total_item_sold", y="product_category_name",
                    orientation="h", text="total_item_sold"
                )
                fig_top.update_layout(xaxis_title="Total Item Terjual", yaxis_title="Kategori")
                st.plotly_chart(fig_top, use_container_width=True)

            with col2:
                st.markdown(f"**Bottom {top_n} Kategori Produk Paling Sedikit Terjual**")
                fig_bottom = px.bar(
                    bottomN.sort_values("total_item_sold"),
                    x="total_item_sold", y="product_category_name",
                    orientation="h", text="total_item_sold"
                )
                fig_bottom.update_layout(xaxis_title="Total Item Terjual", yaxis_title="Kategori")
                st.plotly_chart(fig_bottom, use_container_width=True)
        else:
            with col1:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.barh(topN["product_category_name"], topN["total_item_sold"])
                ax.set_title(f"Top {top_n} Kategori Terlaris ")
                ax.set_xlabel("Total Item Terjual")
                st.pyplot(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.barh(bottomN["product_category_name"], bottomN["total_item_sold"])
                ax.set_title(f"Bottom {top_n} Kategori Terendah ")
                ax.set_xlabel("Total Item Terjual")
                st.pyplot(fig)

st.divider()

# ======================================================
# PERTANYAAN 3: Demografi Pelanggan (2018)
# ======================================================
st.subheader("3️⃣ Bagaimana demografi pelanggan pada tahun 2018?")

df_2018 = df_filtered[df_filtered["order_purchase_timestamp"].dt.year == 2018].copy()

if df_2018.empty:
    st.warning("Data tahun 2018 tidak tersedia untuk filter yang dipilih.")
else:
    customer_state_2018 = (
        df_2018.groupby("customer_state")["customer_unique_id"]
        .nunique()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    customer_state_2018.columns = ["customer_state", "unique_customers"]

    if PLOTLY_OK:
        fig_q3 = px.bar(
            customer_state_2018,
            x="customer_state", y="unique_customers",
            title="Top 10 Distribusi Pelanggan Berdasarkan State"
        )
        fig_q3.update_layout(xaxis_title="State", yaxis_title="Jumlah Pelanggan (unik)")
        st.plotly_chart(fig_q3, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(customer_state_2018["customer_state"], customer_state_2018["unique_customers"])
        ax.set_title("Top 10 Distribusi Pelanggan Berdasarkan State ")
        ax.set_xlabel("State")
        ax.set_ylabel("Jumlah Pelanggan (unik)")
        st.pyplot(fig)
