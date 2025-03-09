from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
from werkzeug.utils import secure_filename
from joblib import load
import numpy as np
import pandas as pd
import re
from bs4 import BeautifulSoup
import json
import os
import yt_dlp
import librosa
import librosa.display
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time
import random
import sqlite3
import google.generativeai as genai
app = Flask(__name__)
app.secret_key = "supersecretkey"


# 設定上傳資料夾
UPLOAD_FOLDER = "../uploads"
ALLOWED_EXTENSIONS = {"wav"}
genai.configure(api_key='')


# 確保上傳資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    """檢查副檔名是否允許"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_features(file_path):
    import librosa
    import numpy as np
    features = []
    y, sr = librosa.load(file_path, sr=None)  # y 是波形, sr 是取樣率
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    features.append(tempo.item())

    pitches, _ = librosa.piptrack(y=y, sr=sr)
    pitch_range = np.max(pitches) - np.min(pitches)
    features.append(pitch_range)
    
    energy = sum(abs(y**2))
    features.append(energy)

    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    avg_valence = spectral_centroid.mean()
    features.append(avg_valence)

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key = chroma.mean(axis=1).argmax()
    features.append(key)
    
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i in range(mfccs.shape[0]):  # 對每個 MFCC 係數計算統計量
        mfcc_mean = np.mean(mfccs[i])
        # mfcc_std = np.std(mfccs[i])
        mfcc_min = np.min(mfccs[i]) 
        mfcc_max = np.max(mfccs[i])
        features.append(mfcc_mean)
        # features.append(mfcc_std)
        features.append(mfcc_min)
        features.append(mfcc_max)
    return features

def predict(file_path):
    from joblib import load
    features = get_features(file_path)
    model = load("Classification_model.joblib")
    test_data = np.array([features])
    prediction = model.predict(test_data)
    label_mapping = {0:'會紅喔!喔耶', 1:'QQ 繼續加油'}
    predicted_label = label_mapping[prediction[0]]
    print(f"你的歌 {predicted_label}")

    if predicted_label == '會紅喔!喔耶':
        model1 = load("regression_model.joblib")
        prediction1 = model1.predict(test_data)
        prediction_day = round(prediction1[0], 2)
        print(f'預計{prediction_day}天會破百萬點閱')
        return prediction_day
    return predicted_label
def download_wav(url):
    if not os.path.exists('music'):
        os.makedirs('music')

    # 設定下載的檔案路徑（會稍後根據清理後的標題動態設定）
    def clean_string(input_string):
        # 定義需要刪除的符號
        special_chars = [
            r'\\', r'\n', r'\r', r'\t', r'\$', '`', r'\u200B', r'/'
        ]
        
        # 逐一刪除特殊符號
        for char in special_chars:
            input_string = input_string.replace(char, "")
        
        # 刪除其他特殊字符
        input_string = re.sub(r'[*+?^=!:${}()|\[\]\/\\\'\"]', '', input_string)  # 刪除正則表達式中的特殊字符

        return input_string

    # 下載並取得檔案名稱
    with yt_dlp.YoutubeDL() as ydl:
        # 先提取影片信息，這裡我們僅提取資訊而不下載
        info_dict = ydl.extract_info(url, download=False)  # 設定download=False，僅提取資訊
        time.sleep(1)
        # 取得標題，並清理
        title = info_dict.get('title', 'unknown_title')
        cleaned_title = clean_string(title)  # 清理標題中的特殊字符

        # 設定清理後的檔案路徑
        output_path = f'../uploads/{cleaned_title}.%(ext)s'

        ydl_opts = {
            'format': 'bestaudio/best',  # 下載最佳音質
            'outtmpl': output_path,  # 設定下載的檔案名稱
            'embed-thumbnail': True,  # 嵌入縮圖
            'add-metadata': True,  # 添加影片元資料
            'extract-audio': True,  # 只提取音訊
            'audio-format': 'wav',  # 強制轉換為 WAV 格式
            'postprocessors': [{  # 轉換音訊為 WAV
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # 指定音訊編碼格式為 WAV
            }],
             # 代理設置（第三點）
            # 'proxy': 'http://your_proxy_server:port',  # 替換為可用的代理服務
            # 模擬用戶代理（第五點）
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
            }
        }
        time.sleep(1)
        # 執行下載並提取資訊
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)  # 設定download=True，開始下載

    # 返回檔案名稱及路徑
    downloaded_file_name = f"{cleaned_title}.wav"
    file_location = os.path.abspath(os.path.join('music', downloaded_file_name))
    print(f"檔案已下載並儲存在: {file_location}")

    return downloaded_file_name, file_location
def generate_gender_data():
    """將「男 + 女」合計控制在 90~99%，其餘給「其他」"""
    total_mf = random.uniform(90, 99)
    male = random.uniform(0, total_mf)
    female = total_mf - male
    other = 100 - total_mf
    return round(male,2), round(female,2), round(other,2)
