import os
import streamlit as st
import requests
from transformers import pipeline
from dotenv import load_dotenv
from textblob import TextBlob
from datetime import datetime
import streamlit.components.v1 as components


# ===============================
# CONFIG
# ===============================

st.set_page_config(
    page_title="VoxVarta AI",
    page_icon="📰",
    layout="wide"
)


# ===============================
# API
# ===============================

load_dotenv()

API_KEY = os.getenv("GNEWS_API_KEY")

if not API_KEY:
    st.error("Missing GNEWS_API_KEY")
    st.stop()


# ===============================
# MODELS
# ===============================

@st.cache_resource
def load_summarizer():
    return pipeline(
        "summarization",
        model="facebook/bart-large-cnn"
    )


@st.cache_resource
def load_qa():

    return pipeline(
        "question-answering",
        model="deepset/deberta-v3-base-squad2"
    )


summarizer = load_summarizer()
qa_model = load_qa()



# ===============================
# STATE
# ===============================

if "articles" not in st.session_state:
    st.session_state.articles = []

if "interests" not in st.session_state:
    st.session_state.interests = []

if "feed_loaded" not in st.session_state:
    st.session_state.feed_loaded = False



categories = [
    "General",
    "Business",
    "Technology",
    "Entertainment",
    "Sports",
    "Health",
    "Science",
    "Academics"
]


styles = [
    "Quick Summary",
    "Detailed",
    "Explain Like I'm 10",
    "Bullet Points"
]



# ===============================
# CSS
# ===============================

st.markdown("""
<style>

.stApp{
background:linear-gradient(120deg,#fff7ed,#eff6ff,#fdf2f8);
}


.hero{
background:linear-gradient(135deg,#ff9a9e,#fad0c4,#a1c4fd);
padding:40px;
border-radius:30px;
text-align:center;
box-shadow:0 10px 30px rgba(0,0,0,.12);
margin-bottom:45px;
}


.hero h1{
font-size:54px;
font-weight:900;
}


.hero p{
font-size:22px;
font-weight:500;
}


.news-card{
background:white;
padding:25px;
border-radius:25px;
margin:20px 0;
box-shadow:0 10px 25px rgba(0,0,0,.08);
}


.news-title{
font-size:26px;
font-weight:800;
}


.source{
background:linear-gradient(90deg,#fde68a,#fbcfe8);
padding:7px 14px;
border-radius:25px;
font-weight:bold;
}


.summary{
background:#f8fafc;
padding:16px;
border-radius:18px;
margin-top:15px;
}



div.stButton>button{

background:linear-gradient(90deg,#f97316,#ec4899)!important;
color:white!important;
border-radius:25px!important;
font-weight:bold!important;
transition:.2s!important;

}


div.stButton>button:hover{
transform:scale(1.08);
}



section[data-testid="stSidebar"]{
background:linear-gradient(180deg,#fff1f2,#eff6ff);
}


</style>
""",
unsafe_allow_html=True)



# ===============================
# HEADER
# ===============================

st.markdown("""
<div class="hero">

<h1>📰 VoxVarta AI</h1>

<p>
Know more. Scroll less. Save time. Stay ahead.
</p>

</div>
""",
unsafe_allow_html=True)




# ===============================
# SIDEBAR
# ===============================

st.sidebar.title("📰 VoxVarta AI")


st.sidebar.info("""
Your personal AI news assistant.

Powered by:
GNews API + HuggingFace
""")


st.sidebar.subheader("👤 Your Interests")


selected = st.sidebar.multiselect(
    "Choose topics",
    categories,
    default=st.session_state.interests
)


if st.sidebar.button("Save Preferences"):

    st.session_state.interests = selected

    st.session_state.feed_loaded = True

    st.rerun()



sidebar_category = st.sidebar.selectbox(
    "News Category",
    categories
)


sidebar_style = st.sidebar.selectbox(
    "Summary Style",
    styles
)


# ===============================
# SIDEBAR GET NEWS BUTTON
# ===============================

if st.sidebar.button("📰 Get News"):

    st.session_state.articles = get_news(
        "",
        sidebar_category
    )

    st.session_state.feed_loaded = True

    st.rerun()




# ===============================
# MAIN INPUT
# ===============================

if st.session_state.interests:

    st.caption(
    "✨ Showing your personalized feed: "
    +
    ", ".join(st.session_state.interests)
    )


    if st.session_state.feed_loaded:

        st.success(
            "📰 Your personalized news is ready below!"
        )


search = st.text_input(
    "Search news topic",
    placeholder="Example: Artificial Intelligence"
)


