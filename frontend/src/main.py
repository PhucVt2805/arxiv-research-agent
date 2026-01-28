import streamlit as st
import httpx
import os
from datetime import date, timedelta


BACKEND_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
st.set_page_config(page_title="Arxiv Research Hub", layout="wide", page_icon="🔬")


ARXIV_CATEGORIES = {
    "Artificial Intelligence": "AI",
    "Hardware Architecture": "AR",
    "Computational Complexity": "CC",
    "Computational Engineering, Finance, and Science": "CE",
    "Computation and Language": "CL",
    "Cryptography and Security": "CR",
    "Computer Vision and Pattern Recognition": "CV",
    "Computers and Society": "CY",
    "Databases": "DB",
    "Distributed, Parallel, and Cluster Computing": "DC",
    "Digital Libraries": "DL",
    "Discrete Mathematics": "DM",
    "Data Structures and Algorithms": "DS",
    "Emerging Technologies": "ET",
    "Graphics": "GR",
    "Computer Science and Game Theory": "GT",
    "Human-Computer Interaction": "HC",
    "Information Retrieval": "IR",
    "Information Theory": "IT",
    "Logic in Computer Science": "LO",
    "Machine Learning": "LG",
    "Multiagent Systems": "MA",
    "Multimedia": "MM",
    "Mathematical Software": "MS",
    "Numerical Analysis": "NA",
    "Neural and Evolutionary Computing": "NE",
    "Networking and Internet Architecture": "NI",
    "Operating Systems": "OS",
    "Performance": "PF",
    "Programming Languages": "PL",
    "Robotics": "RO",
    "Symbolic Computation": "SC",
    "Sound": "SD",
    "Software Engineering": "SE",
    "Social and Information Networks": "SI",
    "Systems and Control": "SY"
}


if "page" not in st.session_state:
    st.session_state.page = "home"
if "papers_data" not in st.session_state:
    st.session_state.papers_data = []
if "selected_paper" not in st.session_state:
    st.session_state.selected_paper = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def call_crawler(topics: list, keyword: str, days: int, start_date: str = None):
    """Gọi Backend để cào dữ liệu"""
    payload = {
        "keyword": keyword,
        "topics": topics,
        "days_back": days
    }
    if start_date:
        payload["start_date"] = start_date

    st.write(f"Debug Payload: {payload}")
    try:
        with st.spinner(f"🚀 Đang quét arXiv cho chủ đề {topics}... (Vui lòng đợi 10-30s)"):
            resp = httpx.post(
                f"{BACKEND_URL}/crawler/trigger",
                json=payload,
                timeout=120.0
            )
            data = resp.json()
            if data['status'] == 'success':
                st.success(data['message'])
                return True
            else:
                st.error(f"Lỗi Backend: {data['message']}")
                return False
    except Exception as e:
        st.error(f"Không kết nối được Backend: {e}")
        return False