def generate_country_data():
    """隨機選擇 5 國 + 1「其他」，並用亂數分配比例
    除了「其他」固定在最後，其他國家依百分比從大到小排序
    """
    countries = ["USA", "UK", "Canada", "Germany", "France",
                 "Australia", "Brazil", "Japan", "South Korea", "India"]
    # 隨機選取 5 國
    selected = random.sample(countries, 5)
    # 為選中的 5 國產生亂數數值
    country_values = [random.uniform(1, 10) for _ in range(5)]
    # 為「其他」產生亂數數值
    other_value = random.uniform(1, 10)
    # 將選中的國家依數值由大到小排序
    sorted_countries = sorted(zip(selected, country_values), key=lambda x: x[1], reverse=True)
    sorted_country_names, sorted_country_values = zip(*sorted_countries)
    # 組合排序後的國家與「其他」(固定置底)
    all_categories = list(sorted_country_names) + ["其他"]
    all_values = list(sorted_country_values) + [other_value]
    total = sum(all_values)
    percentages = [round((v / total) * 100, 2) for v in all_values]
    return all_categories[0], percentages[0], all_categories[1],percentages[1], all_categories[2],percentages[2], all_categories[3],percentages[3],all_categories[4],percentages[4]
def generate_percentages(n, base_mean, std_dev):
    """通用隨機分配函式。"""
    values = []
    for _ in range(n):
        val = max(random.gauss(base_mean, std_dev), 1)
        values.append(val)
    total = sum(values)
    final = [round((v / total) * 100, 2) for v in values]
    return final[0], final[1], final[2], final[3], final[4], final[5], final[6], final[7]

def generate_scenario_text(path):
    """呼叫 Gemini API 分析音訊，生成描述文字 (若失敗則回傳錯誤訊息)"""
    try:
        your_file = genai.upload_file(path)
        prompt = (
            "幫我完整的分析這首歌，包括歌曲創作，歌曲情境等等"
        )
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(contents=[prompt, your_file])
        return response.text
    except Exception as e:
        return "音訊分析失敗：" + str(e)

def create_data(username):
    conn = sqlite3.connect("WhaleSignal.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {username} ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    other1 = str(100 - (float(row[11])+float(row[13])+float(row[15])+float(row[17])+float(row[19])))
    other2 = str(100 - (float(row[34])+float(row[36])+float(row[38])+float(row[40])+float(row[42])))
    other3 = str(100 - (float(row[57])+float(row[59])+float(row[61])+float(row[63])+float(row[65])))
    other4 = str(100 - (float(row[80])+float(row[82])+float(row[84])+float(row[86])+float(row[88])))
    other5 = str(100 - (float(row[103])+float(row[105])+float(row[107])+float(row[109])+float(row[111])))
    data_str = {
  "youtube": {
    "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[7], row[8], row[9]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27]]
    },
    "country": {
      "categories": [row[10], row[12], row[14], row[16], row[18],"Other"],
      "percentages": [row[11], row[13], row[15], row[17], row[19], other1]
    },
    "day": row[6],
    "scenario": row[4]
  },
  "spotify": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[30], row[31], row[32]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50]]
    },
    "country": {
      "categories": [row[33], row[35], row[37], row[39], row[41],"Other"],
      "percentages": [row[34], row[36], row[38], row[40], row[42], other2]
    },
    "day": row[29],
    "scenario": row[4] 
              },
  "apple-music": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[53], row[54], row[55]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[66], row[67], row[68], row[69], row[70], row[71], row[72], row[73]]
    },    
    "country": {
      "categories": [row[56], row[58], row[60], row[62], row[64],"Other"],
      "percentages": [row[57], row[59], row[61], row[63], row[65], other3]
    },    
    "day": row[52],
    "scenario": row[4]
  },
  "tidal": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[76], row[77], row[78]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[89], row[90], row[91], row[92], row[93], row[94], row[95], row[96]]
    },  
    "country": {
      "categories": [row[79], row[81], row[83], row[85], row[87],"Other"],
      "percentages": [row[80], row[82], row[84], row[86], row[88], other4]
    },  
    "day": row[75],
    "scenario": row[4]
  },
  "amazon-music": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[99], row[100], row[101]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],   
      "percentages": [row[112], row[113], row[114], row[115], row[116], row[117], row[118], row[119]]
    },
    "country": {
      "categories": [row[102], row[104], row[106], row[108], row[110],"Other"],
      "percentages": [row[103], row[105], row[107], row[109], row[111], other5]    
    },    
    "day": row[98],
    "scenario": row[4]
   }
}
    return data_str
