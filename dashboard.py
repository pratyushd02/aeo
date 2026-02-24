# app.py
import streamlit as st
import pandas as pd
import re
import requests
import tempfile
import os
import time
import openpyxl
from openpyxl import Workbook
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from streamlit_pdf_viewer import pdf_viewer

# -----------------------
# CONFIG
# -----------------------
API_URL = "https://chat.binghamton.edu/api/chat/completions"
API_KEY = "sk-dddeec5e68bc4ae6aee77679a7d88c35" 
st.set_page_config(page_title="AEO Dashboard", layout="wide")

# -----------------------
# TABS
# -----------------------
tab1, tab2 = st.tabs(["AI Visibility & Sources", "Summary & Sources Report"])

# -----------------------
# TAB 1: AI Visibility & Sources Generator
# -----------------------
with tab1:
    st.header("AI Visibility & Sources Generator")

    st.subheader("Models and Prompts")
    model_list_str = st.text_area(
        "LLM Models (comma-separated)", value="gpt-oss:120b"
    )
    models = [m.strip() for m in model_list_str.split(",") if m.strip()]

    prompts_str = st.text_area(
        "Prompts (one per line)",
        value=(
            "Best graduate schools in New York for computer science\n"
            "Top MS programs in engineering in the northeast USA\n"
            "Best public universities for master's degrees in New York\n"
            "Best ROI graduate programs in the USA"
        )
    )
    prompts = [p.strip() for p in prompts_str.split("\n") if p.strip()]

    output_file_name = "ollama_ai_visibility_results_dashboard.xlsx"

    # -------- Functions --------
    def query_model(model, prompt):
        prompt_with_instruction = (
            f"{prompt}\n\nPlease provide your answer in detail and include a section titled 'Sources' "
            "listing the main references or links you used."
        )
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt_with_instruction}]}

        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=300)
            response.raise_for_status()
            json_resp = response.json()
            if "choices" in json_resp and json_resp["choices"]:
                return json_resp["choices"][0]["message"]["content"]
            return str(json_resp)
        except Exception as e:
            return f"ERROR: {e}"

    def extract_sources(text):
        urls = re.findall(r'(https?://[^\s)]+)', text)
        if urls:
            return "\n".join(urls)
        match = re.search(r'(Sources|References)[:\-]?\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(2).strip()
        return "N/A"

    def generate_excel(models, prompts):
        if os.path.exists(output_file_name):
            wb = openpyxl.load_workbook(output_file_name)
        else:
            wb = Workbook()
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

        for model in models:
            sheet_name = model[:6]
            if sheet_name in wb.sheetnames:
                del wb[sheet_name]
            ws = wb.create_sheet(title=sheet_name)
            ws.append(["Prompt", "Response", "Sources"])

            for prompt in prompts:
                st.info(f"Querying model {model} for prompt: {prompt}")
                answer = query_model(model, prompt)
                sources = extract_sources(answer)
                ws.append([prompt, answer, sources])
                st.success(f"Completed prompt → waiting 15 seconds...")
                time.sleep(15)

        excel_bytes = BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        return excel_bytes

    # -------- Generate Button --------
    if st.button("Generate Excel"):
        if not models or not prompts:
            st.error("Please provide at least one model and one prompt.")
        else:
            st.info("Generating Excel, this may take several minutes...")
            excel_data = generate_excel(models, prompts)
            st.success("Excel generation complete!")
            st.download_button(
                "📥 Download Excel File",
                data=excel_data,
                file_name=output_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# -----------------------
# TAB 2: Summary & Sources Report
# -----------------------
with tab2:
    st.header("Summary & Sources Report")

    st.subheader("Upload Excel & Generate Reports")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    model_name = st.text_input("LLM Model Name", value="mixtral:8x22b")

    summary_btn = st.button("Generate Summary Report")
    sources_btn = st.button("Generate Sources Report")

    # -------- UTILITY FUNCTIONS --------
    def chunk_list(lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    def safe_ollama_chat(model, prompt):
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except:
            return response.text.strip()
    
    # -----------------------
# SUMMARY REPORT
# -----------------------
    def generate_aeo_report_pdf(file_path, model):
        xls = pd.ExcelFile(file_path)
        all_rows = []

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            for _, row in df.iterrows():
                all_rows.append(f"Prompt: {row['Prompt']}\nResponse: {row['Response']}")

        def chunk_list(lst, chunk_size):
            for i in range(0, len(lst), chunk_size):
                yield lst[i:i + chunk_size]

        chunks = list(chunk_list(all_rows, 100))
        chunk_summaries = []

        for idx, chunk in enumerate(chunks):
            chunk_text = "\n\n".join(chunk)
            chunk_prompt = f"""
    You are analyzing AI-generated responses about graduate program flexibility.
    Summarize ONLY the following dataset chunk into 6-10 factual bullet points:

    {chunk_text}
    """
            summary = safe_ollama_chat(model, chunk_prompt)
            chunk_summaries.append(summary)

        # Final synthesis
        final_prompt = f"""
    You are an expert AEO (AI Engine Optimization) and graduate program analyst.
    You are given summaries of AI model responses about graduate program flexibility.

    Your job is to analyze ONLY this provided data.

    Create a structured executive report with the following sections:

    1. Executive Summary
    - 3-5 concise bullet points capturing the key findings.

    2. University Mention Frequency
    - Identify which universities appear the most.
    - Rank them by number of flexibility-related mentions.
    - Provide a short ranked list.

    3. Top Programs Offering Flexible Work Arrangements
    - Extract programs explicitly described as flexible.
    - Identify the type of flexibility mentioned.

    4. Binghamton University Coverage
    - How often Binghamton appears.
    - What is said about flexibility.
    - Where competitors appear but Binghamton does not.

    5. Competitor Gap Analysis
    - Identify universities frequently mentioned where Binghamton is not.
    - Summarize what competitors emphasize.

    6. Actionable Recommendations for Binghamton University
    - Provide 5-7 data-driven recommendations tied directly to gaps in the dataset.

    Format the output with clear headers and bullet points.

    Here are the chunk summaries:
    {chr(10).join(chunk_summaries)}
    """
        final_report = safe_ollama_chat(model, final_prompt)
        final_report_clean = re.sub(r"\n{3,}", "\n\n", final_report)

        # Build PDF
        output_file = file_path.replace(".xlsx", "_LLM_Report_Final_dashboard.pdf")
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        for line in final_report_clean.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Normal"]))
                story.append(Spacer(1, 10))

        chart_paths = generate_aeo_charts(file_path)
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Visual Analytics</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))

        for chart_path in chart_paths:
            story.append(Image(chart_path, width=500, height=350))
            story.append(Spacer(1, 20))

        doc.build(story)
        return output_file

    # -----------------------
    # SOURCES REPORT
    # -----------------------
    def classify_source(domain):
        d = domain.lower()
        if any(x in d for x in ["facebook", "linkedin", "twitter", "instagram", "youtube", "tiktok", "reddit"]):
            return "Social Media"
        elif ".edu" in d:
            return "University Website"
        elif ".gov" in d or ".ac" in d:
            return "Government/Educational Body"
        elif any(x in d for x in [".com", ".org", ".net", "news", "college", "ranking", "review"]):
            return "News / Articles / Blogs"
        else:
            return "Miscellaneous"

    def extract_all_urls(text):
        if not isinstance(text, str): return []
        text = text.replace(")", " ").replace("]", " ")
        urls = re.findall(r'https?://[A-Za-z0-9\.\-_/~%?#=&]+', text)
        clean_domains = []
        for u in urls:
            u = u.strip().strip(".,);:]")
            m = re.findall(r'https?://(?:www\.)?([^/]+)/?', u)
            clean_domains.append(m[0].lower() if m else u)
        return list(set(clean_domains))

    def generate_sources_report_pdf(file_path, model):
        xls = pd.ExcelFile(file_path)
        all_sources = []

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = [c.lower() for c in df.columns]

            src_col = next((c for c in df.columns if "source" in c), None)
            prompt_col = next((c for c in df.columns if "prompt" in c), None)
            if not src_col or not prompt_col: continue

            for _, row in df.iterrows():
                urls = extract_all_urls(str(row[src_col]))
                for d in urls:
                    all_sources.append({
                        "Model": sheet,
                        "Prompt": row[prompt_col],
                        "Website": d,
                        "Category": classify_source(d)
                    })

        df_sources = pd.DataFrame(all_sources)
        if df_sources.empty: return None

        agg = df_sources.groupby(["Category", "Website"]).size().reset_index(name="Count").sort_values(["Category", "Count"], ascending=[True, False])

        # Pie chart
        category_counts = df_sources["Category"].value_counts()
        plt.figure(figsize=(7, 7))
        plt.pie(category_counts, labels=category_counts.index, autopct="%1.1f%%")
        chart_path = os.path.join(tempfile.gettempdir(), "source_pie_chart.png")
        plt.savefig(chart_path, dpi=300, bbox_inches="tight")
        plt.close()

        # LLM summary
        summary_prompt = f"""
    You are analyzing sources used by multiple AI models for graduate program prompts.

    Models: {', '.join(sorted(df_sources['Model'].unique()))}
    Total sources: {len(df_sources)}
    Category breakdown: {category_counts.to_dict()}
    Top 10 websites: {df_sources['Website'].value_counts().head(10).to_dict()}

    Write a short bullet-point summary describing:
    - General source patterns
    - Any biases or missing source types
    """
        llm_summary = safe_ollama_chat(model, summary_prompt)

        # Build PDF
        out_pdf = file_path.replace(".xlsx", "_Sources_Report_dashboard.pdf")
        doc = SimpleDocTemplate(out_pdf, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("<b>1. Summary</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))
        for line in llm_summary.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Normal"]))
                story.append(Spacer(1, 6))

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>2. Source Type Distribution</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))
        story.append(Image(chart_path, width=400, height=400))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>3. Source Table</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))

        for cat in agg["Category"].unique():
            subset = agg[agg["Category"] == cat]
            story.append(Paragraph(f"<b>{cat}</b>", styles["Heading3"]))
            data = [["Website", "Count"]] + subset[["Website", "Count"]].values.tolist()
            t = Table(data, repeatRows=1, colWidths=[300, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ]))
            story.append(t)
            story.append(Spacer(1, 14))

        doc.build(story)
        return out_pdf


    def generate_aeo_charts(file_path):
        universities = ["Binghamton", "Buffalo", "Stony Brook", "Columbia", "NYU", "Cornell",
                        "Syracuse", "RIT", "SUNY", "CUNY", "RPI", "University at Albany"]
        xls = pd.ExcelFile(file_path)
        all_data = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            for _, row in df.iterrows():
                response = str(row["Response"])
                prompt = row["Prompt"]
                for uni in universities:
                    count = len(re.findall(rf"\b{re.escape(uni)}\b", response, re.IGNORECASE))
                    all_data.append({"Model": sheet, "Prompt": prompt, "University": uni, "Mentions": count})
        df_all = pd.DataFrame(all_data)
        chart_paths = []

        mentions_sum = df_all.groupby("University")["Mentions"].sum().sort_values(ascending=False)
        plt.figure(figsize=(10, 6))
        mentions_sum.plot(kind="bar")
        plt.title("Total Mentions per University (All Models)")
        plt.ylabel("Number of Mentions")
        plt.xlabel("University")
        plt.xticks(rotation=45)
        plt.tight_layout()
        bar_chart_path = os.path.join(tempfile.gettempdir(), "mentions_bar_chart.png")
        plt.savefig(bar_chart_path)
        chart_paths.append(bar_chart_path)
        plt.close()

        pivot_prompt_uni = df_all.groupby(["Prompt", "University"])["Mentions"].sum().unstack().fillna(0)
        plt.figure(figsize=(12, 10))
        sns.heatmap(pivot_prompt_uni, cmap="YlGnBu", linewidths=0.5)
        plt.title("Heatmap: Prompts vs University Mentions")
        plt.xlabel("University")
        plt.ylabel("Prompt")
        plt.tight_layout()
        heatmap_path = os.path.join(tempfile.gettempdir(), "mentions_heatmap.png")
        plt.savefig(heatmap_path)
        chart_paths.append(heatmap_path)
        plt.close()
        return chart_paths

    if uploaded_file:
        temp_path = "uploaded.xlsx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if summary_btn:
            st.subheader("Summary Report")
            st.info("Generating... please wait.")
            pdf_path = generate_aeo_report_pdf(temp_path, model_name)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("📥 Download Summary PDF", data=pdf_bytes,
                               file_name=os.path.basename(pdf_path), mime="application/pdf")
            st.subheader("📄 PDF Preview")
            pdf_viewer(pdf_bytes)

        if sources_btn:
            st.subheader("Sources Report")
            st.info("Generating... please wait.")
            pdf_path = generate_sources_report_pdf(temp_path, model_name)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button("📥 Download Sources PDF", data=pdf_bytes,
                                   file_name=os.path.basename(pdf_path), mime="application/pdf")
                st.subheader("📄 PDF Preview")
                pdf_viewer(pdf_bytes)
            else:
                st.error("No valid sources found in the file.")
    else:
        st.info("Upload an Excel file to begin.")
