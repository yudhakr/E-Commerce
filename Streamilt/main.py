import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Dashboard E-Commerce", layout="wide")

# ===============================
# TITLE
# ===============================
st.title("📊 Dashboard Analisis E-Commerce")
st.caption("Visualisasi untuk menjawab pertanyaan bisnis")

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("Upload Dataset")
    uploaded_file = st.file_uploader("Upload file CSV", type=["csv"])

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    # datetime aman
    if 'order_approved_at' in df.columns:
        df['order_approved_at'] = pd.to_datetime(df['order_approved_at'], errors='coerce')

    # bersihkan price jika ada
    if 'price' in df.columns:
        df['price'] = (
            df['price']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.replace(' ', '')
        )
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)

    return df

if uploaded_file is None:
    st.warning("Silakan upload dataset terlebih dahulu.")
    st.stop()

df = load_data(uploaded_file)

# ===============================
# FILTER TAHUN
# ===============================
if 'order_approved_at' in df.columns:
    df['year'] = df['order_approved_at'].dt.year

    with st.sidebar:
        st.header("Filter Tahun")
        year_range = st.slider(
            "Rentang Tahun",
            int(df['year'].min()),
            int(df['year'].max()),
            (
                int(df['year'].min()),
                int(df['year'].max())
            )
        )

    filtered_df = df[
        (df['year'] >= year_range[0]) &
        (df['year'] <= year_range[1])
    ]
else:
    filtered_df = df

# ===============================
# BUSINESS QUESTIONS
# ===============================
st.header("📌 Pertanyaan Bisnis")
st.markdown("""
1. Produk apa dengan jumlah pembelian terbesar?  
2. Berapa tingkat kepuasan pembeli terhadap layanan?  
3. Bagaimana data pembelian order setiap bulannya?
""")

# =====================================================
# 1. PRODUK TERBESAR
# =====================================================
st.subheader("🛒 Produk dengan Jumlah Pembelian Terbesar")

if 'product_category_name_english' in filtered_df.columns:
    product_sales = (
        filtered_df.groupby('product_category_name_english')['product_id']
        .count()
        .reset_index(name='total_sales')
        .sort_values('total_sales', ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12,5))
    sns.barplot(
        data=product_sales.head(5),
        x='total_sales',
        y='product_category_name_english',
        ax=ax
    )
    st.pyplot(fig)

    top_product = product_sales.iloc[0]['product_category_name_english']
    st.caption(f"Produk dengan pembelian tertinggi adalah **{top_product}**.")

# =====================================================
# 2. KEPUASAN PELANGGAN
# =====================================================
st.subheader("⭐ Tingkat Kepuasan Pelanggan")

if 'review_score' in filtered_df.columns:
    rating_counts = filtered_df['review_score'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8,4))
    sns.barplot(x=rating_counts.index, y=rating_counts.values, ax=ax)
    st.pyplot(fig)

    avg_rating = filtered_df['review_score'].mean()
    st.caption(f"Rata-rata rating pelanggan berada di angka **{avg_rating:.2f}**.")

# =====================================================
# 3. ORDER BULANAN
# =====================================================
st.subheader("📈 Data Pembelian Order Setiap Bulan")

if 'order_approved_at' in filtered_df.columns and 'order_id' in filtered_df.columns:

    # Buat kolom bulan angka
    filtered_df['month_num'] = filtered_df['order_approved_at'].dt.month

    # Agregasi benar-benar per bulan
    monthly_df = (
        filtered_df
        .groupby('month_num')['order_id']
        .count()
        .reset_index(name='order_count')
    )

    # Mapping nama bulan
    month_map = {
        1:'January', 2:'February', 3:'March', 4:'April',
        5:'May', 6:'June', 7:'July', 8:'August',
        9:'September', 10:'October', 11:'November', 12:'December'
    }

    monthly_df['month'] = monthly_df['month_num'].map(month_map)

    # Urutkan bulan
    monthly_df = monthly_df.sort_values('month_num')

    # ====== PLOT ======
    fig, ax = plt.subplots(figsize=(10,5))

    ax.plot(
        monthly_df["month"],
        monthly_df["order_count"],
        marker='o',
        linewidth=2,
        color="#72BCD4"
    )

    ax.set_title("Number of Orders per Month", fontsize=18)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Orders")

    plt.xticks(rotation=25)
    plt.grid(alpha=0.3)

    st.pyplot(fig)

    # ====== INSIGHT ======
    highest_month = monthly_df.loc[monthly_df['order_count'].idxmax(), 'month']
    lowest_month = monthly_df.loc[monthly_df['order_count'].idxmin(), 'month']

    st.caption(
        f"Order tertinggi terjadi pada **{highest_month}**, "
        f"sementara order terendah terjadi pada **{lowest_month}**."
    )



# ===============================
# FOOTER
# ===============================
st.caption("© Dashboard Analisis E-Commerce - Streamlit")
