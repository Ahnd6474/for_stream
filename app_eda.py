import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# 한글 폰트 문제 방지
plt.rcParams['font.family'] = 'sans-serif'

# 지역명 한글→영어 매핑
REGION_EN = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
    '제주': 'Jeju'
}

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")
        st.markdown("""
---
**Population Trends Dataset**
- Source: KOSTAT population trends
- Period: 2008–2017 by province/city
- Variables:
  - `Year`: survey year
  - `Region`: province or city
  - `Population`: total population
  - `Births`: number of births
  - `Deaths`: number of deaths
""")

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------



class EDA:
    def __init__(self):
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv")
            return

        df = pd.read_csv(uploaded)
        df[['연도','인구','출생아수(명)','사망자수(명)']] = \
            df[['연도','인구','출생아수(명)','사망자수(명)']].apply(pd.to_numeric, errors='coerce')
        df['region_en'] = df['지역'].map(REGION_EN).fillna(df['지역'])
        self.df = df.sort_values(['지역','연도'])

        tabs = st.tabs([
            "Basic Stats",
            "Yearly Trend",
            "Region Analysis",
            "Change Analysis",
            "Visualization"
        ])
        with tabs[0]:
            self.basic_stats()
        with tabs[1]:
            self.yearly_trend()
        with tabs[2]:
            self.region_analysis()
        with tabs[3]:
            self.change_analysis()
        with tabs[4]:
            self.visualization()

    def basic_stats(self):
        st.subheader("DataFrame Info")
        buf = io.StringIO()
        self.df.info(buf=buf)
        st.text(buf.getvalue())

        st.subheader("Summary Statistics")
        num = ['인구','출생아수(명)','사망자수(명)']
        st.dataframe(self.df[num].describe())

    def yearly_trend(self):
        st.subheader("Nationwide Population Trend & Projection")
        df_nat = self.df[self.df['지역']=='전국'].sort_values('연도')
        y, pop = df_nat['연도'], df_nat['인구']

        recent = df_nat.tail(3)
        avg_inc = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

        last_year, last_pop = int(y.max()), float(pop.iloc[-1])
        target_year = 2035
        pred = last_pop + avg_inc * (target_year - last_year)

        fig, ax = plt.subplots()
        ax.plot(y, pop, marker='o', label='Observed')
        ax.plot([last_year, target_year], [last_pop, pred],
                linestyle='--', marker='x', label='Projected')
        ax.set_title("Yearly Total Population")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")
        ax.legend()
        st.pyplot(fig)

    def region_analysis(self):
        st.subheader("Top-100 Yearly Δ Population Cases")
        df = self.df[self.df['지역']!='전국'].copy()
        df['diff'] = df.groupby('지역')['인구'].diff()
        df_top = df.dropna().nlargest(100, 'diff')[['연도','region_en','diff']]

        # Styling
        styled = (df_top.assign(diff=lambda d: d['diff'].map("{:,.0f}".format))
                   .style
                   .background_gradient(
                       subset=['diff'],
                       cmap=['red','white','blue'],
                       low=0, high=0
                   ))
        st.dataframe(styled, use_container_width=True)

    def change_analysis(self):
        st.subheader("5-Year Regional Change Charts")
        max_y = self.df['연도'].max()
        min_y = max_y - 5
        df5 = self.df[self.df['연도'].isin([min_y, max_y]) & (self.df['지역']!='전국')]
        pivot = df5.pivot(index='지역', columns='연도', values='인구')
        pivot['change_amt'] = pivot[max_y] - pivot[min_y]
        pivot['change_rate'] = pivot['change_amt'] / pivot[min_y] * 100
        pivot = pivot.reset_index().assign(region_en=lambda d: d['지역'].map(REGION_EN))

        # Absolute change
        df_amt = pivot.sort_values('change_amt', ascending=False)
        df_amt['change_amt_k'] = df_amt['change_amt'] / 1000
        fig1, ax1 = plt.subplots(figsize=(8,6))
        sns.barplot(x='change_amt_k', y='region_en', data=df_amt, ax=ax1)
        ax1.set_title("5-Year Population Δ (Absolute)")
        ax1.set_xlabel("Δ (thousands)")
        for p in ax1.patches:
            ax1.text(p.get_width()+0.1, p.get_y()+p.get_height()/2,
                     f"{p.get_width():.1f}", va='center')
        st.pyplot(fig1)

        # Rate change
        df_rate = pivot.sort_values('change_rate', ascending=False)
        fig2, ax2 = plt.subplots(figsize=(8,6))
        sns.barplot(x='change_rate', y='region_en', data=df_rate, ax=ax2)
        ax2.set_title("5-Year Population Δ (%)")
        ax2.set_xlabel("Δ (%)")
        for p in ax2.patches:
            ax2.text(p.get_width()+0.5, p.get_y()+p.get_height()/2,
                     f"{p.get_width():.1f}%", va='center')
        st.pyplot(fig2)

    def visualization(self):
        st.subheader("Stacked Area Chart by Region")
        df = self.df[self.df['지역']!='전국']
        pivot = df.pivot(index='연도', columns='region_en', values='인구').fillna(0)
        fig, ax = plt.subplots(figsize=(10,6))
        pivot.plot.area(ax=ax)
        ax.set_title("Population by Region Over Time")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")
        st.pyplot(fig)

# 실제 사용 예
home = Home()
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False

if st.session_state['data_loaded'] or st.button("Start EDA"):
    st.session_state['data_loaded'] = True
    eda = EDA()   

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