category = st.selectbox(
    "Select News Category",
    categories,
    index=categories.index(sidebar_category)
)


style = st.selectbox(
    "Select Summary Style",
    styles,
    index=styles.index(sidebar_style)
)




# ===============================
# FETCH NEWS
# ===============================

def get_news(search="", category="General"):

    url = (
        f"https://gnews.io/api/v4/top-headlines?"
        f"token={API_KEY}"
        f"&lang=en"
        f"&country=in"
        f"&max=5"
    )


    if search:

        url += f"&q={search}"


    elif st.session_state.interests:

        url += "&q=" + " OR ".join(
            st.session_state.interests
        )


    elif category!="General":

        url += f"&topic={category.lower()}"


    return requests.get(url).json().get(
        "articles",
        []
    )

if st.session_state.feed_loaded and not st.session_state.articles:

    st.session_state.articles = get_news(
        "",
        "General"
    )


# ===============================
# ASK
# ===============================

def ask_news(context,question):

    if not question:
        return "Ask something."


    result = qa_model(
        {
        "context":context,
        "question":question
        }
    )

    return result["answer"]




# ===============================
# GET NEWS
# ===============================

if st.button("Get Today's News"):

    st.session_state.articles = get_news(
        search,
        category
    )




# ===============================
# DISPLAY
# ===============================

if st.session_state.articles:

    st.markdown("## 🔥 Today's Highlights")


    text = " ".join(
        [
            x.get("title","")
            for x in st.session_state.articles
        ]
    )


    highlight = summarizer(
        "Create 3 highlights: " + text[:700],
        max_length=80,
        min_length=20,
        do_sample=False
    )


    st.info(
        highlight[0]["generated_text"]
    )



    for i, article in enumerate(st.session_state.articles):

        title = article.get("title","")
        desc = article.get("description","")
        url = article.get("url","")


        try:

            published_time = datetime.fromisoformat(
                article.get("publishedAt","").replace("Z","")
            ).strftime("%d %b %Y | %I:%M %p")

        except:

            published_time = "Unknown time"



        context = f"{title}. {desc}"


        st.markdown(
            '<div class="news-card">',
            unsafe_allow_html=True
        )


        st.markdown(
        f"""
        <span class="source">
        {article.get("source",{}).get("name","Unknown")}
        • 🕒 {published_time}
        </span>
        """,
        unsafe_allow_html=True
        )


        st.markdown(
        f"""
        <div class="news-title">
        {title}
        </div>
        """,
        unsafe_allow_html=True
        )


        mood = TextBlob(title).sentiment.polarity


        st.write(
            "News Mood:",
            "🟢 Positive" if mood > 0.1 else
            "🔴 Negative" if mood < -0.1 else
            "🟡 Neutral"
        )


        summary = ""


        if desc:

            result = summarizer(
                "Explain simply: " + desc[:500],
                max_length=120,
                min_length=30,
                do_sample=False
            )


            summary = result[0]["generated_text"]


            st.markdown(
            f"""
            <div class="summary">

            <b>AI Summary</b>

            <p>{summary}</p>

            </div>
            """,
            unsafe_allow_html=True
            )



        # ===============================
        # SIDE BY SIDE BUTTONS
        # ===============================

        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                "🔊 Listen",
                key=f"voice_{i}"
            ):

                components.html(
                f"""
                <script>

                let msg =
                new SpeechSynthesisUtterance(
                `{summary}`
                );

                window.speechSynthesis.cancel();

                window.speechSynthesis.speak(msg);

                </script>
                """,
                height=0
                )



        with col2:

            if st.button(
                "🛡 Check Credibility",
                key=f"cred_{i}"
            ):


                source = article.get(
                    "source",
                    {}
                ).get(
                    "name",
                    "Unknown"
                )


                score = 50


                if article.get("url"):
                    score += 20


                if article.get("publishedAt"):
                    score += 20


                credibility = (
                    "🟢 High credibility"
                    if score >= 80
                    else
                    "🟡 Medium credibility"
                )


                st.success(
f"""
Source:
{source}

Reliability:
{credibility}

Score:
{score}/100
"""
                )



        if url:

            st.link_button(
                "🔗 Read full story",
                url
            )



        st.markdown(
            "### 💬 Ask about this news"
        )


        q = st.text_input(
            "Type your question",
            key=f"q_{i}"
        )


        if st.button(
            "Ask",
            key=f"ask_{i}"
        ):

            st.success(
                ask_news(
                    context,
                    q
                )
            )


        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )



else:

    st.info(
        "Click Get Today's News to load articles."
    )