def get_latest_user_song(username):
    conn = sqlite3.connect("WhaleSignal.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {username} ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row[5] == '0':
        fame_indicator = "QQ 繼續加油"
    else:
        fame_indicator = "會紅喔!"
    latest_song = {
        "fame_indicator": fame_indicator,
        "trending_days":row[6],
        "song_name": row[1],
        "upload_time": row[3][:10]
    }
    return latest_song

def fetch_history(user_name):
    conn = sqlite3.connect("WhaleSignal.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f'SELECT id, date as upload_time, filename as song_name FROM "{user_name}" ORDER BY date DESC')
    rows = c.fetchall()
    conn.close()

    history = []
    for r in rows:
        rec = dict(r)
        rec["upload_time"] = rec["upload_time"][:10]  # 轉換日期格式
        rec["id"] = r["id"]
        history.append(rec)

    return history

def create_data_byid(username, id):
    conn = sqlite3.connect("WhaleSignal.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {username} WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    other1 = str(100 - (float(row[11])+float(row[13])+float(row[15])+float(row[17])+float(row[19])))
    other2 = str(100 - (float(row[34])+float(row[36])+float(row[38])+float(row[40])+float(row[42])))
    other3 = str(100 - (float(row[57])+float(row[59])+float(row[61])+float(row[63])+float(row[65])))
    other4 = str(100 - (float(row[80])+float(row[82])+float(row[84])+float(row[86])+float(row[88])))
    other5 = str(100 - (float(row[103])+float(row[105])+float(row[107])+float(row[109])+float(row[111])))
    data_str = {
  "youtube": {
    "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[7], row[8], row[9]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27]]
    },
    "country": {
      "categories": [row[10], row[12], row[14], row[16], row[18],"Other"],
      "percentages": [row[11], row[13], row[15], row[17], row[19], other1]
    },
    "day": row[6],
    "scenario": row[4]
  },
  "spotify": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[30], row[31], row[32]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[43], row[44], row[45], row[46], row[47], row[48], row[49], row[50]]
    },
    "country": {
      "categories": [row[33], row[35], row[37], row[39], row[41],"Other"],
      "percentages": [row[34], row[36], row[38], row[40], row[42], other2]
    },
    "day": row[29],
    "scenario": row[4] 
              },
  "apple-music": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[53], row[54], row[55]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[66], row[67], row[68], row[69], row[70], row[71], row[72], row[73]]
    },    
    "country": {
      "categories": [row[56], row[58], row[60], row[62], row[64],"Other"],
      "percentages": [row[57], row[59], row[61], row[63], row[65], other3]
    },    
    "day": row[52],
    "scenario": row[4]
  },
  "tidal": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[76], row[77], row[78]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],
      "percentages": [row[89], row[90], row[91], row[92], row[93], row[94], row[95], row[96]]
    },  
    "country": {
      "categories": [row[79], row[81], row[83], row[85], row[87],"Other"],
      "percentages": [row[80], row[82], row[84], row[86], row[88], other4]
    },  
    "day": row[75],
    "scenario": row[4]
  },
  "amazon-music": { 
      "gender": {
      "categories": ["Male", "Female", "Other"],
      "percentages": [row[99], row[100], row[101]]
    },
    "age": {
      "categories": ["<12", "13-17", "18-24", "25-34", "35-44", "45-54", "55-64", ">65"],   
      "percentages": [row[112], row[113], row[114], row[115], row[116], row[117], row[118], row[119]]
    },
    "country": {
      "categories": [row[102], row[104], row[106], row[108], row[110],"Other"],
      "percentages": [row[103], row[105], row[107], row[109], row[111], other5]    
    },    
    "day": row[98],
    "scenario": row[4]
   }
}
    return data_str
