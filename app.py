import streamlit as st
import pandas as pd
import random
import sqlite3
import requests

st.set_page_config(page_title="极简大乐透", layout="wide")
st.title("🎯 大乐透极简分析台")

# ================= 1. 数据库与更新模块 =================
def init_db():
    conn = sqlite3.connect('simple.db')
    conn.execute("CREATE TABLE IF NOT EXISTS draws (period TEXT PRIMARY KEY, f1 INT, f2 INT, f3 INT, f4 INT, f5 INT, b1 INT, b2 INT)")
    conn.commit()
    conn.close()

def sync_from_third_party():
    """去第三方公开接口抓取最新数据（成功率极高，防报错）"""
    # 使用第三方开源数据接口
    url = "https://api.pearktrue.cn/api/lottery/?type=dlt"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200 and "data" in data:
                conn = sqlite3.connect('simple.db')
                count = 0
                for item in data["data"]:
                    period = str(item["expect"])
                    # 第三方接口的号码格式通常是 "01,04,11,12,18,06,11"
                    nums = [int(x) for x in item["openCode"].split(",")]
                    cur = conn.execute("INSERT OR IGNORE INTO draws VALUES (?,?,?,?,?,?,?,?)",
                        (period, nums[0], nums[1], nums[2], nums[3], nums[4], nums[5], nums[6]))
                    count += cur.rowcount
                conn.commit()
                conn.close()
                return True, f"成功从第三方同步 {count} 期最新数据！"
    except Exception as e:
        return False, "第三方接口连接失败，请手动更新。"
    return False, "接口数据解析失败。"

# 初始化
init_db()

# 🔥 侧边栏：更新控制中心
st.sidebar.header("📡 数据更新中心")
if st.sidebar.button("🔄 一键抓取最新数据", type="primary"):
    with st.sidebar.spinner("正在连接第三方数据源..."):
        success, msg = sync_from_third_party()
        if success:
            st.sidebar.success(msg)
            st.rerun()
        else:
            st.sidebar.error(msg)

st.sidebar.divider()
st.sidebar.subheader("✍️ 手动强制更新")
with st.sidebar.form("manual_update"):
    st.write("如果一键抓取失败，请直接在此填入最新开奖结果：")
    p = st.text_input("期号（如 26124）")
    f_str = st.text_input("前区（空格隔开，如 03 06 10 14 21）")
    b_str = st.text_input("后区（空格隔开，如 04 09）")
    submitted = st.form_submit_button("确认录入")
    
    if submitted and p and f_str and b_str:
        try:
            f_nums = [int(x) for x in f_str.split()]
            b_nums = [int(x) for x in b_str.split()]
            if len(f_nums) == 5 and len(b_nums) == 2:
                conn = sqlite3.connect('simple.db')
                conn.execute("INSERT OR REPLACE INTO draws VALUES (?,?,?,?,?,?,?,?)",
                             (p.strip(), f_nums[0], f_nums[1], f_nums[2], f_nums[3], f_nums[4], b_nums[0], b_nums[1]))
                conn.commit()
                conn.close()
                st.sidebar.success(f"✅ {p}期 录入成功！")
                st.rerun()
            else:
                st.sidebar.error("格式错误，前区5个号，后区2个号")
        except:
            st.sidebar.error("请输入纯数字和空格")

# 读取最新
conn = sqlite3.connect('simple.db')
history = conn.execute("SELECT * FROM draws ORDER BY period DESC").fetchall()
if len(history) == 0:
    # 初始兜底
    conn.execute("INSERT INTO draws VALUES ('26123', 13, 18, 19, 20, 28, 9, 11)")
    conn.commit()
    history = conn.execute("SELECT * FROM draws ORDER BY period DESC").fetchall()
conn.close()
latest = history[0]


# ================= 2. 页面展示 =================
tab1, tab2, tab3 = st.tabs(["📅 历史记录", "🎲 随机生成一注", "🔄 反推与对比"])

with tab1:
    st.subheader("历史开奖记录")
    for row in history:
        front = sorted([row[1], row[2], row[3], row[4], row[5]])
        back = sorted([row[6], row[7]])
        st.info(f"**{row[0]}期** | 前区：{front} | 后区：{back}")

with tab2:
    st.subheader("随机生成一注")
    st.write("在数学概率与上期重号之间寻找平衡。")
    
    if st.button("🎲 启动摇奖", type="primary"):
        front = set(random.sample(range(1, 36), 4)) 
        front.add(random.choice(latest[1:6]))      
        front = sorted(list(front))
        back = sorted(random.sample(range(1, 13), 2))
        
        st.success(f"### 推荐号码：前区 {front} | 后区 {back}")
        st.session_state['gen_front'] = front
        st.session_state['gen_back'] = back

with tab3:
    st.subheader("反推分析（基于最新一期）")
    st.write(f"**最新一期（{latest[0]}）开奖：** 前区 {sorted(latest[1:6])} | 后区 {sorted(latest[6:9])}")
    
    if 'gen_front' not in st.session_state:
        st.warning("请先在上一个页面点『启动摇奖』生成一注，才能对比反推！")
    else:
        gen_f = st.session_state['gen_front']
        gen_b = st.session_state['gen_back']
        act_f = sorted(latest[1:6])
        
        st.write(f"**你的推荐号码：** 前区 {gen_f} | 后区 {gen_b}")
        st.markdown("---")
        st.markdown("### 🔍 深度对比与反推")
        
        sum_gen = sum(gen_f)
        sum_act = sum(act_f)
        odd_gen = sum(1 for n in gen_f if n % 2 != 0)
        odd_act = sum(1 for n in act_f if n % 2 != 0)
        
        st.write(f"**1. 和值对比**：上一期前区和值为 **{sum_act}**，你的推荐和值为 **{sum_gen}**。")
        st.write(f"**2. 奇偶对比**：上一期奇数有 **{odd_act}** 个，你的推荐奇数有 **{odd_gen}** 个。")
        
        st.write("**3. 逐位推演**：")
        for i in range(5):
            diff = gen_f[i] - act_f[i]
            st.write(f"- 第 {i+1} 位：上期开 `{act_f[i]}`，推演号 `{gen_f[i]}`，发生偏移 `{diff:+d}`。")
            
        if abs(sum_gen - sum_act) < 20:
            st.success("✅ **结论**：你的号码和值完美落在上一期的引力区间内。")
        else:
            st.error("⚠️ **结论**：和值偏离较大，属于极端的冷门爆发组合。")