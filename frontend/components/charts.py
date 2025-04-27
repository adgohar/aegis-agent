from datetime import datetime

import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud


def get_risk_level(score: float) -> str:
    if score < 0.10:
        return "Very Low Risk"
    elif score < 0.30:
        return "Low Risk"
    elif score < 0.55:
        return "Medium Risk"
    elif score < 0.75:
        return "High Risk"
    else:
        return "Extreme Risk"


def flatten_events(events: list) -> pd.DataFrame:
    """
    Convert a list of event dictionaries into a flat Pandas DataFrame for visualization.
    Each row represents one event with fields including:
      - title, risk_score, risk_level,
      - likelihood, impact,
      - a concatenated string for risk categories (main and subcategories),
      - a concatenated string for risk subcategories only,
      - a formatted date, source, and description.
    """
    data = []
    for e in events:
        ra = e.get("risk_assessment", {})
        risk_score = ra.get("risk_score")
        # Compute overall risk level using the helper function if risk_score exists.
        risk_level = get_risk_level(risk_score) if risk_score is not None else None
        likelihood = ra.get("likelihood")
        impact = ra.get("impact")

        # Format the timestamp.
        # Expected format is like "2025-01-11T13:00:00Z"; we remove the trailing "Z" and ignore the time part.
        ts = e.get("timestamp", "")
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", ""))
            formatted_date = dt.strftime("%d/%m/%Y")
        except Exception:
            formatted_date = ts  # fallback to the original timestamp

        # Process risk categories:
        # Create a concatenated string of main risk categories (with subcategories in parentheses)
        risk_cats = ""
        if e.get("risk_categories"):
            risk_cats = ", ".join([
                f"{r.get('class_name', '')}" +
                (f" ({', '.join(r.get('families', []))})" if r.get("families") else "")
                for r in e.get("risk_categories", [])
            ])

        # Process subcategories separately: extract all families from each risk.
        risk_subcats = []
        if e.get("risk_categories"):
            for r in e.get("risk_categories", []):
                families = r.get("families")
                if families:
                    risk_subcats.extend(families)
        risk_subcats_str = ", ".join(risk_subcats) if risk_subcats else ""

        data.append({
            "title": e.get("title"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "likelihood": likelihood,
            "impact": impact,
            "risk_categories": risk_cats,
            "risk_subcategories": risk_subcats_str,  # New field for subcategories only.
            "date": formatted_date,
            "source": e.get("source_name", ""),
            "description": e.get("description", "")
        })

    return pd.DataFrame(data)


def create_overall_risk_donut_chart(df: pd.DataFrame, risk_level_colors: dict):
    # Group by overall risk level and count events.
    risk_counts = df['risk_level'].value_counts().reset_index()
    risk_counts.columns = ['risk_level', 'count']
    risk_level_order = ["Very Low Risk", "Low Risk", "Medium Risk", "High Risk", "Extreme Risk"]
    risk_counts['risk_level'] = pd.Categorical(risk_counts['risk_level'],
                                               categories=risk_level_order, ordered=True)
    risk_counts = risk_counts.sort_values('risk_level')
    total_events = int(df.shape[0])

    fig = px.pie(
        risk_counts,
        values='count',
        names='risk_level',
        hole=0.5,
        color='risk_level',
        color_discrete_map=risk_level_colors,
        title="Event Count by Overall Risk Level"
    )
    fig.update_layout(
        annotations=[dict(text=f"{total_events}", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig


def create_broad_risk_donut_chart(df: pd.DataFrame, all_risk_categories: list):
    # Extract broad risk categories from the risk_categories column.
    risk_list = []
    for idx, row in df.iterrows():
        if row['risk_categories']:
            cats = [cat.strip() for cat in row['risk_categories'].split(",")]
            for cat in cats:
                for broad in all_risk_categories:
                    if broad.lower() in cat.lower():
                        risk_list.append(broad)
                        break
    if risk_list:
        df_risk = pd.DataFrame(risk_list, columns=['risk_category'])
        cat_counts = df_risk['risk_category'].value_counts().reset_index()
        cat_counts.columns = ['risk_category', 'count']
        order = all_risk_categories
        cat_counts['risk_category'] = pd.Categorical(cat_counts['risk_category'], categories=order, ordered=True)
        cat_counts = cat_counts.sort_values('risk_category')
    else:
        cat_counts = pd.DataFrame(columns=['risk_category', 'count'])

    fig = px.pie(
        cat_counts,
        values='count',
        names='risk_category',
        hole=0.5,
        color='risk_category',
        color_discrete_map={
            "Financial": "#9B59B6",
            "Geopolitical": "#34495E",
            "Technology": "#16A085",
            "Environmental": "#27AE60",
            "Social": "#D35400",
            "Governance": "#7F8C8D"
        },
        title="Event Count by Broad Risk Category"
    )
    total_cat_events = cat_counts['count'].sum() if not cat_counts.empty else 0
    fig.update_layout(
        annotations=[dict(text=f"{total_cat_events}", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig


def create_risk_subcategory_wordcloud(events: list, df: pd.DataFrame):
    # Build a frequency dictionary from the "risk_subcategories" column in the flattened DataFrame.
    subcat_freq = {}
    for subcats in df["risk_subcategories"]:
        if subcats:
            for subcat in subcats.split(","):
                subcat = subcat.strip()
                if subcat:
                    subcat_freq[subcat] = subcat_freq.get(subcat, 0) + 1
    if subcat_freq:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            colormap="viridis"
        ).generate_from_frequencies(subcat_freq)
        fig_wc, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        return fig_wc
    else:
        return None
