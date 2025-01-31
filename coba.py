import streamlit as st
import asyncio
import pandas as pd
from twikit import Client, TooManyRequests
from datetime import datetime, timedelta
import time
from random import randint
import os

async def get_tweets(account, client, start_date, end_date):
    query = f'from:{account} lang:id'
    if start_date and end_date:
        query += f' since:{start_date} until:{end_date}'
    
    print(f'{datetime.now()} - Mengambil tweet untuk akun: {account} dengan query: {query}')
    tweets = await client.search_tweet(query, product='Top')
    return tweets

async def main(account_names, start_date, end_date, cookies_file):
    all_tweet_data = {}

    for account in account_names:
        print(f'{datetime.now()} - Menggunakan cookies dari file: {cookies_file}')
        
        client = Client(language='en-US')
        client.load_cookies(cookies_file)

        tweet_data = []
        tweets = await get_tweets(account, client, start_date, end_date)

        while tweets:
            try:
                for tweet in tweets:
                    tweet_data.append({
                        "Username": tweet.user.name,
                        "Username Handle": tweet.user.screen_name,
                        "Profile Image": tweet.user.profile_image_url,
                        "Text": tweet.text,
                        "Created At": parse_tweet_date(tweet.created_at),
                        "Retweets": tweet.retweet_count,
                        "Likes": tweet.favorite_count,
                        "Tweet URL": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                    })

                wait_time = randint(2, 4)
                print(f"{datetime.now()} - Menunggu {wait_time} detik sebelum mengambil tweet berikutnya...")
                time.sleep(wait_time)
                
                tweets = await tweets.next()
            except TooManyRequests as e:
                rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
                print(f'{datetime.now()} - Batas permintaan tercapai. Menunggu hingga {rate_limit_reset}')
                wait_time = rate_limit_reset - datetime.now()
                time.sleep(wait_time.total_seconds())
                continue

        all_tweet_data[account] = pd.DataFrame(tweet_data) if tweet_data else pd.DataFrame()

    return all_tweet_data

def parse_tweet_date(date_str):
    try:
        return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
    except ValueError:
        return date_str

st.sidebar.title("Twitter Tweet Scraper")

account_input = st.sidebar.text_input("Masukkan nama akun (pisahkan dengan koma jika lebih dari satu):")
account_select = st.sidebar.multiselect("Atau pilih akun dari daftar:", [
    "bmkg_semarang", "psisfcofficial", "lokersemarid", "dishubkotasmg"
])

cookies_files = ['cookies_1.json', 'cookies_2.json', 'cookies_3.json']
user_labels = ['User 1', 'User 2', 'User 3']
cookies_file_selection = st.sidebar.selectbox("Pilih akun pengguna (Jika terkena limit, ganti pengguna ⚠️):", user_labels)

cookies_file = cookies_files[user_labels.index(cookies_file_selection)]

start_date = st.sidebar.date_input("Tanggal Mulai", datetime.today() - timedelta(weeks=1))
end_date = st.sidebar.date_input("Tanggal Selesai", datetime.today())
end_date_corrected = end_date + timedelta(days=1)

st.sidebar.caption("Contoh masukan manual: `account_1, account_2`")
st.sidebar.markdown("---")

scrape_button = st.sidebar.button("Scrape Tweet 📥")

st.title("Twitter Tweet Scraper 🐦")
st.write("Selamat datang di aplikasi **Twitter Tweet Scraper**!")

if scrape_button:
    if account_input or account_select:
        account_names = [name.strip() for name in account_input.split(",")] if account_input else account_select

        with st.spinner(f"Sedang mengambil tweet dari akun: {', '.join(account_names)}..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            all_tweet_data = loop.run_until_complete(main(account_names, start_date, end_date_corrected, cookies_file))

        for account, tweet_df in all_tweet_data.items():
            if not tweet_df.empty:
                tweet_df_sorted = tweet_df.sort_values(by="Created At", ascending=False)

                with st.expander(f"Tweet dari @{account} ", expanded=False):
                    st.write(f"**{len(tweet_df_sorted)} tweet ditemukan untuk akun @{account}:**")
                    for _, row in tweet_df_sorted.iterrows():
                        created_at_str = row['Created At'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['Created At'], datetime) else row['Created At']
                        
                        tweet_content = f"""
                        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 8px; background-color: #f9f9f9; margin-bottom: 20px;">
                            <div style="display: flex; align-items: center;">
                                <img src="{row['Profile Image']}" style="border-radius: 50%; width: 50px; height: 50px; margin-right: 10px;">
                                <div style="font-size: 18px; font-weight: bold; color: #1DA1F2;">{row['Username']} (@{row['Username Handle']}) <span style="color: gray;">({created_at_str})</span></div>
                            </div>
                            <div style="font-size: 16px; padding: 10px; color: #333;">{row['Text']}</div>
                            <div style="font-size: 14px; color: #666;">
                                <span>🔁 {row['Retweets']} Retweets | ❤️ {row['Likes']} Likes</span> | 
                                <a href="{row['Tweet URL']}" target="_blank" style="color: #1DA1F2;">Lihat Tweet</a>
                            </div>
                        </div>
                        """

                        st.markdown(tweet_content, unsafe_allow_html=True)
            else:
                st.info(f"Tidak ada tweet yang ditemukan untuk akun @{account}.")
    else:
        st.error("Mohon masukkan nama akun Twitter!")

st.markdown("---")
st.write("Developed by **Mesakh Besta Anugrah** ⚔️")
