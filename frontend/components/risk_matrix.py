import streamlit as st


def render_risk_matrix():
    """
    Renders the risk matrix as an HTML table with colored cells.
    The matrix uses five risk levels with these thresholds:
      - Very Low Risk (Blue): normalized risk < 0.10
      - Low Risk (Green): 0.10 ≤ normalized risk < 0.30
      - Medium Risk (Yellow): 0.30 ≤ normalized risk < 0.55
      - High Risk (Orange): 0.55 ≤ normalized risk < 0.75
      - Extreme Risk (Dark Red): normalized risk ≥ 0.75
    """

    row_labels = ["Rare (0.001)", "Unlikely (0.01)", "Possible (0.1)", "Likely (0.5)", "Almost Certain (0.9)"]
    col_labels = [
        "Insignificant<br>(0.001)",
        "Minor<br>(0.01)",
        "Moderate<br>(0.1)",
        "Major<br>(0.5)",
        "Catastrophic<br>(0.9)"
    ]

    # Precomputed normalized risk values (rounded to 2 decimals)
    matrix = [
        [0.00, 0.01, 0.06, 0.28, 0.50],
        [0.01, 0.01, 0.06, 0.28, 0.51],
        [0.06, 0.06, 0.11, 0.33, 0.56],
        [0.28, 0.28, 0.33, 0.56, 0.78],
        [0.50, 0.51, 0.56, 0.78, 1.00]
    ]

    def get_color(value):
        if value < 0.10:
            return "#3498DB"  # Very Low Risk: Blue
        elif value < 0.30:
            return "#2ECC71"  # Low Risk: Green
        elif value < 0.55:
            return "#F1C40F"  # Medium Risk: Yellow
        elif value < 0.75:
            return "#E67E22"  # High Risk: Orange
        else:
            return "#C0392B"  # Extreme Risk: Dark Red

    # Build the HTML table.
    html = '<table style="border-collapse: collapse; width: 100%;">'

    html += "<colgroup>"
    html += '<col style="width: 25%;">'
    for _ in range(5):
        html += '<col style="width: 15%;">'
    html += "</colgroup>"

    html += "<tr><th style='border: 1px solid #ddd; padding: 8px;'></th>"
    for col in col_labels:
        html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{col}</th>"
    html += "</tr>"

    for i, row_label in enumerate(row_labels):
        html += f"<tr><th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{row_label}</th>"
        for j, value in enumerate(matrix[i]):
            color = get_color(value)
            html += (
                f"<td style='border: 1px solid #ddd; padding: 8px; text-align: center; "
                f"background-color: {color}; color: white;'>"
                f"{value:.2f}</td>"
            )
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)
