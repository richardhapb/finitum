import sys
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
from datetime import datetime

conn_str = os.getenv("CONN_STR")

if not conn_str:
    print("There is no connection string")
    sys.exit(1)

conn = create_engine(conn_str)

# Global data containers
expenses_data = pd.DataFrame()
transfers_data = pd.DataFrame()
combined_data = pd.DataFrame()


def load_financial_data():
    """Load and process financial data"""
    global expenses_data, transfers_data, combined_data

    try:
        # Load expenses
        expenses_df = pd.read_sql("SELECT * FROM expense", conn)
        print(f"Loaded {len(expenses_df)} expenses")

        # Load transfers
        transfers_df = pd.read_sql("SELECT * FROM transference", conn)
        print(f"Loaded {len(transfers_df)} transfers")

        if len(expenses_df) == 0 and len(transfers_df) == 0:
            print("No data found")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Process expenses
        if len(expenses_df) > 0:
            expenses_df["type"] = "Expense"
            expenses_df["counterparty"] = expenses_df["commerce"]
            print(f"Sample expense date: {expenses_df['date'].iloc[0]} (type: {type(expenses_df['date'].iloc[0])})")
            expenses_df["date"] = pd.to_datetime(expenses_df["date"])

        # Process transfers
        if len(transfers_df) > 0:
            transfers_df["type"] = "Transfer"
            transfers_df["counterparty"] = transfers_df["recipient"]
            print(f"Sample transfer date: {transfers_df['date'].iloc[0]} (type: {type(transfers_df['date'].iloc[0])})")
            transfers_df["date"] = pd.to_datetime(transfers_df["date"])

        # Combine datasets
        all_columns = np.array(["amount", "currency", "category", "date", "description", "type", "counterparty"])

        expenses_clean = expenses_df[all_columns] if len(expenses_df) > 0 else pd.DataFrame(columns=all_columns)
        transfers_clean = transfers_df[all_columns] if len(transfers_df) > 0 else pd.DataFrame(columns=all_columns)

        combined_df = pd.concat([expenses_clean, transfers_clean], ignore_index=True)

        if len(combined_df) > 0:
            print(
                f"Combined data sample date: {combined_df['date'].iloc[0]} (tz_info: {combined_df['date'].iloc[0].tzinfo})"
            )

            # Date processing - handle timezone conversion properly
            try:
                # Check if dates are already timezone aware
                if combined_df["date"].dt.tz is None:
                    combined_df["date_local"] = (
                        combined_df["date"].dt.tz_localize("UTC").dt.tz_convert("America/Santiago")
                    )
                else:
                    combined_df["date_local"] = combined_df["date"].dt.tz_convert("America/Santiago")
            except Exception as e:
                print(f"Timezone conversion error: {e}")
                # Fallback to naive datetime
                combined_df["date_local"] = combined_df["date"]
            combined_df["year_month"] = combined_df["date_local"].dt.to_period("M")
            combined_df["week"] = combined_df["date_local"].dt.isocalendar().week
            combined_df["day_name"] = combined_df["date_local"].dt.day_name()
            combined_df["day_of_month"] = combined_df["date_local"].dt.day
            combined_df["hour"] = combined_df["date_local"].dt.hour

            # Financial analysis columns
            combined_df["is_current_month"] = combined_df["year_month"] == pd.Period.now("M")
            combined_df["is_weekend"] = combined_df["date_local"].dt.weekday >= 5

        return expenses_df, transfers_df, combined_df

    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


app = Dash(__name__)

template = "plotly_dark"

