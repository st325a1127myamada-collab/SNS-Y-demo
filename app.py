# SNSアプリ
#==================================
import streamlit as st
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import os
import json
from datetime import datetime

# 設定
# =====================
USERS_FILE = "users.json"               #ユーザー情報を保存するファイル名(大量に文字列を生成してしまう)
POSTS_FILE = "posts.json"               #投稿データを保存するファイル名(〃)
DEFAULT_ICON = "icon_user_light.png"    #ユーザーがアイコン未設定の際に使う画像

# ロゴ生成
# =====================
def load_logo_rounded():
    img = Image.open("y.jpg").convert("RGBA")
    img = img.resize((64, 64))

    mask = Image.new("L", (64, 64), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 64, 64), radius=12, fill=255)

    out = Image.new("RGBA", (64, 64))
    out.paste(img, (0, 0), mask)

    buf = BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

LOGO_BASE64 = load_logo_rounded()

# JSONヘルパー
# =====================
def load_json(path, default): 
    if not os.path.exists(path):                  #ファイルが存在するか確認
        return default
    with open(path, "r", encoding="utf-8") as f:  #ファイルがあれば読み込み
        return json.load(f)                       #JSON → Python に変換

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json(USERS_FILE, {})   #ユーザー情報は辞書(dict)
posts = load_json(POSTS_FILE, [])   #投稿情報はリスト(list)


#以下　アプリに視覚的に関わるコード

# 初期設定
# =====================
st.set_page_config(page_title="Y", layout="wide") #初期レイアウト

if "current_user" not in st.session_state:
    st.session_state.current_user = None          #保存領域 current_userが未定義=None

