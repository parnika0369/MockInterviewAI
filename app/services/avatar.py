import os
import webbrowser

def show_avatar_with_question(question_text: str, question_number: int, total_questions: int):
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MockInterviewAI — Jenny</title>
    <meta http-equiv="refresh" content="2">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #080810;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', sans-serif;
            color: white;
        }}
        .badge {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 7px 20px;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 36px;
            color: rgba(255,255,255,0.35);
            letter-spacing: 1px;
        }}
        canvas {{
            display: block;
            margin-bottom: 20px;
        }}
        .avatar-name {{
            font-size: 18px;
            font-weight: 600;
            color: rgba(255,255,255,0.88);
            margin-bottom: 4px;
            letter-spacing: 0.3px;
        }}
        .avatar-title {{
            font-size: 11px;
            color: rgba(255,255,255,0.28);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 38px;
        }}
        .question-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 36px 48px;
            max-width: 700px;
            width: 90%;
            position: relative;
            overflow: hidden;
        }}
        .question-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(100,160,255,0.15), transparent);
        }}
        .asking-label {{
            font-size: 11px;
            color: rgba(255,255,255,0.28);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .dots {{ display: flex; gap: 4px; }}
        .dot {{
            width: 5px; height: 5px;
            border-radius: 50%;
            background: rgba(100,160,255,0.5);
            animation: bounce 1.4s ease-in-out infinite;
        }}
        .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes bounce {{
            0%,80%,100% {{ transform: translateY(0); opacity: 0.3; }}
            40% {{ transform: translateY(-5px); opacity: 0.9; }}
        }}
        .question-text {{
            font-size: 20px;
            line-height: 1.8;
            color: rgba(255,255,255,0.85);
            font-weight: 400;
        }}
        .footer-hint {{
            margin-top: 30px;
            font-size: 11px;
            color: rgba(255,255,255,0.18);
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body>

    <div class="badge">Question {question_number} of {total_questions}</div>

    <canvas id="sphere" width="220" height="220"></canvas>

    <div class="avatar-name">Jenny</div>
    <div class="avatar-title">AI Interviewer · MockInterviewAI</div>

    <div class="question-card">
        <div class="asking-label">
            <div class="dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
            Jenny is asking
        </div>
        <div class="question-text">{question_text}</div>
    </div>

    <div class="footer-hint">Switch back to your terminal to record your answer</div>

    <script>
        const canvas = document.getElementById('sphere');
        const ctx = canvas.getContext('2d');
        const cx = 110, cy = 110;
        const baseRadius = 75;
        const rows = 14, cols = 28;
        let time = 0;

        function drawSphere() {{
            ctx.clearRect(0, 0, 220, 220);

            // sphere expands and contracts like breathing/speaking
            const pulse = Math.sin(time * 2.5) * 14;
            const radius = baseRadius + pulse;

            for (let i = 0; i <= rows; i++) {{
                const phi = (Math.PI * i) / rows;
                for (let j = 0; j <= cols; j++) {{
                    const theta = (2 * Math.PI * j) / cols + time * 0.3;

                    const x3 = radius * Math.sin(phi) * Math.cos(theta);
                    const y3 = radius * Math.cos(phi);
                    const z3 = radius * Math.sin(phi) * Math.sin(theta);

                    const rx = cx + x3;
                    const ry = cy - y3;

                    // depth based size and opacity
                    const depth = (z3 + radius) / (2 * radius);
                    const dotSize = depth * 2.8 + 0.4;
                    const alpha = depth * 0.85 + 0.12;

                    const r = Math.floor(40 + depth * 60);
                    const g = Math.floor(100 + depth * 80);
                    const b = Math.floor(220 + depth * 35);

                    ctx.beginPath();
                    ctx.arc(rx, ry, dotSize, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
                    ctx.fill();
                }}
            }}

            time += 0.018;
            requestAnimationFrame(drawSphere);
        }}

        drawSphere();
    </script>

</body>
</html>"""

    fixed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar_display.html")
    with open(fixed_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    if question_number == 1:
        webbrowser.open(f"file:///{fixed_path}")