app.layout = html.Div(
    style={
        "backgroundColor": "#0a0a0a",
        "color": "#ffffff",
        "padding": "20px",
        "minHeight": "100vh",
        "fontFamily": "Inter, -apple-system, sans-serif",
    },
    children=[
        html.H1(
            "💰 Personal Finance Manager",
            style={
                "textAlign": "center",
                "marginBottom": "40px",
                "color": "#00ff88",
                "fontSize": "2.5rem",
                "fontWeight": "300",
            },
        ),
        # Executive Summary Cards
        html.Div(id="executive-summary", style={"marginBottom": "40px"}),
        # Current Month vs Historical Analysis
        html.Div(
            [
                html.H2("📊 Current Month Performance", style={"color": "#00ff88", "marginBottom": "20px"}),
                html.Div(
                    [
                        html.Div([dcc.Graph(id="current-month-comparison")], style={"width": "50%"}),
                        html.Div([dcc.Graph(id="monthly-trend-analysis")], style={"width": "50%"}),
                    ],
                    style={"display": "flex"},
                ),
            ],
            style={"marginBottom": "40px"},
        ),
        # Category Deep Dive
        html.Div(
            [
                html.H2("🏷️ Category Analysis", style={"color": "#00ff88", "marginBottom": "20px"}),
                html.Div(
                    [
                        html.Div([dcc.Graph(id="category-breakdown")], style={"width": "60%"}),
                        html.Div([dcc.Graph(id="category-trend")], style={"width": "40%"}),
                    ],
                    style={"display": "flex"},
                ),
            ],
            style={"marginBottom": "40px"},
        ),
        # Spending Patterns & Insights
        html.Div(
            [
                html.H2("🕒 Spending Patterns", style={"color": "#00ff88", "marginBottom": "20px"}),
                html.Div(
                    [
                        html.Div([dcc.Graph(id="weekly-pattern")], style={"width": "50%"}),
                        html.Div([dcc.Graph(id="daily-heatmap")], style={"width": "50%"}),
                    ],
                    style={"display": "flex"},
                ),
            ],
            style={"marginBottom": "40px"},
        ),
        # Top Merchants & Budget Tracking
        html.Div([
            html.H2("🏪 Merchant Analysis", style={"color": "#00ff88", "marginBottom": "20px"}),
            html.Div(
                [
                    html.Div([dcc.Graph(id="top-merchants")], style={"width": "50%"}),
                    html.Div([dcc.Graph(id="expense-distribution")], style={"width": "50%"}),
                ],
                style={"display": "flex"},
            ),
        ]),
        # Data refresh
        dcc.Store(id="data-store"),
        dcc.Interval(id="interval-component", interval=10000, n_intervals=0, max_intervals=1),
        html.Div(
            [
                html.Button(
                    "🔄 Refresh Data",
                    id="refresh-btn",
                    style={
                        "backgroundColor": "#00ff88",
                        "color": "#000",
                        "border": "none",
                        "padding": "12px 24px",
                        "borderRadius": "8px",
                        "fontWeight": "bold",
                        "cursor": "pointer",
                        "marginTop": "30px",
                    },
                )
            ],
            style={"textAlign": "center"},
        ),
    ],
)


@callback(Output("data-store", "data"), [Input("interval-component", "n_intervals"), Input("refresh-btn", "n_clicks")])
def refresh_data(n_intervals, n_clicks):
    global expenses_data, transfers_data, combined_data
    expenses_data, transfers_data, combined_data = load_financial_data()
    return {"refresh": True, "timestamp": datetime.now().isoformat()}