# CSS                                            　HTML/CSSを直接書く
# =====================
st.markdown("""
<style>
body { background:#F5F8FA; }
.card {
    background:white;
    border-radius:12px;
    padding:12px;
    margin-bottom:12px;
    box-shadow:0 2px 6px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)           #外部入力を受け付けると実行されてしまうXSS

# 画像ユーティリティ
# =====================
def pil_to_b64(img: Image.Image):      #PIL画像→Base64(文字列)
    buf = BytesIO()                    #メモリ上にある仮ファイル作成
    img.save(buf, format="PNG")        #PNGをメモリに保存
    return base64.b64encode(buf.getvalue()).decode()    #バイト列→文字列

def b64_to_pil(b64, default_path=None):                 #Base64(文字列)→PIL画像
    try:
        return Image.open(BytesIO(base64.b64decode(b64)))
    except Exception:                  #エラー時に灰色のダミー画像表示
        return Image.open(default_path) if default_path and os.path.exists(default_path) else Image.new("RGB", (100,100), (200,200,200))

def circle_icon(pil_img, size=48):     #アイコン画像を丸くする
    pil_img = pil_img.convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(pil_img, (0, 0), mask)
    return out

# ユーザー作成
# =====================
def create_user(name, userid, icon_pil):
    users[userid] = {                  #user辞書に新しいユーザーを追加
        "name": name,                  #以下表示用の関数
        "userid": f"@{userid}",
        "icon": pil_to_b64(icon_pil)   #Base64に変換
    }
    save_json(USERS_FILE, users)
    return userid

# 投稿作成
# =====================
def create_post(author, text, image=None):  #投稿したユーザー、本文、画像（なしも可）
    posts.insert(0, {                       #最新の投稿を一番上にする
        "id": datetime.now().strftime('%Y%m%d%H%M%S%f'),    #現在時刻ID
        "author": author,
        "text": text,
        "image": image,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M'),  #時刻表示
        "likes": 0,                                         #いいね数
        "replies": []                                       #コメント機能用
    })
    save_json(POSTS_FILE, posts)

# 投稿表示
# =====================
def render_post(post):
    user = users.get(post["author"], {})  #辞書からユーザーを情報を取得、｛｝は未定義エラー防止

    icon_pil = b64_to_pil(user.get("icon"), DEFAULT_ICON)       #画像をBase64→PIL画像
    icon = circle_icon(icon_pil)
    buf = BytesIO(); icon.save(buf, format="PNG")               #PIL画像→Base64
    icon_b64 = base64.b64encode(buf.getvalue()).decode()        #HTMLで<img>として表示を可能に

    st.markdown('<div class="card">', unsafe_allow_html=True)   #CSSの{card}を使用
    st.markdown(f"""
    <div style='display:flex; gap:10px;'>
        <img src='data:image/png;base64,{icon_b64}' width='48'>
        <div>
            <b>{user.get('name')}</b> <span style='color:gray'>{user.get('userid')}</span><br>
            {post['text']}
        </div>
    </div>
    """, unsafe_allow_html=True)                                #投稿の表示関連

    if post.get("image"):
        st.image(Image.open(BytesIO(base64.b64decode(post["image"]))))          #画像があれば、Base64→PIL→Streamlit表示

    if st.button(f"♡ {post['likes']}", key=f"like_{post['id']}"):  #いいね表示
        post["likes"] += 1
        save_json(POSTS_FILE, posts)
        st.rerun()                                                 #再描写

    st.markdown(f"<div style='color:gray;font-size:12px'>{post['time']}</div>", #投稿時刻表示
                unsafe_allow_html=True
                )

    for r in post["replies"]:                                       #コメント欄表示
        reply_user = users.get(r["user"], {})
        reply_icon_pil = b64_to_pil(reply_user.get("icon"), DEFAULT_ICON)       #アイコン取得 Base64→PIL画像
        reply_icon = circle_icon(reply_icon_pil, size=32)
        buf = BytesIO()
        reply_icon.save(buf, format="PNG")
        reply_icon_b64 = base64.b64encode(buf.getvalue()).decode()
        
        st.markdown(f"""
                <div style="display:flex; gap:8px; margin-left:20px; margin-top:6px;">
                    <img src="data:image/png;base64,{reply_icon_b64}" width="32">
                    <div>
                        <b>{reply_user.get("name")}</b>
                        <span style="color:gray; font-size:12px;">
                            {reply_user.get("userid", "")}
                        </span><br>
                        {r["text"]}
                    </div>
                </div>
        """, unsafe_allow_html=True)                #コメントした際のアイコン表示詳細


    with st.form(f"reply_{post['id']}"):            #投稿ごとの独立したコメントフォーム
        reply = st.text_input("返信")                #コメント入力欄
        if st.form_submit_button("送信") and reply:                #空投稿防止
            post["replies"].append({                 #コメントを投稿データに追加
                "user": st.session_state.current_user,
                "text": reply,
                "time": datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            save_json(POSTS_FILE, posts)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)                  #投稿終了

# レイアウト
# =====================
col_left, col_main = st.columns([1,4])      #画面を2つのカラムに分割 左右1:4

with col_left:                              #画面左部分
    st.markdown(f"<img src='data:image/png;base64,{LOGO_BASE64}'>", unsafe_allow_html=True) #Base64の画像をHTMLで表示(ロゴ)

with col_main:                              #画面メイン部分
    if st.session_state.current_user is None:                                         #「session_state」にユーザーがいなければ、登録画面
        st.subheader("ユーザー登録")
        name = st.text_input("ユーザー名")
        userid = st.text_input("アカウントID")
        icon = st.file_uploader("アイコン画像", type=["png","jpg","jpeg"])

        if st.button("開始") and name and userid:                                     #必須項目が入力済みで「開始」を押す
            icon_pil = Image.open(icon) if icon else Image.open(DEFAULT_ICON)         #アイコンを設定（未定義でデフォルトアイコン）
            st.session_state.current_user = create_user(name, userid, icon_pil)       #ユーザー作成、セッションに「ログイン状態」を保存
            st.rerun()                      #ホーム画面へ
    else:
        st.header("ホーム")                 #ログイン済み

        with st.form("post"):              #投稿フォーム（Enterで誤送信防止）
            text = st.text_area("今どうしてる？")
            img = st.file_uploader("画像（任意）", type=["png","jpg","jpeg"])
            if st.form_submit_button("投稿") and text:
                img_b64 = base64.b64encode(img.read()).decode() if img else None      #画像をBase64に変換
                create_post(st.session_state.current_user, text, img_b64)             #投稿作成
                st.rerun()

        for post in posts:                 #投稿をタイムラインに表示
            render_post(post)