import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# 设置网页基本属性，需放在第一行
st.set_page_config(page_title="全国核酸检测产品招标监控台", page_icon="🔬", layout="wide")

# ================= 核心爬虫功能 =================
# st.cache_data(ttl=3600) 表示这个函数的结果会缓存1小时（3600秒）
# 这实现了“自动化监控”：网页每过1小时被访问时，会自动重新抓取最新数据
@st.cache_data(ttl=3600)
def fetch_bidding_data(keyword="核酸检测 试剂 提取仪"):
    """
    爬取公共资源交易网或政府采购网的数据（示例框架）
    注意：实际生产环境中，由于各网站反爬策略不同，需配置 Headers 或使用 Selenium
    """
    # 这里我们构造一个模拟的数据集来展示看板效果
    # 实际应用中，你需要在此处用 requests.get() 访问招标网站并解析 HTML
    mock_data = [
        {"发布时间": datetime.now().strftime("%Y-%m-%d"), "项目名称": "XX省疾病预防控制中心核酸提取仪采购项目", "采购单位": "XX省疾控中心", "预算金额(万元)": 150.0, "状态": "公开招标", "链接": "https://example.com/1"},
        {"发布时间": datetime.now().strftime("%Y-%m-%d"), "项目名称": "XX市第一人民医院核酸检测试剂盒采购", "采购单位": "XX市第一人民医院", "预算金额(万元)": 85.5, "状态": "中标公告", "链接": "https://example.com/2"},
        {"发布时间": "2026-11-09", "项目名称": "XX区妇幼保健院全自动核酸扩增仪招标", "采购单位": "XX区妇幼保健院", "预算金额(万元)": 45.0, "状态": "公开招标", "链接": "https://example.com/3"},
        {"发布时间": "2026-11-08", "项目名称": "XX海关口岸传染病核酸检测物资采购", "采购单位": "XX海关", "预算金额(万元)": 320.0, "状态": "意向公开", "链接": "https://example.com/4"}
    ]
    return pd.DataFrame(mock_data)

# ================= 网页 UI 搭建 =================

st.title("🔬 疾控/医院核酸检测产品招标监控台")
st.markdown("自动监控国内公开招标平台信息，数据每小时自动刷新一次。")

# 侧边栏：搜索与过滤
with st.sidebar:
    st.header("🔍 监控条件设置")
    search_keyword = st.text_input("关键词", value="核酸检测")
    bidding_type = st.selectbox("公告类型", ["全部", "公开招标", "意向公开", "中标公告"])
    st.markdown("---")
    st.write(f"上次刷新时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    if st.button("🔄 立即强制刷新"):
        st.cache_data.clear() # 清除缓存，立刻重新爬取

# 获取数据
with st.spinner("正在全网检索最新招标信息，请稍候..."):
    df = fetch_bidding_data(search_keyword)

# 数据过滤逻辑
if bidding_type != "全部":
    df = df[df["状态"] == bidding_type]

# 顶部数据概览卡片
col1, col2, col3 = st.columns(3)
col1.metric("今日新增招标总数", f"{len(df[df['发布时间'] == datetime.now().strftime('%Y-%m-%d')])} 项")
col2.metric("监控数据总量", f"{len(df)} 项")
col3.metric("涉及总预算估算", f"{df['预算金额(万元)'].sum()} 万元")

st.markdown("### 📄 最新招标/中标明细")

# 使用 Streamlit 的可交互表格展示数据
st.dataframe(
    df,
    column_config={
        "链接": st.column_config.LinkColumn("查看详情", display_text="点击前往原文")
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("注：实际数据需接入中国政府采购网或各省公共资源交易中心 API 或通过定制爬虫获取。")
