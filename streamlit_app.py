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
    if len(cols) < 2:
        return None

    out = df[[cols[0], cols[1]]].copy()
    out.columns = ["item", "minutes"]
    out["item"] = out["item"].astype(str).str.strip()
    out["minutes"] = pd.to_numeric(out["minutes"], errors="coerce")
    out = out.dropna(subset=["item", "minutes"])
    out = out[out["item"] != ""]
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
        st.error("The CSV needs at least two usable columns: item name and cooking time.")
        st.stop()

    st.subheader("Loaded data")
    st.dataframe(data, use_container_width=True)

    selected = st.multiselect(
        "Select two or more items",
        options=data["item"].tolist()
    )

    if len(selected) >= 2:
        selected_df = data[data["item"].isin(selected)].copy()
        selected_df = selected_df.sort_values(["minutes", "item"], ascending=[False, True]).reset_index(drop=True)

        st.subheader("Load order")
        for i in range(len(selected_df)):
            item = selected_df.loc[i, "item"]
            
            if i == 0:
                wait = 0
            else:
                prev_minutes = selected_df.loc[i - 1, "minutes"]
                wait = prev_minutes - selected_df.loc[i, "minutes"]
            
            st.markdown(f"**{item}:** {fmt_minutes(wait)} minutes")
        
        st.subheader("Timing table")
        result = selected_df.copy()
        result["wait_time"] = 0.0
        for i in range(1, len(result)):
            result.loc[i, "wait_time"] = result.loc[i-1, "minutes"] - result.loc[i, "minutes"]
        
        st.dataframe(result[["item", "minutes", "wait_time"]], use_container_width=True)
        
        # Verify all finish at max time
        max_time = result.loc[0, "minutes"]
        st.markdown(f"**All finish at {fmt_minutes(max_time)} minutes**")

        csv = result[["item", "minutes", "wait_time"]].to_csv(index=False).encode("utf-8")
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
