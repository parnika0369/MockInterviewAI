import plotly.graph_objects as go
import pandas as pd
import webbrowser
import os

def generate_report(session_result: dict):

    job_roles = session_result.get("job_roles", "Unknown")
    duration = session_result.get("duration_minutes", 0)
    overall_score = session_result.get("overall_session_score", 0)
    questions = session_result.get("session_results", [])

    rows = []
    for q in questions:
        answer_eval = q.get("answer_evaluation", {})
        video = q.get("video_analysis", {})
        rows.append({
            "Question Number": q.get("question_number", 0),
            "Question": q.get("question", ""),
            "Difficulty": q.get("difficulty", ""),
            "Your Answer": q.get("transcript", "") or "You did not answer this question.",
            "Answer Score": answer_eval.get("overall_score", 0),
            "Strengths": answer_eval.get("strengths", []),
            "Weaknesses": answer_eval.get("weaknesses", []),
            "Ideal Answer": answer_eval.get("ideal_answer_summary", ""),
            "Feedback": answer_eval.get("feedback", ""),
            "Body Language": round(video.get("overall_body_language_score", 0), 1),
            "Confidence": round(video.get("confidence_score", 0), 1),
            "Posture": round(video.get("posture_score", 0), 1),
            "Emotion": video.get("dominant_emotion", "neutral"),
        })

    df = pd.DataFrame(rows)

    if overall_score >= 75:
        score_color = "#2E7D32"
        score_label = "Great Performance"
    elif overall_score >= 50:
        score_color = "#F57F17"
        score_label = "Good Effort — Keep Practicing"
    else:
        score_color = "#C62828"
        score_label = "Needs Improvement"

    # ── CHART 1 — Answer Score ──
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=df["Question Number"].apply(lambda x: f"Q{x}"),
        y=df["Answer Score"],
        marker_color="#1565C0",
        text=df["Answer Score"],
        textposition="outside",
        textfont=dict(size=13, color="#1565C0")
    ))
    fig1.update_layout(
        title=dict(text="Answer Score per Question", font=dict(size=15, color="#333333"), x=0.5),
        yaxis=dict(range=[0, 110], title="Score", gridcolor="#EEEEEE", color="#555555"),
        xaxis=dict(color="#555555"),
        height=300,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#333333"),
        showlegend=False,
        margin=dict(t=50, b=30, l=40, r=20)
    )
    answer_chart_html = fig1.to_html(full_html=False, include_plotlyjs=False)

    # ── CHART 2 — Body Language Score ──
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df["Question Number"].apply(lambda x: f"Q{x}"),
        y=df["Body Language"],
        marker_color="#2E7D32",
        text=df["Body Language"],
        textposition="outside",
        textfont=dict(size=13, color="#2E7D32")
    ))
    fig2.update_layout(
        title=dict(text="Body Language Score per Question", font=dict(size=15, color="#333333"), x=0.5),
        yaxis=dict(range=[0, 110], title="Score", gridcolor="#EEEEEE", color="#555555"),
        xaxis=dict(color="#555555"),
        height=300,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#333333"),
        showlegend=False,
        margin=dict(t=50, b=30, l=40, r=20)
    )
    body_chart_html = fig2.to_html(full_html=False, include_plotlyjs=False)

    # ── QUESTION CARDS ──
    question_cards_html = ""
    for _, row in df.iterrows():
        score = row["Answer Score"]

        if score >= 75:
            verdict_color = "#2E7D32"
            verdict_bg = "#E8F5E9"
            verdict_text = "Good Answer"
        elif score >= 40:
            verdict_color = "#F57F17"
            verdict_bg = "#FFF8E1"
            verdict_text = "Partial Answer"
        else:
            verdict_color = "#C62828"
            verdict_bg = "#FFEBEE"
            verdict_text = "Incorrect / Missing Answer"

        difficulty_colors = {
            "Easy": "#2E7D32",
            "Medium": "#F57F17",
            "Hard": "#C62828"
        }
        diff_color = difficulty_colors.get(row["Difficulty"], "#555555")

        strengths_html = ""
        for s in row["Strengths"]:
            strengths_html += f"<li style='color:#2E7D32; margin:4px 0'>{s}</li>"
        if not strengths_html:
            strengths_html = "<li style='color:#999'>None noted</li>"

        weaknesses_html = ""
        for w in row["Weaknesses"]:
            weaknesses_html += f"<li style='color:#C62828; margin:4px 0'>{w}</li>"
        if not weaknesses_html:
            weaknesses_html = "<li style='color:#999'>None noted</li>"

        emotion_colors = {
            "happy": "#2E7D32",
            "neutral": "#1565C0",
            "nervous": "#C62828",
            "surprised": "#F57F17",
            "stressed": "#C62828",
            "confused": "#6A1B9A",
            "looking_away": "#555555"
        }
        emotion_color = emotion_colors.get(row["Emotion"], "#555555")

        question_cards_html += f"""
        <div class="question-card">

            <div class="card-header">
                <span class="q-number">Question {int(row['Question Number'])}</span>
                <span class="difficulty" style="color:{diff_color}; border-color:{diff_color}">
                    {row['Difficulty']}
                </span>
                <span class="verdict" style="color:{verdict_color}; background:{verdict_bg}; border-color:{verdict_color}">
                    {verdict_text}
                </span>
                <span class="score" style="color:{verdict_color}">
                    {score}/100
                </span>
            </div>

            <div class="question-text">
                {row['Question']}
            </div>

            <div class="two-col">
                <div class="col-box" style="border-left: 3px solid #1565C0">
                    <div class="box-title">Your Answer</div>
                    <div class="your-answer">
                        {row['Your Answer']}
                    </div>
                </div>
                <div class="col-box" style="border-left: 3px solid #2E7D32">
                    <div class="box-title" style="color:#2E7D32">What the Ideal Answer Looks Like</div>
                    <div class="ideal-answer">
                        {row['Ideal Answer']}
                    </div>
                </div>
            </div>

            <div class="two-col" style="margin-top:14px">
                <div class="col-box" style="border-left: 3px solid #2E7D32">
                    <div class="box-title">What You Did Well</div>
                    <ul style="margin:8px 0; padding-left:18px">
                        {strengths_html}
                    </ul>
                </div>
                <div class="col-box" style="border-left: 3px solid #C62828">
                    <div class="box-title">What To Improve</div>
                    <ul style="margin:8px 0; padding-left:18px">
                        {weaknesses_html}
                    </ul>
                </div>
            </div>

            <div class="feedback-box">
                <div class="box-title">Detailed Feedback</div>
                <p style="color:#444444; margin:8px 0; line-height:1.7">{row['Feedback']}</p>
            </div>

            <div class="body-row">
                <div class="body-stat">
                    <span class="stat-label">Body Language</span>
                    <span class="stat-value" style="color:#2E7D32">{row['Body Language']}/100</span>
                </div>
                <div class="body-stat">
                    <span class="stat-label">Confidence</span>
                    <span class="stat-value" style="color:#1565C0">{row['Confidence']}/100</span>
                </div>
                <div class="body-stat">
                    <span class="stat-label">Posture</span>
                    <span class="stat-value" style="color:#6A1B9A">{row['Posture']}/100</span>
                </div>
                <div class="body-stat">
                    <span class="stat-label">Emotion</span>
                    <span class="stat-value" style="color:{emotion_color}">{row['Emotion'].capitalize()}</span>
                </div>
            </div>

        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MockInterviewAI Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                background-color: #F5F5F5;
                font-family: 'Arial', sans-serif;
                padding: 30px;
                color: #222222;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 24px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            }}
            .header h1 {{
                font-size: 28px;
                color: #111111;
                margin-bottom: 8px;
            }}
            .header p {{
                font-size: 15px;
                color: #666666;
            }}
            .overall-score {{
                font-size: 42px;
                font-weight: bold;
                color: {score_color};
                margin: 10px 0 4px 0;
            }}
            .score-label {{
                font-size: 15px;
                color: {score_color};
                font-weight: bold;
            }}
            .charts-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 28px;
            }}
            .chart-box {{
                background: white;
                border-radius: 12px;
                padding: 16px;
                flex: 1;
                box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            }}
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                color: #111111;
                margin: 28px 0 16px 0;
            }}
            .question-card {{
                background: white;
                border-radius: 12px;
                padding: 22px;
                margin-bottom: 22px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.08);
                border-top: 3px solid #DDDDDD;
            }}
            .card-header {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 14px;
                flex-wrap: wrap;
            }}
            .q-number {{
                font-size: 18px;
                font-weight: bold;
                color: #111111;
            }}
            .difficulty {{
                font-size: 12px;
                padding: 3px 10px;
                border: 1px solid;
                border-radius: 20px;
            }}
            .verdict {{
                font-size: 13px;
                padding: 4px 12px;
                border: 1px solid;
                border-radius: 20px;
                font-weight: bold;
            }}
            .score {{
                font-size: 20px;
                font-weight: bold;
                margin-left: auto;
            }}
            .question-text {{
                font-size: 15px;
                color: #333333;
                margin-bottom: 16px;
                padding: 12px 16px;
                background: #F9F9F9;
                border-radius: 8px;
                line-height: 1.6;
                border-left: 3px solid #CCCCCC;
            }}
            .two-col {{
                display: flex;
                gap: 14px;
            }}
            .col-box {{
                flex: 1;
                background: #FAFAFA;
                border-radius: 8px;
                padding: 14px;
            }}
            .box-title {{
                font-size: 11px;
                font-weight: bold;
                color: #888888;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}
            .your-answer {{
                color: #444444;
                font-size: 14px;
                line-height: 1.6;
                font-style: italic;
            }}
            .ideal-answer {{
                color: #2E7D32;
                font-size: 14px;
                line-height: 1.6;
            }}
            .feedback-box {{
                background: #FAFAFA;
                border-radius: 8px;
                padding: 14px;
                margin-top: 14px;
                border-left: 3px solid #F57F17;
            }}
            .body-row {{
                display: flex;
                gap: 12px;
                margin-top: 14px;
                flex-wrap: wrap;
            }}
            .body-stat {{
                flex: 1;
                background: #F5F5F5;
                border-radius: 8px;
                padding: 12px 14px;
                display: flex;
                flex-direction: column;
                gap: 4px;
                min-width: 100px;
            }}
            .stat-label {{
                font-size: 11px;
                color: #888888;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .stat-value {{
                font-size: 18px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>

        <div class="header">
            <h1>MockInterviewAI — Session Report</h1>
            <p>Role: <b>{job_roles}</b> &nbsp;|&nbsp; Duration: <b>{duration} mins</b></p>
            <div class="overall-score">{overall_score}/100</div>
            <div class="score-label">{score_label}</div>
        </div>

        <div class="charts-row">
            <div class="chart-box">{answer_chart_html}</div>
            <div class="chart-box">{body_chart_html}</div>
        </div>

        <div class="section-title">Question-by-Question Breakdown</div>
        {question_cards_html}

    </body>
    </html>
    """

    report_path = os.path.abspath("interview_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nReport saved: {report_path}")
    print("Opening in browser...")
    webbrowser.open(f"file://{report_path}")

    return report_path