def fetch_papers(keyword: str = None, sort_by="published_date", order="desc"):
    """Lấy dữ liệu từ DB để hiển thị"""
    try:
        payload = {
            "sort_by": sort_by,
            "order": order,
            "limit": 100
        }
        if keyword:
            payload["keyword"] = keyword

        resp = httpx.post(
            f"{BACKEND_URL}/papers/search",
            json=payload,
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu: {e}")
        return []


# ==========================================
# TRANG 1: HOME (Landing Page)
# ==========================================
def render_home():
    st.title("🔬 Arxiv Research Assistant")
    st.markdown("### Bạn muốn bắt đầu nghiên cứu như thế nào?")
    tab1, tab2, tab3 = st.tabs(["🔍 Nghiên cứu sâu", "📰 Tin tức mới", "💾 Kho Dữ liệu"])

     # ==================================================
    # TAB 1: RESEARCH MODE
    # ==================================================
    with tab1:
        st.subheader("Tìm kiếm bài báo theo Từ khóa & Mốc thời gian")
        
        col_input, col_date = st.columns([3, 1])
        with col_input:
            query = st.text_input(
                "Nhập từ khóa:", 
                placeholder="Nhập từ khóa bạn quan tâm...",
                key="query"
            )
        with col_date:
             start_date = st.date_input(
                "Tìm kiếm từ:",
                value=date(2026, 1, 1),
                max_value=date.today(),
                format="DD/MM/YYYY"
            )
            
        with st.expander("Bộ lọc nâng cao (Giới hạn phạm vi)"):
            st.caption("Chỉ tìm từ khóa trong các danh mục sau (để tránh kết quả không liên quan):")
            selected_cats = st.multiselect(
                "Giới hạn: ",
                options=list(ARXIV_CATEGORIES.keys()),
                default=["Artificial Intelligence", "Computation and Language"],
                key="cats1"
            )
        
        if st.button("🚀 Tìm kiếm", type="primary", key="search_button"):
            if not query.strip():
                st.warning("Vui lòng nhập từ khóa!")
            else:
                mapped_topics = [ARXIV_CATEGORIES[name] for name in selected_cats]
                date_str = start_date.strftime("%Y-%m-%d")
                
                # Gọi API
                if call_crawler(mapped_topics, query, days=None, start_date=date_str):
                    st.session_state.papers_data = fetch_papers(keyword=query)
                    st.session_state.current_query = query
                    st.session_state.page = "results"
                    st.rerun()
    # ==================================================
    # TAB 2: NEWS MODE
    # ==================================================
    with tab2:
        st.subheader("Cập nhật bài báo mới nhất theo chủ đề:")
        selected_names = st.multiselect(
            "Chọn lĩnh vực:", 
            options=list(ARXIV_CATEGORIES.keys()),
            default=["Artificial Intelligence"],
            key="cats2"
        )
        
        c2_1, c2_2 = st.columns([1, 1])
        with c2_1:
            days_back_opt2 = st.slider("Quét lại bao nhiêu ngày trước?", 1, 30, 3)
        
        if st.button("🚀 Bắt đầu quét (Category)", type="primary"):
            mapped_topics = [ARXIV_CATEGORIES[name] for name in selected_names]
            
            if call_crawler(mapped_topics, '', days=days_back_opt2):
                st.session_state.papers_data = fetch_papers()
                st.session_state.page = "results"
                st.rerun()
    # ==================================================
    # TAB 2: DEFAULT MODE
    # ==================================================
    with tab3:
        st.write("Xem lại các bài báo đã lưu trong Database mà không cần cào mới.")
        if st.button("📂 Mở Kho Dữ liệu"):
            st.session_state.papers_data = fetch_papers()
            st.session_state.page = "results"
            st.rerun()

# ==========================================
# PAGE 2: RESULT
# ==========================================
def render_results():
    col_head_1, col_head_2 = st.columns([4, 1])
    with col_head_1:
        st.title("📑 Danh sách Bài báo")
    with col_head_2:
        if st.button("🏠 Về trang chủ"):
            st.session_state.page = "home"
            st.rerun()

    if "current_keyword" in st.session_state and st.session_state.current_keyword:
        st.info(f"🔍 Đang hiển thị kết quả lọc theo từ khóa: **'{st.session_state.current_keyword}'**")
        if st.button("❌ Xóa lọc (Xem tất cả)"):
            st.session_state.current_keyword = None
            st.session_state.papers_data = fetch_papers() # Fetch all
            st.rerun()
    else:
        st.caption("Đang hiển thị tất cả bài báo mới nhất.")

    with st.expander("⚙️ Bộ lọc & Sắp xếp", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sort_attr = st.selectbox("Sắp xếp theo:", 
                                     ["published_date", "primary_category"], 
                                     format_func=lambda x: "Ngày xuất bản" if x == "published_date" else "Chuyên mục")
        with c2:
            order = st.selectbox("Thứ tự:", ["desc", "asc"], 
                                 format_func=lambda x: "Mới nhất / A-Z" if x == "desc" else "Cũ nhất / Z-A")
        with c3:
            st.write("")
            if st.button("Áp dụng Sắp xếp"):
                st.session_state.papers_data = fetch_papers(sort_attr, order)
                st.rerun()

    papers = st.session_state.papers_data
    
    if not papers:
        st.info("Không có dữ liệu. Hãy quay lại trang chủ để cào thêm.")
        return

    for paper in papers:
        with st.container(border=True):
            c_title, c_action = st.columns([4, 1])
            with c_title:
                st.subheader(f"[{paper['prime_category']}] {paper['title']}")
                st.caption(f"📅 {paper['published_date'][:10]} | ✍️ {', '.join(paper.get('authors', []))[:60]}...")
            with c_action:
                st.write("")
                if st.button("💬 Chat", key=paper['_id']):
                    st.session_state.selected_paper = paper
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": f"Chào bạn! Tôi là trợ lý nghiên cứu về bài báo: **{paper['title']}**. Hãy hỏi tôi bất cứ điều gì!"
                    }]
                    st.session_state.page = "chat"
                    st.rerun()
            
            with st.expander("Xem tóm tắt (Abstract)"):
                st.write(paper['summary'])
                st.markdown(f"[Link gốc Arxiv]({paper['arxiv_url']}) | [Link PDF]({paper['pdf_url']})")

# ==========================================
# PAGE 3: CHAT (Deep Dive)
# ==========================================
def render_chat():
    paper = st.session_state.selected_paper
    if not paper:
        st.session_state.page = "results"
        st.rerun()

    with st.sidebar:
        if st.button("⬅️ Quay lại danh sách"):
            st.session_state.selected_paper = None
            st.session_state.page = "results"
            st.rerun()
        
        st.info(f"Đang thảo luận về:\n\n**{paper['title']}**")
        st.divider()
        st.markdown("**Abstract:**")
        st.caption(paper['summary'])

    st.header("🤖 Research Chat")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Đặt câu hỏi về bài báo này..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                with httpx.stream(
                    "POST", 
                    f"{BACKEND_URL}/chat/stream", 
                    json={
                        "paper_id": paper['_id'],
                        "message": prompt,
                        "history": st.session_state.messages[:-1]
                    },
                    timeout=60.0
                ) as response:
                    for chunk in response.iter_text():
                        if chunk:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")

# ==========================================
# MAIN ROUTER
# ==========================================
def main():
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "results":
        render_results()
    elif st.session_state.page == "chat":
        render_chat()

if __name__ == "__main__":
    main()