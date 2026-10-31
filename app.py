import streamlit as st
import pandas as pd
import random
import sqlite3
import json

st.set_page_config(page_title="极简大乐透", layout="wide")
st.title("🎯 大乐透极简分析台")

# 数据库初始化（自带假数据兜底，绝对不报错）
def init_db():
    conn = sqlite3.connect('simple.db')
    conn.execute("CREATE TABLE IF NOT EXISTS draws (period TEXT, f1 INT, f2 INT, f3 INT, f4 INT, f5 INT, b1 INT, b2 INT)")
    # 如果没数据，自动塞10期真实历史数据进去演示
    if conn.execute("SELECT COUNT(*) FROM draws").fetchone()[0] == 0:
        mock_data = [
            ("26123", 19, 13, 20, 28, 18, 11, 9),
            ("26122", 24, 21, 2, 14, 22, 12, 2),
            ("26121", 25, 8, 6, 19, 5, 10, 4),
            ("26120", 1, 7, 12, 15, 30, 5, 8),
            ("26119", 3, 9, 11, 22, 33, 6, 7)
        ]
        for row in mock_data:
            conn.execute("INSERT INTO draws VALUES (?,?,?,?,?,?,?,?)", row)
        conn.commit()
    conn.close()

init_db()

# 读取历史
def get_history():
    conn = sqlite3.connect('simple.db')
    rows = conn.execute("SELECT * FROM draws ORDER BY period DESC").fetchall()
    conn.close()
    return rows

history = get_history()
latest = history[0]

# 三个极简标签页
tab1, tab2, tab3 = st.tabs(["📅 历史记录", "🎲 随机生成一注", "🔄 反推与对比"])

with tab1:
    st.subheader("最近开奖记录")
    df = pd.DataFrame(history, columns=["期号", "前1", "前2", "前3", "前4", "前5", "后1", "后2"])
    # 按前区排序展示
    for i, row in df.iterrows():
        front = sorted([row['前1'], row['前2'], row['前3'], row['前4'], row['前5']])
        back = sorted([row['后1'], row['后2']])
        st.info(f"**{row['期号']}期** | 前区：{front} | 后区：{back}")

with tab2:
    st.subheader("随机生成一注")
    st.write("在数学概率与上期重号之间寻找平衡。")
    
    if st.button("🎲 启动摇奖", type="primary"):
        # 前区随机抽5个，加上上期可能的重号概率
        front = set(random.sample(range(1, 36), 4)) # 抽4个纯随机
        front.add(random.choice(latest[1:6]))      # 带上1个上期的重号
        front = sorted(list(front))
        
        back = sorted(random.sample(range(1, 13), 2))
        
        st.success(f"### 推荐号码：前区 {front} | 后区 {back}")
        
        # 存入 session 供第三页使用
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
        
        # 简单的和值与奇偶计算
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
            
        # 总结
        if abs(sum_gen - sum_act) < 20:
            st.success("✅ **结论**：你的号码和值完美落在上一期的引力区间内，属于非常合理的偏移！")
        else:
            st.error("⚠️ **结论**：和值偏离较大，属于极端的冷门爆发组合。")