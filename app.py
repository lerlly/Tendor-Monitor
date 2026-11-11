import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 设置网页基本属性
st.set_page_config(page_title="全国核酸检测产品招标监控台", page_icon="🔬", layout="wide")

@st.cache_data(ttl=3600)
def fetch_bidding_data(keyword="核酸检测 疾控"):
    """
    针对中国政府采购网(CCGP)的真实爬虫逻辑
    """
    # 中国政府采购网的高级搜索接口
    url = "http://search.ccgp.gov.cn/bxsearch"
    
    # 构造请求参数：指定搜索关键词，按时间倒序排，时间范围为近3个月
    params = {
        "searchtype": 1,
        "page_index": 1,
        "bidSort": 0,
        "buyerName": "",
        "projectId": "",
        "pinYin": 0,
        "displayZone": "",
        "zoneId": "",
        "pppStatus": 0,
        "agentName": "",
        "timeType": 5, # 5表示近3个月
        "keyword": keyword
    }
    
    # 模拟真实浏览器，防止被服务器直接拒绝
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Host": "search.ccgp.gov.cn"
    }

    data_list = []
    
    try:
        # 发送网络请求
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 确保中文字符正常解码
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 政府采购网的搜索结果存放在 class="vT-srch-result-list-bid" 的 ul 标签下的 li 中
            results = soup.find_all('ul', class_='vT-srch-result-list-bid')
            
            if results:
                items = results[0].find_all('li')
                for item in items:
                    # 提取项目链接和名称
                    a_tag = item.find('a')
                    link = a_tag['href'] if a_tag else ""
                    title = a_tag.get_text(strip=True) if a_tag else "未知项目名称"
                    
                    # 提取发布时间、采购人等附加信息
                    info_span = item.find_all('span')
                    publish_date = ""
                    purchaser = ""
                    
                    for span in info_span:
                        text = span.get_text(strip=True)
                        if text.startswith("发布时间："):
                            publish_date = text.replace("发布时间：", "").split(" ")[0]
                        elif text.startswith("采购人："):
                            purchaser = text.replace("采购人：", "")

                    # 提取公告类型（如：公开招标、中标公告）
                    strong_tag = item.find('strong')
                    status = strong_tag.get_text(strip=True) if strong_tag else "未知类型"

                    data_list.append({
                        "发布时间": publish_date,
                        "项目名称": title,
                        "采购单位": purchaser,
                        "状态": status,
                        "链接": link
                    })
    except Exception as e:
        st.error(f"抓取数据时发生错误，可能是网络波动或遭遇反爬拦截：{e}")

    # 如果抓取失败或没有数据，返回一个空的标准化表格以防网页崩溃
    if not data_list:
        return pd.DataFrame(columns=["发布时间", "项目名称", "采购单位", "状态", "链接"])
        
    return pd.DataFrame(data_list)

# ================= 网页 UI 搭建 =================

st.title("🔬 疾控/医院核酸检测产品招标监控台")
st.markdown("数据源：中国政府采购网 (ccgp.gov.cn) | 每小时自动刷新")

with st.sidebar:
    st.header("🔍 监控条件设置")
    search_keyword = st.text_input("关键词", value="核酸检测 提取仪")
    bidding_type = st.selectbox("公告类型过滤", ["全部", "公开招标", "中标公告", "竞争性磋商", "询价公告"])
    st.markdown("---")
    st.write(f"上次刷新时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    if st.button("🔄 立即强制刷新"):
        st.cache_data.clear()

with st.spinner("正在从中国政府采购网抓取最新数据，请稍候..."):
    df = fetch_bidding_data(search_keyword)

if not df.empty:
    if bidding_type != "全部":
        df = df[df["状态"].str.contains(bidding_type, na=False)]

    col1, col2 = st.columns(2)
    today_str = datetime.now().strftime('%Y.%m.%d')
    col1.metric("今日新增招标", f"{len(df[df['发布时间'] == today_str])} 项")
    col2.metric("当前检索结果总数", f"{len(df)} 项")

    st.markdown("### 📄 真实招标/中标明细")
    st.dataframe(
        df,
        column_config={
            "链接": st.column_config.LinkColumn("查看详情", display_text="点击前往原网公告")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("当前关键词未检索到近期招标信息，或网络请求被对方服务器拦截。")