def get_ID_user_song(username, id):
    conn = sqlite3.connect("WhaleSignal.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {username} WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row[5] == '0':
        fame_indicator = "QQ 繼續加油"
    else:
        fame_indicator = "會紅喔!"
    latest_song = {
        "fame_indicator": fame_indicator,
        "trending_days":row[6],
        "song_name": row[1],
        "upload_time": row[3][:10]
    }
    return latest_song



# ==============================================================================================================================================================

@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    import datetime
    """處理音檔上傳"""
    print('hiiiiii')
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)  # 儲存檔案
    filepath.replace("\\", "/")
    print(filepath)
    print("分析中......")
    output = predict(filepath)
    if output == 'QQ 繼續加油':
        output = '0'
        day = 1
    else:
        day = output
        output = '1'
    date = datetime.datetime.now()
    scenario = generate_scenario_text(filepath)
    yt_boy, yt_girl, yt_other = generate_gender_data()
    spo_boy, spo_girl, spo_other = generate_gender_data()
    apl_boy, apl_girl, apl_other = generate_gender_data()
    tid_boy, tid_girl, tid_other = generate_gender_data()
    ama_boy, ama_girl, ama_other = generate_gender_data()
    yt_country1, yt_percent1, yt_country2, yt_percent2, yt_country3, yt_percent3, yt_country4, yt_percent4, yt_country5, yt_percent5 = generate_country_data()
    spo_country1, spo_percent1, spo_country2, spo_percent2, spo_country3, spo_percent3, spo_country4, spo_percent4, spo_country5, spo_percent5 = generate_country_data()
    apl_country1, apl_percent1, apl_country2, apl_percent2, apl_country3, apl_percent3, apl_country4, apl_percent4, apl_country5, apl_percent5 = generate_country_data()
    tid_country1, tid_percent1, tid_country2, tid_percent2, tid_country3, tid_percent3, tid_country4, tid_percent4, tid_country5, tid_percent5 = generate_country_data()
    ama_country1, ama_percent1, ama_country2, ama_percent2, ama_country3, ama_percent3, ama_country4, ama_percent4, ama_country5, ama_percent5 = generate_country_data()
    yt_under_12, yt_13_17, yt_18_24, yt_25_34, yt_35_44, yt_45_54, yt_55_64, yt_over_65 = generate_percentages(8, 12.5, 2)
    spo_under_12, spo_13_17, spo_18_24, spo_25_34, spo_35_44, spo_45_54, spo_55_64, spo_over_65 = generate_percentages(8, 12.5, 2)
    apl_under_12, apl_13_17, apl_18_24, apl_25_34, apl_35_44, apl_45_54, apl_55_64, apl_over_65 = generate_percentages(8, 12.5, 2)
    tid_under_12, tid_13_17, tid_18_24, tid_25_34, tid_35_44, tid_45_54, tid_55_64, tid_over_65 = generate_percentages(8, 12.5, 2)  
    ama_under_12, ama_13_17, ama_18_24, ama_25_34, ama_35_44, ama_45_54, ama_55_64, ama_over_65 = generate_percentages(8, 12.5, 2)
    print(session['username'])
    connect = sqlite3.connect('WhaleSignal.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {session['username']} (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   filename TEXT, 
                   filepath TEXT,
                   date TEXT,
                   scenario TEXT,
                   yt_good_or_bad TEXT,
                   yt_day TEXT,
                   yt_boy TEXT,
                   yt_girl TEXT,
                   yt_other TEXT,
                   yt_country1 TEXT,
                   yt_percent1 TEXT,
                   yt_country2 TEXT,
                   yt_percent2 TEXT,
                   yt_country3 TEXT,
                   yt_percent3 TEXT,
                   yt_country4 TEXT,
                   yt_percent4 TEXT,
                   yt_country5 TEXT,
                   yt_percent5 TEXT,
                   yt_under_12 TEXT,
                   yt_13_17 TEXT,
                   yt_18_24 TEXT,
                   yt_25_34 TEXT,
                   yt_35_44 TEXT,                                    
                   yt_45_54 TEXT,
                   yt_55_64 TEXT,
                   yt_over_65 TEXT,
                   spo_good_or_bad TEXT,
                   spo_day TEXT,
                   spo_boy TEXT,
                   spo_girl TEXT,
                   spo_other TEXT,
                   spo_country1 TEXT,
                   spo_percent1 TEXT,
                   spo_country2 TEXT,
                   spo_percent2 TEXT,
                   spo_country3 TEXT,
                   spo_percent3 TEXT,
                   spo_country4 TEXT,
                   spo_percent4 TEXT,
                   spo_country5 TEXT,
                   spo_percent5 TEXT,
                   spo_under_12 TEXT,
                   spo_13_17 TEXT,
                   spo_18_24 TEXT,
                   spo_25_34 TEXT,
                   spo_35_44 TEXT,                                    
                   spo_45_54 TEXT,
                   spo_55_64 TEXT,
                   spo_over_65 TEXT,
                   apl_good_or_bad TEXT,
                   apl_day TEXT,
                   apl_boy TEXT,
                   apl_girl TEXT,
                   apl_other TEXT,
                   apl_country1 TEXT,
                   apl_percent1 TEXT,
                   apl_country2 TEXT,
                   apl_percent2 TEXT,
                   apl_country3 TEXT,
                   apl_percent3 TEXT,
                   apl_country4 TEXT,
                   apl_percent4 TEXT,
                   apl_country5 TEXT,
                   apl_percent5 TEXT,
                   apl_under_12 TEXT,
                   apl_13_17 TEXT,
                   apl_18_24 TEXT,
                   apl_25_34 TEXT,
                   apl_35_44 TEXT,                                    
                   apl_45_54 TEXT,
                   apl_55_64 TEXT,
                   apl_over_65 TEXT,
                   tid_good_or_bad TEXT,
                   tid_day TEXT,
                   tid_boy TEXT,
                   tid_girl TEXT,
                   tid_other TEXT,
                   tid_country1 TEXT,
                   tid_percent1 TEXT,
                   tid_country2 TEXT,
                   tid_percent2 TEXT,
                   tid_country3 TEXT,
                   tid_percent3 TEXT,
                   tid_country4 TEXT,
                   tid_percent4 TEXT,
                   tid_country5 TEXT,
                   tid_percent5 TEXT,
                   tid_under_12 TEXT,
                   tid_13_17 TEXT,
                   tid_18_24 TEXT,
                   tid_25_34 TEXT,
                   tid_35_44 TEXT,                                    
                   tid_45_54 TEXT,
                   tid_55_64 TEXT,
                   tid_over_65 TEXT,
                   ama_good_or_bad TEXT,
                   ama_day TEXT,
                   ama_boy TEXT,
                   ama_girl TEXT,
                   ama_other TEXT,
                   ama_country1 TEXT,
                   ama_percent1 TEXT,
                   ama_country2 TEXT,
                   ama_percent2 TEXT,
                   ama_country3 TEXT,
                   ama_percent3 TEXT,
                   ama_country4 TEXT,
                   ama_percent4 TEXT,
                   ama_country5 TEXT,
                   ama_percent5 TEXT,
                   ama_under_12 TEXT,
                   ama_13_17 TEXT,
                   ama_18_24 TEXT,
                   ama_25_34 TEXT,
                   ama_35_44 TEXT,                                    
                   ama_45_54 TEXT,
                   ama_55_64 TEXT,
                   ama_over_65 TEXT              
                   )""")
    cursor.execute(f""" INSERT into {session['username']} (filename, filepath, date, scenario, yt_good_or_bad,yt_day,yt_boy,yt_girl,yt_other,yt_country1,yt_percent1,yt_country2,yt_percent2,yt_country3,yt_percent3,yt_country4,yt_percent4,yt_country5,yt_percent5,yt_under_12,yt_13_17,yt_18_24,yt_25_34,yt_35_44,yt_45_54,yt_55_64,yt_over_65,spo_good_or_bad,spo_day,spo_boy,spo_girl,spo_other,spo_country1,spo_percent1,spo_country2,spo_percent2,spo_country3,spo_percent3,spo_country4,spo_percent4,spo_country5,spo_percent5,spo_under_12,spo_13_17,spo_18_24,spo_25_34,spo_35_44,spo_45_54,spo_55_64,spo_over_65,apl_good_or_bad,apl_day,apl_boy,apl_girl,apl_other,apl_country1,apl_percent1,apl_country2,apl_percent2,apl_country3,apl_percent3,apl_country4,apl_percent4,apl_country5,apl_percent5,apl_under_12,apl_13_17,apl_18_24,apl_25_34,apl_35_44,apl_45_54,apl_55_64,apl_over_65,tid_good_or_bad,tid_day,tid_boy,tid_girl,tid_other,tid_country1,tid_percent1,tid_country2,tid_percent2,tid_country3,tid_percent3,tid_country4,tid_percent4,tid_country5,tid_percent5,tid_under_12,tid_13_17,tid_18_24,tid_25_34,tid_35_44,tid_45_54,tid_55_64,tid_over_65,ama_good_or_bad,ama_day,ama_boy,ama_girl,ama_other,ama_country1,ama_percent1,ama_country2,ama_percent2,ama_country3,ama_percent3,ama_country4,ama_percent4,ama_country5,ama_percent5,ama_under_12,ama_13_17,ama_18_24,ama_25_34,ama_35_44,ama_45_54,ama_55_64,ama_over_65) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   ((filename, filepath, date, scenario, output, day ,yt_boy,yt_girl,yt_other,yt_country1,yt_percent1,yt_country2,yt_percent2,yt_country3,yt_percent3,yt_country4,yt_percent4,yt_country5,yt_percent5,yt_under_12,yt_13_17,yt_18_24,yt_25_34,yt_35_44,yt_45_54,yt_55_64,yt_over_65,output,day+2,spo_boy,spo_girl,spo_other,spo_country1,spo_percent1,spo_country2,spo_percent2,spo_country3,spo_percent3,spo_country4,spo_percent4,spo_country5,spo_percent5,spo_under_12,spo_13_17,spo_18_24,spo_25_34,spo_35_44,spo_45_54,spo_55_64,spo_over_65,output,day-3,apl_boy,apl_girl,apl_other,apl_country1,apl_percent1,apl_country2,apl_percent2,apl_country3,apl_percent3,apl_country4,apl_percent4,apl_country5,apl_percent5,apl_under_12,apl_13_17,apl_18_24,apl_25_34,apl_35_44,apl_45_54,apl_55_64,apl_over_65,output,day+4,tid_boy,tid_girl,tid_other,tid_country1,tid_percent1,tid_country2,tid_percent2,tid_country3,tid_percent3,tid_country4,tid_percent4,tid_country5,tid_percent5,tid_under_12,tid_13_17,tid_18_24,tid_25_34,tid_35_44,tid_45_54,tid_55_64,tid_over_65,output,day-2,ama_boy,ama_girl,ama_other,ama_country1,ama_percent1,ama_country2,ama_percent2,ama_country3,ama_percent3,ama_country4,ama_percent4,ama_country5,ama_percent5,ama_under_12,ama_13_17,ama_18_24,ama_25_34,ama_35_44,ama_45_54,ama_55_64,ama_over_65)
                   )
                   )
    connect.commit()
    try:
        if os.path.exists(filepath):
                os.remove(filepath)
                print(f"檔案 {filepath} 已刪除")
    except:
        pass
    # create_data(session['username'])
    return jsonify({"message": "File uploaded successfully", "file_path": filepath}), 200  # ✅ 正確回應