@callback(Output("executive-summary", "children"), Input("data-store", "data"))
def update_executive_summary(data):
    if len(combined_data) == 0:
        return html.Div("No financial data available", style={"color": "#ff4444", "textAlign": "center"})

    # Calculate key metrics
    current_month_data = combined_data[combined_data["is_current_month"]]
    previous_months = combined_data[~combined_data["is_current_month"]]

    current_month_total = current_month_data["amount"].sum()
    avg_previous_month = previous_months.groupby("year_month")["amount"].sum().mean() if len(previous_months) > 0 else 0

    total_spent = combined_data["amount"].sum()
    transaction_count = len(combined_data)
    avg_transaction = combined_data["amount"].mean()

    # Month-over-month change
    mom_change = (
        ((current_month_total - avg_previous_month) / avg_previous_month * 100) if avg_previous_month > 0 else 0
    )
    mom_color = "#ff4444" if mom_change > 10 else "#00ff88" if mom_change < -5 else "#ffaa00"

    # Top category this month
    if len(current_month_data) > 0:
        top_category = current_month_data.groupby("category")["amount"].sum().idxmax()
        top_category_amount = current_month_data.groupby("category")["amount"].sum().max()
    else:
        top_category = "N/A"
        top_category_amount = 0

    cards = [
        {
            "title": "This Month",
            "value": f"${current_month_total:,.0f}",
            "subtitle": f"{mom_change:+.1f}% vs avg",
            "color": mom_color,
        },
        {
            "title": "Avg Previous Months",
            "value": f"${avg_previous_month:,.0f}",
            "subtitle": "Monthly average",
            "color": "#888888",
        },
        {
            "title": "Total Spent",
            "value": f"${total_spent:,.0f}",
            "subtitle": f"{transaction_count} transactions",
            "color": "#00aaff",
        },
        {
            "title": "Avg Transaction",
            "value": f"${avg_transaction:,.0f}",
            "subtitle": "Per transaction",
            "color": "#aa88ff",
        },
        {
            "title": "Top Category",
            "value": top_category,
            "subtitle": f"${top_category_amount:,.0f}",
            "color": "#ff8800",
        },
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.H3(card["value"], style={"color": card["color"], "margin": "0", "fontSize": "1.8rem"}),
                    html.P(card["title"], style={"color": "#ffffff", "margin": "5px 0", "fontWeight": "bold"}),
                    html.P(card["subtitle"], style={"color": "#cccccc", "margin": "0", "fontSize": "0.9rem"}),
                ],
                style={
                    "backgroundColor": "#1a1a1a",
                    "padding": "20px",
                    "margin": "5px",
                    "borderRadius": "12px",
                    "textAlign": "center",
                    "border": f"1px solid {card['color']}",
                    "flex": "1",
                },
            )
            for card in cards
        ],
        style={"display": "flex", "gap": "10px"},
    )


@callback(Output("current-month-comparison", "figure"), Input("data-store", "data"))
def update_current_month_comparison(data):
    if len(combined_data) == 0:
        return go.Figure()

    # Compare current month to previous months
    monthly_totals = combined_data.groupby("year_month")["amount"].sum().reset_index()
    monthly_totals["month_str"] = monthly_totals["year_month"].astype(str)
    monthly_totals["is_current"] = monthly_totals["year_month"] == pd.Period.now("M")

    colors = ["#00ff88" if is_current else "#333333" for is_current in monthly_totals["is_current"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=monthly_totals["month_str"],
                y=monthly_totals["amount"],
                marker_color=colors,
                text=[f"${x:,.0f}" for x in monthly_totals["amount"]],
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Current Month vs Historical",
        xaxis_title="Month",
        yaxis_title="Total Spent ($)",
        template=template,
        showlegend=False,
    )

    return fig


@callback(Output("monthly-trend-analysis", "figure"), Input("data-store", "data"))
def update_monthly_trend(data):
    if len(combined_data) == 0:
        return go.Figure()

    monthly_data = combined_data.groupby(["year_month", "type"])["amount"].sum().reset_index()
    monthly_data["month_str"] = monthly_data["year_month"].astype(str)

    fig = px.line(
        monthly_data,
        x="month_str",
        y="amount",
        color="type",
        template=template,
        color_discrete_map={"Expense": "#ff6666", "Transfer": "#66aaff"},
    )

    fig.update_layout(title="Monthly Spending Trend by Type", xaxis_title="Month", yaxis_title="Amount ($)")

    return fig


@callback(Output("category-breakdown", "figure"), Input("data-store", "data"))
def update_category_breakdown(data):
    if len(combined_data) == 0:
        return go.Figure()

    current_month_data = combined_data[combined_data["is_current_month"]]

    if len(current_month_data) == 0:
        return go.Figure().add_annotation(text="No current month data", showarrow=False)

    category_totals = current_month_data.groupby("category")["amount"].sum().sort_values(ascending=False)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=category_totals.index,
                values=category_totals.values,
                hole=0.4,
                textinfo="label+percent+value",
                texttemplate="%{label}<br>%{percent}<br>$%{value:,.0f}",
                marker=dict(colors=px.colors.qualitative.Set3),
            )
        ]
    )

    fig.update_layout(
        title="Current Month Spending by Category",
        template=template,
        annotations=[dict(text=f"Total<br>${category_totals.sum():,.0f}", x=0.5, y=0.5, font_size=16, showarrow=False)],
    )

    return fig


