import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO

def scrape_boat_data(row):
    result_main = {
        "id": row["id"],
        "url": row["url"],
        "boat_name": None,
        "image_1": None,
        "image_2": None,
    }
    table_data = [{} for _ in range(6)]  # List of dicts for each table
    try:
        res = requests.get(row["url"], timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Boat name
        name_div = soup.find("div", class_="boats-dimension")
        result_main["boat_name"] = name_div.get_text(strip=True) if name_div else None

        # Image 1
        dimen_div = soup.find("div", class_="dimen")
        img1 = dimen_div.find("img")["src"] if dimen_div and dimen_div.find("img") else None
        result_main["image_1"] = img1

        # Image 2
        boat_div = soup.find("div", class_="boat")
        img2 = boat_div.find("img")["src"] if boat_div and boat_div.find("img") else None
        result_main["image_2"] = img2

        # Extract tables
        table_divs = soup.find_all("div", class_="spec-bord")
        for idx, div in enumerate(table_divs[:6]):
            rows = div.find_all("tr")
            for row_ in rows:
                tds = row_.find_all("td")
                if len(tds) >= 2:
                    key = tds[0].get_text(strip=True)
                    value = tds[1].get_text(strip=True)
                    table_data[idx][key] = value

    except Exception as e:
        st.warning(f"Error scraping {row['url']}: {e}")

    return result_main, table_data

st.title("⛵ Sailboat Data Extractor")

uploaded_file = st.file_uploader("Upload CSV with 'id' and 'url' columns", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    main_data = []
    table_data_list = [ [] for _ in range(6) ]
    all_keys = [set() for _ in range(6)]

    with st.spinner("Scraping pages..."):
        for _, row in df.iterrows():
            base, tables = scrape_boat_data(row)
            main_data.append(base)

            for i, tdata in enumerate(tables):
                tdata_row = {"id": base["id"], "url": base["url"]}
                tdata_row.update(tdata)
                all_keys[i].update(tdata.keys())
                table_data_list[i].append(tdata_row)

    # Output BOAT_DATA
    df_main = pd.DataFrame(main_data)
    st.subheader("BOAT_DATA.csv")
    st.dataframe(df_main)
    st.download_button("Download BOAT_DATA.csv", df_main.to_csv(index=False), file_name="BOAT_DATA.csv")

    # Output BOAT_DATA_1 through BOAT_DATA_6
    for i in range(6):
        if table_data_list[i]:
            keys = ["id", "url"] + sorted(all_keys[i])
            df_table = pd.DataFrame(table_data_list[i])
            df_table = df_table.reindex(columns=keys)
            st.subheader(f"BOAT_DATA_{i+1}.csv")
            st.dataframe(df_table)
            st.download_button(f"Download BOAT_DATA_{i+1}.csv", df_table.to_csv(index=False), file_name=f"BOAT_DATA_{i+1}.csv")