@app.route("/upload_url", methods=["POST"])
def upload_url():
    import datetime
    """處理 YouTube 連結上傳"""
    print('hello')
    data = request.get_json()
    
    if not data or "youtube_url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    youtube_url = data["youtube_url"]
    # 這裡可以加入下載音檔的邏輯，例如使用 yt-dlp 下載
    filename, filepath = download_wav(youtube_url)
    filepath ='../uploads/' + filename
    output = predict(filepath)
    if output == 'QQ 繼續加油':
        output = '0'
        day = 1
    else:
        day = output
        output = '1'
    date = datetime.datetime.now()
    scenario = generate_scenario_text(filepath)
    yt_boy, yt_girl, yt_other = generate_gender_data()
    spo_boy, spo_girl, spo_other = generate_gender_data()
    apl_boy, apl_girl, apl_other = generate_gender_data()
    tid_boy, tid_girl, tid_other = generate_gender_data()
    ama_boy, ama_girl, ama_other = generate_gender_data()
    yt_country1, yt_percent1, yt_country2, yt_percent2, yt_country3, yt_percent3, yt_country4, yt_percent4, yt_country5, yt_percent5 = generate_country_data()
    spo_country1, spo_percent1, spo_country2, spo_percent2, spo_country3, spo_percent3, spo_country4, spo_percent4, spo_country5, spo_percent5 = generate_country_data()
    apl_country1, apl_percent1, apl_country2, apl_percent2, apl_country3, apl_percent3, apl_country4, apl_percent4, apl_country5, apl_percent5 = generate_country_data()
    tid_country1, tid_percent1, tid_country2, tid_percent2, tid_country3, tid_percent3, tid_country4, tid_percent4, tid_country5, tid_percent5 = generate_country_data()
    ama_country1, ama_percent1, ama_country2, ama_percent2, ama_country3, ama_percent3, ama_country4, ama_percent4, ama_country5, ama_percent5 = generate_country_data()
    yt_under_12, yt_13_17, yt_18_24, yt_25_34, yt_35_44, yt_45_54, yt_55_64, yt_over_65 = generate_percentages(8, 12.5, 2)
    spo_under_12, spo_13_17, spo_18_24, spo_25_34, spo_35_44, spo_45_54, spo_55_64, spo_over_65 = generate_percentages(8, 12.5, 2)
    apl_under_12, apl_13_17, apl_18_24, apl_25_34, apl_35_44, apl_45_54, apl_55_64, apl_over_65 = generate_percentages(8, 12.5, 2)
    tid_under_12, tid_13_17, tid_18_24, tid_25_34, tid_35_44, tid_45_54, tid_55_64, tid_over_65 = generate_percentages(8, 12.5, 2)  
    ama_under_12, ama_13_17, ama_18_24, ama_25_34, ama_35_44, ama_45_54, ama_55_64, ama_over_65 = generate_percentages(8, 12.5, 2)
    print(session['username'])
    connect = sqlite3.connect('WhaleSignal.db', check_same_thread=False)
    cursor = connect.cursor()
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {session['username']} (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   filename TEXT, 
                   filepath TEXT,
                   date TEXT,
                   scenario TEXT,
                   yt_good_or_bad TEXT,
                   yt_day TEXT,
                   yt_boy TEXT,
                   yt_girl TEXT,
                   yt_other TEXT,
                   yt_country1 TEXT,
                   yt_percent1 TEXT,
                   yt_country2 TEXT,
                   yt_percent2 TEXT,
                   yt_country3 TEXT,
                   yt_percent3 TEXT,
                   yt_country4 TEXT,
                   yt_percent4 TEXT,
                   yt_country5 TEXT,
                   yt_percent5 TEXT,
                   yt_under_12 TEXT,
                   yt_13_17 TEXT,
                   yt_18_24 TEXT,
                   yt_25_34 TEXT,
                   yt_35_44 TEXT,                                    
                   yt_45_54 TEXT,
                   yt_55_64 TEXT,
                   yt_over_65 TEXT,
                   spo_good_or_bad TEXT,
                   spo_day TEXT,
                   spo_boy TEXT,
                   spo_girl TEXT,
                   spo_other TEXT,
                   spo_country1 TEXT,
                   spo_percent1 TEXT,
                   spo_country2 TEXT,
                   spo_percent2 TEXT,
                   spo_country3 TEXT,
                   spo_percent3 TEXT,
                   spo_country4 TEXT,
                   spo_percent4 TEXT,
                   spo_country5 TEXT,
                   spo_percent5 TEXT,
                   spo_under_12 TEXT,
                   spo_13_17 TEXT,
                   spo_18_24 TEXT,
                   spo_25_34 TEXT,
                   spo_35_44 TEXT,                                    
                   spo_45_54 TEXT,
                   spo_55_64 TEXT,
                   spo_over_65 TEXT,
                   apl_good_or_bad TEXT,
                   apl_day TEXT,
                   apl_boy TEXT,
                   apl_girl TEXT,
                   apl_other TEXT,
                   apl_country1 TEXT,
                   apl_percent1 TEXT,
                   apl_country2 TEXT,
                   apl_percent2 TEXT,
                   apl_country3 TEXT,
                   apl_percent3 TEXT,
                   apl_country4 TEXT,
                   apl_percent4 TEXT,
                   apl_country5 TEXT,
                   apl_percent5 TEXT,
                   apl_under_12 TEXT,
                   apl_13_17 TEXT,
                   apl_18_24 TEXT,
                   apl_25_34 TEXT,
                   apl_35_44 TEXT,                                    
                   apl_45_54 TEXT,
                   apl_55_64 TEXT,
                   apl_over_65 TEXT,
                   tid_good_or_bad TEXT,
                   tid_day TEXT,
                   tid_boy TEXT,
                   tid_girl TEXT,
                   tid_other TEXT,
                   tid_country1 TEXT,
                   tid_percent1 TEXT,
                   tid_country2 TEXT,
                   tid_percent2 TEXT,
                   tid_country3 TEXT,
                   tid_percent3 TEXT,
                   tid_country4 TEXT,
                   tid_percent4 TEXT,
                   tid_country5 TEXT,
                   tid_percent5 TEXT,
                   tid_under_12 TEXT,
                   tid_13_17 TEXT,
                   tid_18_24 TEXT,
                   tid_25_34 TEXT,
                   tid_35_44 TEXT,                                    
                   tid_45_54 TEXT,
                   tid_55_64 TEXT,
                   tid_over_65 TEXT,
                   ama_good_or_bad TEXT,
                   ama_day TEXT,
                   ama_boy TEXT,
                   ama_girl TEXT,
                   ama_other TEXT,
                   ama_country1 TEXT,
                   ama_percent1 TEXT,
                   ama_country2 TEXT,
                   ama_percent2 TEXT,
                   ama_country3 TEXT,
                   ama_percent3 TEXT,
                   ama_country4 TEXT,
                   ama_percent4 TEXT,
                   ama_country5 TEXT,
                   ama_percent5 TEXT,
                   ama_under_12 TEXT,
                   ama_13_17 TEXT,
                   ama_18_24 TEXT,
                   ama_25_34 TEXT,
                   ama_35_44 TEXT,                                    
                   ama_45_54 TEXT,
                   ama_55_64 TEXT,
                   ama_over_65 TEXT              
                   )""")
    cursor.execute(f""" INSERT into {session['username']} (filename, filepath, date, scenario, yt_good_or_bad,yt_day,yt_boy,yt_girl,yt_other,yt_country1,yt_percent1,yt_country2,yt_percent2,yt_country3,yt_percent3,yt_country4,yt_percent4,yt_country5,yt_percent5,yt_under_12,yt_13_17,yt_18_24,yt_25_34,yt_35_44,yt_45_54,yt_55_64,yt_over_65,spo_good_or_bad,spo_day,spo_boy,spo_girl,spo_other,spo_country1,spo_percent1,spo_country2,spo_percent2,spo_country3,spo_percent3,spo_country4,spo_percent4,spo_country5,spo_percent5,spo_under_12,spo_13_17,spo_18_24,spo_25_34,spo_35_44,spo_45_54,spo_55_64,spo_over_65,apl_good_or_bad,apl_day,apl_boy,apl_girl,apl_other,apl_country1,apl_percent1,apl_country2,apl_percent2,apl_country3,apl_percent3,apl_country4,apl_percent4,apl_country5,apl_percent5,apl_under_12,apl_13_17,apl_18_24,apl_25_34,apl_35_44,apl_45_54,apl_55_64,apl_over_65,tid_good_or_bad,tid_day,tid_boy,tid_girl,tid_other,tid_country1,tid_percent1,tid_country2,tid_percent2,tid_country3,tid_percent3,tid_country4,tid_percent4,tid_country5,tid_percent5,tid_under_12,tid_13_17,tid_18_24,tid_25_34,tid_35_44,tid_45_54,tid_55_64,tid_over_65,ama_good_or_bad,ama_day,ama_boy,ama_girl,ama_other,ama_country1,ama_percent1,ama_country2,ama_percent2,ama_country3,ama_percent3,ama_country4,ama_percent4,ama_country5,ama_percent5,ama_under_12,ama_13_17,ama_18_24,ama_25_34,ama_35_44,ama_45_54,ama_55_64,ama_over_65) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   ((filename, filepath, date, scenario, output, day ,yt_boy,yt_girl,yt_other,yt_country1,yt_percent1,yt_country2,yt_percent2,yt_country3,yt_percent3,yt_country4,yt_percent4,yt_country5,yt_percent5,yt_under_12,yt_13_17,yt_18_24,yt_25_34,yt_35_44,yt_45_54,yt_55_64,yt_over_65,output,day+2,spo_boy,spo_girl,spo_other,spo_country1,spo_percent1,spo_country2,spo_percent2,spo_country3,spo_percent3,spo_country4,spo_percent4,spo_country5,spo_percent5,spo_under_12,spo_13_17,spo_18_24,spo_25_34,spo_35_44,spo_45_54,spo_55_64,spo_over_65,output,day-3,apl_boy,apl_girl,apl_other,apl_country1,apl_percent1,apl_country2,apl_percent2,apl_country3,apl_percent3,apl_country4,apl_percent4,apl_country5,apl_percent5,apl_under_12,apl_13_17,apl_18_24,apl_25_34,apl_35_44,apl_45_54,apl_55_64,apl_over_65,output,day+4,tid_boy,tid_girl,tid_other,tid_country1,tid_percent1,tid_country2,tid_percent2,tid_country3,tid_percent3,tid_country4,tid_percent4,tid_country5,tid_percent5,tid_under_12,tid_13_17,tid_18_24,tid_25_34,tid_35_44,tid_45_54,tid_55_64,tid_over_65,output,day-2,ama_boy,ama_girl,ama_other,ama_country1,ama_percent1,ama_country2,ama_percent2,ama_country3,ama_percent3,ama_country4,ama_percent4,ama_country5,ama_percent5,ama_under_12,ama_13_17,ama_18_24,ama_25_34,ama_35_44,ama_45_54,ama_55_64,ama_over_65)
                   )
                   )
    connect.commit()
    try:
        if os.path.exists(filepath):
                os.remove(filepath)
                print(f"檔案 {filename} 已刪除")
    except:
        pass
    return jsonify({"message": "URL received", "youtube_url": youtube_url}), 200