@callback(Output("category-trend", "figure"), Input("data-store", "data"))
def update_category_trend(data):
    if len(combined_data) == 0:
        return go.Figure()

    # Get top 5 categories by total spending
    top_categories = combined_data.groupby("category")["amount"].sum().nlargest(5).index
    category_monthly = combined_data[combined_data["category"].isin(top_categories)]
    category_monthly = category_monthly.groupby(["year_month", "category"])["amount"].sum().reset_index()
    category_monthly["month_str"] = category_monthly["year_month"].astype(str)

    fig = px.line(category_monthly, x="month_str", y="amount", color="category", template=template)

    fig.update_layout(title="Top Categories Trend", xaxis_title="Month", yaxis_title="Amount ($)")

    return fig


@callback(Output("weekly-pattern", "figure"), Input("data-store", "data"))
def update_weekly_pattern(data):
    if len(combined_data) == 0:
        return go.Figure()

    # Day of week spending pattern
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily_spending = combined_data.groupby("day_name")["amount"].sum().reindex(day_order).fillna(0)

    colors = ["#ff6666" if day in ["Saturday", "Sunday"] else "#66aaff" for day in daily_spending.index]

    fig = go.Figure(
        data=[
            go.Bar(
                x=daily_spending.index,
                y=daily_spending.values,
                marker_color=colors,
                text=[f"${x:,.0f}" for x in daily_spending.values],
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Spending by Day of Week",
        xaxis_title="Day",
        yaxis_title="Total Spent ($)",
        template=template,
        showlegend=False,
    )

    return fig


@callback(Output("daily-heatmap", "figure"), Input("data-store", "data"))
def update_daily_heatmap(data):
    if len(combined_data) == 0:
        return go.Figure()

    # Create day vs hour heatmap
    heatmap_data = combined_data.groupby(["day_name", "hour"])["amount"].sum().reset_index()
    heatmap_pivot = heatmap_data.pivot(index="day_name", columns="hour", values="amount").fillna(0)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_pivot = heatmap_pivot.reindex(day_order)

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale="Viridis",
            hovertemplate="<b>%{y}</b><br>Hour: %{x}<br>Spent: $%{z:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Spending Heatmap (Day vs Hour)", xaxis_title="Hour of Day", yaxis_title="Day of Week", template=template
    )

    return fig


@callback(Output("top-merchants", "figure"), Input("data-store", "data"))
def update_top_merchants(data):
    if len(combined_data) == 0:
        return go.Figure()

    current_month_data = combined_data[combined_data["is_current_month"]]

    if len(current_month_data) == 0:
        return go.Figure().add_annotation(text="No current month data", showarrow=False)

    top_merchants = current_month_data.groupby("counterparty")["amount"].sum().sort_values(ascending=True).tail(10)

    fig = go.Figure(
        data=[
            go.Bar(
                x=top_merchants.values,
                y=top_merchants.index,
                orientation="h",
                marker_color="#00ff88",
                text=[f"${x:,.0f}" for x in top_merchants.values],
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Top 10 Merchants (Current Month)", xaxis_title="Amount Spent ($)", template=template, height=400
    )

    return fig


@callback(Output("expense-distribution", "figure"), Input("data-store", "data"))
def update_expense_distribution(data):
    if len(combined_data) == 0:
        return go.Figure()

    # Transaction size distribution
    amounts = combined_data["amount"]

    fig = go.Figure(data=[go.Histogram(x=amounts, nbinsx=30, marker_color="#66aaff", opacity=0.7)])

    fig.update_layout(
        title="Transaction Size Distribution",
        xaxis_title="Transaction Amount ($)",
        yaxis_title="Frequency",
        template=template,
    )

    # Add median line
    median_amount = amounts.median()
    fig.add_vline(x=median_amount, line_dash="dash", line_color="red", annotation_text=f"Median: ${median_amount:,.0f}")

    return fig


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5050)
