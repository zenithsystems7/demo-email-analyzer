"""
Customer Email Analyzer Dashboard
Streamlit web interface for analyzing customer service email threads
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import sys
import os

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer.thread_analyzer import load_and_analyze, FLAGS

# Page config
st.set_page_config(
    page_title="Customer Email Analyzer",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .critical-flag { color: #ff4b4b; font-weight: bold; }
    .high-flag { color: #ffa500; font-weight: bold; }
    .medium-flag { color: #ffd700; }
    .low-flag { color: #00cc00; }
    .thread-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .customer-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .agent-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and analyze thread data."""
    return load_and_analyze("data/email_threads.json")


def main():
    # Sidebar navigation
    st.sidebar.title("📧 Email Analyzer")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["📊 Overview", "🚨 Urgent Action", "🚩 Flagged Threads", "👥 Agent Performance", "📈 Issue Trends"]
    )

    # Load data
    try:
        data = load_data()
    except FileNotFoundError:
        st.error("Data file not found. Please run `python generate_sample_data.py` first.")
        return

    # Route to pages
    if page == "📊 Overview":
        show_overview(data)
    elif page == "🚨 Urgent Action":
        show_urgent_action(data)
    elif page == "🚩 Flagged Threads":
        show_flagged_threads(data)
    elif page == "👥 Agent Performance":
        show_agent_performance(data)
    elif page == "📈 Issue Trends":
        show_issue_trends(data)