@app.route("/analysis/<int:record_id>")
def analysis1(record_id):
    chart_data = create_data_byid(session['username'], record_id)
    data_str = json.dumps(chart_data, ensure_ascii=False)
    ID_song = get_ID_user_song(session['username'], record_id)
    history_records = fetch_history(session['username'])
    return render_template("BD3.html",
                           data_str=data_str,
                           myname=session['username'],
                           latest_song= ID_song,
                           history_records=history_records)

@app.route("/check_user_records", methods=["GET"])
def check_user_records():
    username = request.args.get("username")

    if not username:
        return jsonify({"error": "Missing username"}), 400

    conn = sqlite3.connect("WhaleSignal.db")
    cursor = conn.cursor()

    # 檢查資料庫是否有該使用者的 table
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (username,))
    table_exists = cursor.fetchone()

    conn.close()

    return jsonify({"has_records": bool(table_exists)})

@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    chart_data = create_data(session['username'])
    data_str = json.dumps(chart_data, ensure_ascii=False)
    latest_song = get_latest_user_song(session['username'])
    history_records = fetch_history(session['username'])
    return render_template("BD3.html",
                           data_str=data_str,
                           myname=session['username'],
                           latest_song=latest_song,
                           history_records=history_records)
    # return render_template("BD3.html")
