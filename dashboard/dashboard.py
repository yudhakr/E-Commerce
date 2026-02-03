import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


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

STATE_NAME_MAP = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AM": "Amazonas",
    "AP": "Amapá",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",
    "PA": "Pará",
    "PB": "Paraíba",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "PR": "Paraná",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RO": "Rondônia",
    "RR": "Roraima",
    "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins"
}
# Ambil state yang benar-benar ada di data
available_states = sorted(df["customer_state"].dropna().unique())

# Buat label yang user-friendly
state_labels = {
    code: f"{STATE_NAME_MAP.get(code, code)} ({code})"
    for code in available_states
}

# Dropdown multiselect (user lihat nama lengkap)
selected_labels = st.sidebar.multiselect(
    "Filter State Pelanggan",
    options=list(state_labels.values())
)

# Konversi kembali ke kode state untuk filtering data
selected_states = [
    code for code, label in state_labels.items()
    if label in selected_labels
]

# Terapkan filter
if selected_states:
    df_filtered = df_filtered[df_filtered["customer_state"].isin(selected_states)]

# Filter kategori produk (opsional)
cat_options = sorted(df["product_category_name"].dropna().unique())
selected_cats = st.sidebar.multiselect(
    "Filter Kategori Produk ",
    options=cat_options,
    default=[]
)

if selected_cats:
    df_filtered = df_filtered[df_filtered["product_category_name"].isin(selected_cats)]



# ============================
# Filter tambahan (opsional)
# ============================
st.sidebar.subheader("Filter Tambahan (Opsional)")

# Filter kategori produk (mempengaruhi Q1 & Q2)
cat_options = sorted(df_filtered["product_category_name"].dropna().unique())
selected_cats = st.sidebar.multiselect(
    "Kategori Produk",
    options=cat_options,
    default=[]
)

top_n = st.sidebar.slider("Top/Bottom N", 3, 15, 5)

df_use = df_filtered.copy()
if selected_cats:
    df_use = df_use[df_use["product_category_name"].isin(selected_cats)]

# ======================================================
# PERTANYAAN 1
# Tren Pesanan & Revenue (Jan–Des 2017)
# ======================================================
st.subheader(
    "1️⃣ Bagaimana tren jumlah pesanan dan total revenue perusahaan "
    "pada periode Januari–Desember 2017?"
)

df_2017 = df_use[df_use["order_purchase_timestamp"].dt.year == 2017].copy()

if df_2017.empty:
    st.warning("Data tahun 2017 tidak tersedia untuk filter yang dipilih.")
else:
    trend_2017 = (
        df_2017.set_index("order_purchase_timestamp")
        .resample("M")
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("revenue", "sum")
        )
        .reset_index()
    )

    c1, c2 = st.columns(2)

    with c1:
        fig_orders = px.line(
            trend_2017,
            x="order_purchase_timestamp",
            y="total_orders",
            markers=True,
            title="Tren Jumlah Pesanan per Bulan"
        )
        fig_orders.update_layout(xaxis_title="Bulan", yaxis_title="Total Pesanan")
        st.plotly_chart(fig_orders, use_container_width=True)

    with c2:
        fig_rev = px.line(
            trend_2017,
            x="order_purchase_timestamp",
            y="total_revenue",
            markers=True,
            title="Tren Total Revenue per Bulan"
        )
        fig_rev.update_layout(xaxis_title="Bulan", yaxis_title="Total Revenue (R$)")
        st.plotly_chart(fig_rev, use_container_width=True)


# ======================================================
# PERTANYAAN 2
# Produk Paling Banyak & Sedikit Terjual (2017)
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

        with col1:
            st.markdown(f"**Top {top_n} Kategori Produk Terlaris**")
            fig_top = px.bar(
                topN.sort_values("total_item_sold"),
                x="total_item_sold",
                y="product_category_name",
                orientation="h",
                text="total_item_sold"
            )
            fig_top.update_layout(xaxis_title="Total Item Terjual", yaxis_title="Kategori")
            st.plotly_chart(fig_top, use_container_width=True)

        with col2:
            st.markdown(f"**Bottom {top_n} Kategori Produk Paling Sedikit Terjual**")
            fig_bottom = px.bar(
                bottomN.sort_values("total_item_sold"),
                x="total_item_sold",
                y="product_category_name",
                orientation="h",
                text="total_item_sold"
            )
            fig_bottom.update_layout(xaxis_title="Total Item Terjual", yaxis_title="Kategori")
            st.plotly_chart(fig_bottom, use_container_width=True)

  

# ======================================================
# PERTANYAAN 3
# Demografi Pelanggan 2018
# ======================================================
st.subheader(
    "3️⃣ Bagaimana demografi pelanggan pada tahun 2018?"
)

df_2018 = df_use[df_use["order_purchase_timestamp"].dt.year == 2018].copy()

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

    fig_q3 = px.bar(
        customer_state_2018,
        x="customer_state",
        y="unique_customers",
        title="Top 10 Distribusi Pelanggan Berdasarkan State"
    )
    fig_q3.update_layout(xaxis_title="State", yaxis_title="Jumlah Pelanggan (unik)")
    st.plotly_chart(fig_q3, use_container_width=True)

