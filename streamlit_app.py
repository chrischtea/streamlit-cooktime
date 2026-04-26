import streamlit as st
import pandas as pd

st.set_page_config(page_title="Air Fryer Scheduler", layout="wide")
st.title("Air Fryer Scheduler")

st.write("This app loads your item list from a CSV file on GitHub.")

GITHUB_CSV_URL = "https://raw.githubusercontent.com/chrischtea/streamlit-cooktime/refs/heads/main/data.csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

def normalize_columns(df):
    cols = list(df.columns)
    if len(cols) < 3:
        return None

    out = df[[cols[0], cols[1], cols[2]]].copy()
    out.columns = ["Produkt", "minutes", "Status"]

    out["Produkt"] = out["Produkt"].astype(str).str.strip()
    out["minutes"] = pd.to_numeric(out["minutes"], errors="coerce")
    out["status"] = out["status"].astype(str).str.strip().str.lower()

    out = out.dropna(subset=["Produkt", "minutes", "status"])
    out = out[out["Produkt"] != ""]
    out = out[out["status"] == "x"]
    out["minutes"] = out["minutes"].astype(float)
    return out

def fmt_minutes(x):
    if float(x).is_integer():
        return str(int(x))
    return f"{x:g}"

try:
    df = load_data(GITHUB_CSV_URL)
    data = normalize_columns(df)

    if data is None or data.empty:
        st.error("The CSV needs at least three usable columns: item name, cooking time, and status.")
        st.stop()

    selected = st.pills(
        "Select two or more items",
        sorted(data["Produkt"].tolist()),
        selection_mode="multi"
    )

    if len(selected) >= 2:
        selected_df = data[data["Produkt"].isin(selected)].copy()
        selected_df = selected_df.sort_values(["minutes", "Produkt"], ascending=[False, True]).reset_index(drop=True)

        st.subheader("Load order")

        times_to_next = []
        for i in range(len(selected_df) - 1):
            time_to_next = selected_df.loc[i, "minutes"] - selected_df.loc[i + 1, "minutes"]
            times_to_next.append(time_to_next)
        times_to_next.append(selected_df.loc[len(selected_df) - 1, "minutes"])

        for i, item in enumerate(selected_df["Produkt"]):
            st.markdown(f"**{item}:** {fmt_minutes(times_to_next[i])} minutes")

        st.subheader("Timing table")
        result = selected_df.copy()
        result["time_to_next"] = times_to_next
        st.dataframe(result[["Produkt", "minutes", "time_to_next"]], use_container_width=True)

        max_time = selected_df.loc[0, "minutes"]
        st.markdown(f"**All finish at {fmt_minutes(max_time)} minutes**")

        csv = result[["Produkt", "minutes", "time_to_next"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download schedule as CSV",
            data=csv,
            file_name="air_fryer_schedule.csv",
            mime="text/csv"
        )

    elif len(selected) == 1:
        st.info("Select at least two items.")
    else:
        st.info("Choose items to generate the schedule.")

except Exception as e:
    st.error(f"Could not load the CSV from GitHub: {e}")