@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    return render_template("loginpage.html")
@app.route('/pay', methods=["GET", "POST"])
def pay():
    username = session.get('username')  # 取得 Session 中的 username
    return render_template('pay.html', username=username)
@app.route('/go_to_pay')
def go_to_pay():
    return redirect(url_for('pay', _external=True))
@app.route("/success", methods=["GET", "POST"])
def success():
    return render_template("success.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()

            print(f"📢 登入請求：email={email}, password={password}")  # 🔍 Debug

            if not email or not password:
                return jsonify({"message": "請輸入 Email 和密碼！", "status": "error"}), 400

            with sqlite3.connect('WhaleSignal.db', check_same_thread=False) as connect:
                cursor = connect.cursor()

                # ✅ 查詢使用者
                cursor.execute("SELECT id, username, permission FROM users WHERE email = ? AND password = ?", (email, password))
                user = cursor.fetchone()

            if user:
                session["user_id"] = user[0]
                session["username"] = user[1]
                session["permission"] = user[2]
                print(f"✅ 登入成功！使用者: {session['username']}")  # 🔍 Debug
                return jsonify({"message": "登入成功！", "status": "success",'permission': user[2],"user_id": session['user_id'],"username": session['username'], "redirect": "/"}), 200
            else:
                print("❌ 帳號或密碼錯誤")  # 🔍 Debug
                return jsonify({"message": "帳號或密碼錯誤！", "status": "error"}), 401
        return jsonify({"message": "請使用 POST 方法登入", "status": "error"}), 405
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")  # 🔍 Debug

    # ✅ 確保 `GET` 也回傳 JSON，而不是 `HTML`
    
@app.route("/create_account", methods=["POST"])
def create_account():
    try:
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # ✅ Email 格式驗證
        email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_pattern, email):
            return jsonify({"message": "Email 格式不正確！", "status": "error"}), 400

        if not email or not username or not password or not confirm_password:
            return jsonify({"message": "請填寫所有欄位！", "status": "error"}), 400  

        if password != confirm_password:
            return jsonify({"message": "密碼與確認密碼不一致！", "status": "error"}), 400

        # ✅ 使用 `with` 確保連線釋放
        with sqlite3.connect("WhaleSignal.db", check_same_thread=False) as connect:
            cursor = connect.cursor()

            # ✅ 創建 `users` 資料表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    permission INT NOT NULL
                )
            ''')

            # ✅ 檢查帳號是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify({"message": "此 Email 或 Username 已被使用！", "status": "error"}), 400

            # ✅ 插入新帳戶
            cursor.execute("INSERT INTO users (email, username, password, permission) VALUES (?, ?, ?, ?)", 
                        (email, username, password, 0))
            connect.commit()

            print(f"✅ 帳戶建立成功！Email: {email}, Username: {username}")

        return jsonify({"message": "帳號創建成功！請登入", "status": "success", "redirect": "/log_in"}), 200  

    except sqlite3.OperationalError as e:
        print(f"❌ SQLite 錯誤: {str(e)}")
        return jsonify({"message": "資料庫錯誤，請稍後再試！", "status": "error"}), 500
    except Exception as e:
        print(f"❌ 伺服器錯誤: {str(e)}")
        return jsonify({"message": "伺服器錯誤，請稍後再試！", "status": "error"}), 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 8080))  # Render 需要使用 PORT 變數
    serve(app, host='0.0.0.0', port=port)