def show_overview(data):
    """Overview dashboard page."""
    st.title("📊 Dashboard Overview")
    st.markdown("### Q1 Customer Service Analysis")

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Threads", data["total_threads"])

    with col2:
        st.metric("🚩 Flagged", data["flagged_count"],
                  delta=f"{(data['flagged_count']/data['total_threads']*100):.0f}%",
                  delta_color="inverse")

    with col3:
        st.metric("🔴 Open (Waiting)", data["open_count"],
                  delta="Needs response" if data["open_count"] > 0 else "All clear",
                  delta_color="inverse" if data["open_count"] > 0 else "normal")

    with col4:
        st.metric("⚠️ Active Threats", data["threat_count"],
                  delta="Critical" if data["threat_count"] > 0 else "None",
                  delta_color="inverse" if data["threat_count"] > 0 else "off")

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sentiment Distribution")

        # Calculate sentiment distribution
        sentiments = []
        for thread in data["threads"]:
            final_sent = thread["analysis"]["sentiment_analysis"]["final_sentiment"]
            if final_sent > 0.2:
                sentiments.append("Positive")
            elif final_sent < -0.2:
                sentiments.append("Negative")
            else:
                sentiments.append("Neutral")

        sent_counts = pd.Series(sentiments).value_counts()
        colors = {"Positive": "#00cc00", "Neutral": "#ffd700", "Negative": "#ff4b4b"}

        fig = px.pie(
            values=sent_counts.values,
            names=sent_counts.index,
            color=sent_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_layout(showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Flags by Type")

        # Count flags by type
        flag_counts = {}
        for thread in data["flagged_threads"]:
            for flag in thread["analysis"]["flags"]:
                flag_type = flag["flag_type"]
                flag_counts[flag_type] = flag_counts.get(flag_type, 0) + 1

        if flag_counts:
            # Sort by count
            sorted_flags = sorted(flag_counts.items(), key=lambda x: -x[1])[:8]
            flag_df = pd.DataFrame(sorted_flags, columns=["Flag", "Count"])

            fig = px.bar(
                flag_df,
                x="Count",
                y="Flag",
                orientation="h",
                color="Count",
                color_continuous_scale=["#ffd700", "#ff4b4b"]
            )
            fig.update_layout(showlegend=False, height=300, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No flags detected")

    st.markdown("---")

    # Bottom row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Issue Categories")
        issue_df = pd.DataFrame(
            list(data["issue_stats"].items()),
            columns=["Category", "Count"]
        ).sort_values("Count", ascending=False).head(5)

        for _, row in issue_df.iterrows():
            st.write(f"**{row['Category'].replace('_', ' ').title()}**: {row['Count']}")

    with col2:
        st.subheader("Products with Most Issues")
        product_totals = [(p, stats.get("total", 0)) for p, stats in data["product_stats"].items()]
        product_totals.sort(key=lambda x: -x[1])

        for product, count in product_totals[:5]:
            st.write(f"**{product}**: {count} issues")


def show_urgent_action(data):
    """Urgent action required page."""
    st.title("🚨 Urgent Action Required")

    # Critical alerts
    st.subheader("🔴 Customers Waiting for Response")

    waiting_threads = [t for t in data["open_threads"]
                       if t.get("last_message_role") == "customer"]

    if waiting_threads:
        # Sort by wait time
        waiting_threads.sort(key=lambda x: -x.get("hours_since_last_response", 0))

        for thread in waiting_threads:
            hours = thread.get("hours_since_last_response", 0)
            urgency = "🔴" if hours > 48 else "🟡" if hours > 24 else "🟢"

            with st.expander(f"{urgency} {thread['thread_id']} - Waiting {hours:.1f} hours"):
                st.write(f"**Customer:** {thread['customer']['email']}")
                st.write(f"**Category:** {thread['category'].replace('_', ' ').title()}")
                st.write(f"**Products:** {', '.join(thread['order']['products'])}")

                if thread.get("customer_double_texted"):
                    st.warning("⚠️ Customer sent multiple messages")

                # Show last message
                last_msg = thread["messages"][-1]
                st.markdown("**Last message:**")
                st.markdown(f"<div class='customer-message'>{last_msg['body']}</div>",
                           unsafe_allow_html=True)
    else:
        st.success("✅ No customers waiting for response!")

    st.markdown("---")

    # Threat alerts
    st.subheader("⚠️ Active Threat Situations")

    if data["threat_threads"]:
        for thread in data["threat_threads"]:
            flags = thread["analysis"]["flags"]
            threat_flags = [f for f in flags if "THREAT" in f["flag_type"]]

            threat_types = [f["flag_type"].replace("_THREAT", "").replace("_", " ").title()
                          for f in threat_flags]

            with st.expander(f"🚨 {thread['thread_id']} - {', '.join(threat_types)}"):
                st.write(f"**Customer:** {thread['customer']['email']}")
                st.write(f"**Risk Level:** {thread['analysis']['risk_level'].upper()}")

                # Show threat keywords
                for msg_analysis in thread["analysis"]["message_analyses"]:
                    if msg_analysis.get("threat_keywords_found"):
                        st.error(f"Keywords detected: {', '.join(msg_analysis['threat_keywords_found'])}")

                # Show conversation
                st.markdown("**Conversation:**")
                for msg in thread["messages"]:
                    css_class = "customer-message" if msg["role"] == "customer" else "agent-message"
                    role_label = "📧 Customer" if msg["role"] == "customer" else f"💬 Agent: {msg.get('agent_name', 'Unknown')}"
                    st.markdown(f"**{role_label}**")
                    st.markdown(f"<div class='{css_class}'>{msg['body']}</div>",
                               unsafe_allow_html=True)
    else:
        st.success("✅ No active threat situations!")

    st.markdown("---")

    # Double-text alerts
    st.subheader("📨 Double-Text Alerts")

    double_text_threads = [t for t in data["threads"] if t.get("customer_double_texted")]

    if double_text_threads:
        for thread in double_text_threads:
            with st.expander(f"📨 {thread['thread_id']} - Customer messaged multiple times"):
                st.write(f"**Customer:** {thread['customer']['email']}")
                st.write(f"**Status:** {thread['status'].upper()}")

                # Count consecutive customer messages
                consecutive = 0
                for msg in thread["messages"]:
                    if msg["role"] == "customer":
                        consecutive += 1
                    else:
                        break

                if consecutive > 1:
                    st.warning(f"Customer sent {consecutive} messages before getting a response")
    else:
        st.success("✅ No double-text situations!")


def show_flagged_threads(data):
    """Flagged threads view."""
    st.title("🚩 Flagged Threads")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        # Get unique flag types
        all_flags = set()
        for thread in data["flagged_threads"]:
            for flag in thread["analysis"]["flags"]:
                all_flags.add(flag["flag_type"])

        selected_flag = st.selectbox("Filter by Flag", ["All"] + sorted(list(all_flags)))

    with col2:
        products = list(data["product_stats"].keys())
        selected_product = st.selectbox("Filter by Product", ["All"] + sorted(products))

    with col3:
        agents = [s["name"] for s in data["agent_stats"].values()]
        selected_agent = st.selectbox("Filter by Agent", ["All"] + sorted(set(agents)))

    st.markdown("---")

    # Filter threads
    filtered = data["flagged_threads"]

    if selected_flag != "All":
        filtered = [t for t in filtered
                   if any(f["flag_type"] == selected_flag for f in t["analysis"]["flags"])]

    if selected_product != "All":
        filtered = [t for t in filtered
                   if selected_product in t.get("order", {}).get("products", [])]

    if selected_agent != "All":
        filtered = [t for t in filtered
                   if t.get("assigned_agent", {}).get("name") == selected_agent]

    st.write(f"Showing {len(filtered)} threads")

    # Display threads
    for thread in filtered:
        analysis = thread["analysis"]
        flags = analysis["flags"]
        trajectory = analysis["sentiment_analysis"]

        # Determine card color based on risk
        risk_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        risk_icon = risk_colors.get(analysis["risk_level"], "⚪")

        # Flag badges
        flag_badges = []
        for flag in flags:
            severity = flag["severity"]
            color_class = {"critical": "critical-flag", "high": "high-flag",
                          "medium": "medium-flag", "low": "low-flag"}.get(severity, "")
            flag_badges.append(f"<span class='{color_class}'>{flag['flag_type']}</span>")

        with st.expander(f"{risk_icon} {thread['thread_id']} | {' '.join(flag_badges)}", expanded=False):
            # Thread info
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Customer:** {thread['customer']['email']}")
                st.write(f"**Category:** {thread['category'].replace('_', ' ').title()}")

            with col2:
                st.write(f"**Products:** {', '.join(thread['order']['products'])}")
                st.write(f"**Status:** {thread['status'].upper()}")

            with col3:
                st.write(f"**Risk Level:** {analysis['risk_level'].upper()}")
                st.write(f"**Response Type:** {thread.get('our_response_type', 'N/A')}")

            # Sentiment trajectory
            st.markdown("**Sentiment Trajectory:**")
            sent_change = trajectory["sentiment_change"]
            direction = "📈" if sent_change > 0 else "📉" if sent_change < 0 else "➡️"
            st.write(f"{direction} {trajectory['initial_sentiment']:.2f} → {trajectory['final_sentiment']:.2f} ({trajectory['trajectory']})")

            # Flags detail
            st.markdown("**Flags:**")
            for flag in flags:
                icon = "🔴" if flag["severity"] == "critical" else "🟠" if flag["severity"] == "high" else "🟡"
                reason = f" - {flag['reason']}" if flag.get('reason') else ""
                st.write(f"{icon} **{flag['flag_type']}**: {flag['description']}{reason}")

            # Conversation
            st.markdown("**Conversation:**")
            for i, msg in enumerate(thread["messages"]):
                msg_analysis = analysis["message_analyses"][i] if i < len(analysis["message_analyses"]) else {}

                if msg["role"] == "customer":
                    sentiment = msg_analysis.get("polarity", 0)
                    sent_icon = "😊" if sentiment > 0.2 else "😠" if sentiment < -0.2 else "😐"
                    st.markdown(f"**📧 Customer** {sent_icon} (sentiment: {sentiment:.2f})")
                    st.markdown(f"<div class='customer-message'>{msg['body']}</div>",
                               unsafe_allow_html=True)

                    # Show threats if any
                    if msg_analysis.get("threat_keywords_found"):
                        st.error(f"⚠️ Threat keywords: {', '.join(msg_analysis['threat_keywords_found'])}")
                else:
                    resp_time = msg.get("response_time_hours", 0)
                    time_warning = " ⚠️" if resp_time and resp_time > 24 else ""
                    st.markdown(f"**💬 {msg.get('agent_name', 'Agent')}** (response: {resp_time:.1f}h{time_warning})")
                    st.markdown(f"<div class='agent-message'>{msg['body']}</div>",
                               unsafe_allow_html=True)


def show_agent_performance(data):
    """Agent performance page."""
    st.title("👥 Agent Performance")

    if not data["agent_stats"]:
        st.info("No agent data available")
        return

    # Convert to dataframe
    agent_df = pd.DataFrame([
        {
            "Agent": stats["name"],
            "Threads": stats["threads_handled"],
            "Avg Response (hrs)": stats["avg_response_time_hours"],
            "Resolution Rate": stats["resolution_rate"],
            "Escalation Rate": stats["escalation_rate"],
            "Avg Sentiment Change": stats["avg_sentiment_improvement"]
        }
        for stats in data["agent_stats"].values()
    ])

    # Sort by threads handled
    agent_df = agent_df.sort_values("Threads", ascending=False)

    # Display table
    st.subheader("Performance Metrics")
    st.dataframe(agent_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Response Time by Agent")
        fig = px.bar(
            agent_df,
            x="Agent",
            y="Avg Response (hrs)",
            color="Avg Response (hrs)",
            color_continuous_scale=["#00cc00", "#ffd700", "#ff4b4b"]
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Sentiment Improvement by Agent")
        fig = px.bar(
            agent_df,
            x="Agent",
            y="Avg Sentiment Change",
            color="Avg Sentiment Change",
            color_continuous_scale=["#ff4b4b", "#ffd700", "#00cc00"]
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Agents needing attention
    st.subheader("🚨 Agents Needing Attention")

    problem_agents = agent_df[
        (agent_df["Escalation Rate"] > 20) |
        (agent_df["Avg Response (hrs)"] > 12) |
        (agent_df["Avg Sentiment Change"] < 0)
    ]

    if not problem_agents.empty:
        for _, agent in problem_agents.iterrows():
            issues = []
            if agent["Escalation Rate"] > 20:
                issues.append(f"High escalation rate ({agent['Escalation Rate']}%)")
            if agent["Avg Response (hrs)"] > 12:
                issues.append(f"Slow responses ({agent['Avg Response (hrs)']}h average)")
            if agent["Avg Sentiment Change"] < 0:
                issues.append(f"Negative sentiment impact ({agent['Avg Sentiment Change']:.2f})")

            st.warning(f"**{agent['Agent']}**: {', '.join(issues)}")
    else:
        st.success("✅ All agents performing within acceptable parameters!")


def show_issue_trends(data):
    """Issue trends page."""
    st.title("📈 Issue Trends")

    # Issue distribution
    st.subheader("Issue Distribution")

    issue_df = pd.DataFrame(
        list(data["issue_stats"].items()),
        columns=["Category", "Count"]
    ).sort_values("Count", ascending=False)

    fig = px.bar(
        issue_df,
        x="Count",
        y="Category",
        orientation="h",
        color="Count",
        color_continuous_scale=["#ffd700", "#ff4b4b"]
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Repeat issues
    st.subheader("🔄 Repeat Issues Detected")

    if data["repeat_issues"]:
        for issue in data["repeat_issues"]:
            with st.expander(f"⚠️ {issue['issue_type'].replace('_', ' ').title()} - {issue['count']} occurrences"):
                st.write("**Affected Customers:**")
                for email in issue["customers"]:
                    st.write(f"  • {email}")
                st.write(f"\n**Thread IDs:** {', '.join(issue['threads'])}")
                st.info("💡 Consider investigating this as a systemic issue")
    else:
        st.success("✅ No repeat issues detected (3+ customers with same complaint)")

    st.markdown("---")

    # Products with issues
    st.subheader("Issues by Product")

    if data["product_stats"]:
        product_data = []
        for product, stats in data["product_stats"].items():
            for issue_type, count in stats.items():
                if issue_type != "total" and count > 0:
                    product_data.append({
                        "Product": product,
                        "Issue": issue_type.replace("_", " ").title(),
                        "Count": count
                    })

        if product_data:
            product_df = pd.DataFrame(product_data)

            fig = px.bar(
                product_df,
                x="Product",
                y="Count",
                color="Issue",
                barmode="stack"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Highlight problematic products
            st.subheader("⚠️ Products Needing Attention")

            product_totals = [(p, stats.get("total", 0)) for p, stats in data["product_stats"].items()]
            product_totals.sort(key=lambda x: -x[1])

            for product, total in product_totals[:3]:
                if total >= 3:
                    stats = data["product_stats"][product]
                    top_issues = sorted(
                        [(k, v) for k, v in stats.items() if k != "total"],
                        key=lambda x: -x[1]
                    )[:2]
                    issues_str = ", ".join([f"{k.replace('_', ' ')}: {v}" for k, v in top_issues])
                    st.warning(f"**{product}**: {total} total issues ({issues_str})")
    else:
        st.info("No product-specific data available")

    st.markdown("---")

    # Insights
    st.subheader("💡 Key Insights")

    insights = []

    # Most common issue
    if data["issue_stats"]:
        top_issue = max(data["issue_stats"].items(), key=lambda x: x[1])
        insights.append(f"Most common issue: **{top_issue[0].replace('_', ' ').title()}** ({top_issue[1]} occurrences)")

    # Repeat issues insight
    if data["repeat_issues"]:
        insights.append(f"**{len(data['repeat_issues'])}** systemic issues detected - same complaint from 3+ customers")

    # Product insight
    if data["product_stats"]:
        worst_product = max(data["product_stats"].items(), key=lambda x: x[1].get("total", 0))
        if worst_product[1].get("total", 0) >= 3:
            insights.append(f"**{worst_product[0]}** has the most complaints - consider quality review")

    # Threat insight
    if data["threat_count"] > 0:
        insights.append(f"**{data['threat_count']}** threads contain chargeback/legal/reputational threats")

    for insight in insights:
        st.markdown(f"• {insight}")


if __name__ == "__main__":
    main()
