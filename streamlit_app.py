import streamlit as st
import pandas as pd

st.set_page_config(page_title="Air Fryer Scheduler", layout="wide")
st.title("Air Fryer Scheduler")

st.write("This app loads your item list from a CSV file on GitHub.")

GITHUB_CSV_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/data.csv"

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

        rows = []
        for i in range(len(selected_df)):
            item = selected_df.loc[i, "item"]
            minutes = selected_df.loc[i, "minutes"]

            if i == 0:
                wait = 0
            else:
                prev_minutes = selected_df.loc[i - 1, "minutes"]
                wait = prev_minutes - minutes

            rows.append({
                "order": i + 1,
                "item": item,
                "minutes": minutes,
                "wait_before_this_item": wait
            })

        result = pd.DataFrame(rows)

        st.subheader("Cooking order")
        for i, row in result.iterrows():
            if i == 0:
                st.markdown(
                    f"{row['order']}. Put in {row['item']} and cook for {fmt_minutes(row['minutes'])} minutes."
                )
            else:
                st.markdown(
                    f"{row['order']}. Wait {fmt_minutes(row['wait_before_this_item'])} minutes, then put in {row['item']} and cook for {fmt_minutes(row['minutes'])} minutes."
                )

        st.subheader("Timing table")
        st.dataframe(result, use_container_width=True)

        csv = result.to_csv(index=False).encode("utf-8")
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
