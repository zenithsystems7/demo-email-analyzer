"""
Thread Analyzer for Customer Email Analyzer
Detects patterns, flags issues, and calculates agent performance
"""

import json
from typing import Dict, List, Optional
from collections import defaultdict
from .sentiment import (
    analyze_message,
    analyze_thread_trajectory,
    calculate_risk_level,
    get_dominant_emotion
)

# Flag definitions
FLAGS = {
    # Response & Thread Status Flags
    "NO_RESPONSE": {"severity": "critical", "color": "red", "description": "Customer waiting - no agent reply"},
    "DOUBLE_TEXT": {"severity": "high", "color": "red", "description": "Customer sent multiple messages waiting"},
    "SLOW_RESPONSE": {"severity": "medium", "color": "yellow", "description": "Agent took >24hrs to reply"},
    "VERY_SLOW_RESPONSE": {"severity": "high", "color": "red", "description": "Agent took >48hrs to reply"},

    # Sentiment & Escalation Flags
    "ESCALATING": {"severity": "high", "color": "red", "description": "Customer sentiment declining after agent response"},
    "UNRESOLVED": {"severity": "medium", "color": "yellow", "description": "Thread closed with negative sentiment"},
    "POLICY_DECLINE_UPSET": {"severity": "medium", "color": "yellow", "description": "Customer frustrated after policy decline"},
    "POLICY_DECLINE_ACCEPTED": {"severity": "low", "color": "green", "description": "Customer accepted policy decline"},

    # Threat Detection Flags
    "CHARGEBACK_THREAT": {"severity": "critical", "color": "red", "description": "Customer mentioned chargeback/dispute"},
    "LEGAL_THREAT": {"severity": "critical", "color": "red", "description": "Customer mentioned legal action"},
    "REGULATORY_THREAT": {"severity": "critical", "color": "red", "description": "Customer mentioned BBB/FTC/Attorney General"},
    "REPUTATIONAL_THREAT": {"severity": "high", "color": "red", "description": "Customer threatened negative reviews"},

    # Agent Performance Flags
    "CANNED_RESPONSE": {"severity": "medium", "color": "yellow", "description": "Agent used generic/unhelpful response"},
    "WRONG_INFO": {"severity": "high", "color": "red", "description": "Agent provided incorrect information"},
    "REPEAT_ISSUE": {"severity": "medium", "color": "yellow", "description": "Same complaint from multiple customers"}
}

# Canned response indicators
CANNED_INDICATORS = [
    "thank you for contacting us",
    "we apologize for any inconvenience",
    "please allow 5-7 business days",
    "your feedback is important",
    "check our faq",
    "we have received your message",
    "will get back to you soon"
]


def analyze_thread(thread: Dict) -> Dict:
    """
    Perform full analysis on a single thread.

    Returns:
        {
            "thread_id": str,
            "flags": list of flag dicts,
            "risk_level": str,
            "sentiment_analysis": dict,
            "message_analyses": list,
            "needs_review": bool,
            "summary": str
        }
    """
    flags = []
    message_analyses = []

    messages = thread.get("messages", [])
    status = thread.get("status", "closed")
    last_role = thread.get("last_message_role", "agent")
    hours_since = thread.get("hours_since_last_response", 0)
    double_texted = thread.get("customer_double_texted", False)
    response_type = thread.get("our_response_type", "granted")

    # Analyze each message
    for msg in messages:
        analysis = analyze_message(msg.get("body", ""))
        analysis["message_id"] = msg.get("message_id")
        analysis["role"] = msg.get("role")
        analysis["response_time_hours"] = msg.get("response_time_hours")
        message_analyses.append(analysis)

        # Check for threats in customer messages
        if msg.get("role") == "customer":
            threats = analysis.get("threats", {})
            if threats.get("chargeback"):
                flags.append(create_flag("CHARGEBACK_THREAT", msg.get("message_id")))
            if threats.get("legal"):
                flags.append(create_flag("LEGAL_THREAT", msg.get("message_id")))
            if threats.get("regulatory"):
                flags.append(create_flag("REGULATORY_THREAT", msg.get("message_id")))
            if threats.get("reputational"):
                flags.append(create_flag("REPUTATIONAL_THREAT", msg.get("message_id")))

        # Check for canned responses from agents
        if msg.get("role") == "agent":
            if is_canned_response(msg.get("body", "")):
                flags.append(create_flag("CANNED_RESPONSE", msg.get("message_id")))

            # Check response time
            resp_time = msg.get("response_time_hours", 0)
            if resp_time and resp_time > 48:
                flags.append(create_flag("VERY_SLOW_RESPONSE", msg.get("message_id"),
                                         f"Response took {resp_time:.1f} hours"))
            elif resp_time and resp_time > 24:
                flags.append(create_flag("SLOW_RESPONSE", msg.get("message_id"),
                                         f"Response took {resp_time:.1f} hours"))

    # Thread-level analysis
    trajectory = analyze_thread_trajectory(messages)

    # Check for no response
    if status == "open" and last_role == "customer":
        if response_type == "no_response":
            flags.append(create_flag("NO_RESPONSE", None,
                                     f"Customer waiting {hours_since:.1f} hours"))

    # Check for double text
    if double_texted:
        flags.append(create_flag("DOUBLE_TEXT", None,
                                 "Customer sent multiple messages before response"))

    # Check for escalation
    if trajectory["trajectory"] == "declining":
        # Only flag if customer got worse AFTER we responded
        agent_responded = any(m.get("role") == "agent" for m in messages)
        if agent_responded:
            flags.append(create_flag("ESCALATING", trajectory.get("turning_point"),
                                     f"Sentiment dropped from {trajectory['initial_sentiment']:.2f} to {trajectory['final_sentiment']:.2f}"))

    # Check policy decline outcomes
    if response_type == "policy_decline":
        if trajectory["final_sentiment"] < -0.3:
            flags.append(create_flag("POLICY_DECLINE_UPSET", None,
                                     "Customer frustrated after policy decline"))
        else:
            flags.append(create_flag("POLICY_DECLINE_ACCEPTED", None,
                                     "Customer accepted policy decline"))

    # Check for unresolved (closed with negative sentiment)
    if status == "closed" and trajectory["final_sentiment"] < -0.3:
        # Don't double-flag with escalating
        if not any(f["flag_type"] == "ESCALATING" for f in flags):
            flags.append(create_flag("UNRESOLVED", None,
                                     f"Closed with negative sentiment: {trajectory['final_sentiment']:.2f}"))

    # Calculate risk level
    risk_level = calculate_risk_level(trajectory, message_analyses)

    # Determine if needs review
    critical_flags = [f for f in flags if FLAGS[f["flag_type"]]["severity"] == "critical"]
    high_flags = [f for f in flags if FLAGS[f["flag_type"]]["severity"] == "high"]
    needs_review = len(critical_flags) > 0 or len(high_flags) >= 2

    # Generate summary
    summary = generate_thread_summary(thread, flags, trajectory, risk_level)

    return {
        "thread_id": thread.get("thread_id"),
        "flags": flags,
        "risk_level": risk_level,
        "sentiment_analysis": trajectory,
        "message_analyses": message_analyses,
        "needs_review": needs_review,
        "summary": summary
    }


def create_flag(flag_type: str, message_id: Optional[str], reason: str = None) -> Dict:
    """Create a flag dict."""
    flag_info = FLAGS.get(flag_type, {})
    return {
        "flag_type": flag_type,
        "severity": flag_info.get("severity", "medium"),
        "color": flag_info.get("color", "yellow"),
        "description": flag_info.get("description", ""),
        "message_id": message_id,
        "reason": reason
    }


def is_canned_response(text: str) -> bool:
    """Check if an agent response appears to be canned/generic."""
    text_lower = text.lower()
    matches = sum(1 for indicator in CANNED_INDICATORS if indicator in text_lower)
    return matches >= 2


def generate_thread_summary(thread: Dict, flags: List[Dict], trajectory: Dict, risk_level: str) -> str:
    """Generate a human-readable summary of the thread."""
    customer = thread.get("customer", {})
    category = thread.get("category", "general")
    products = thread.get("order", {}).get("products", [])

    summary_parts = []

    # Basic info
    product_str = ", ".join(products) if products else "unknown product"
    summary_parts.append(f"Customer contacted about {category.replace('_', ' ')} regarding {product_str}.")

    # Trajectory
    if trajectory["trajectory"] == "improving":
        summary_parts.append("Sentiment improved during conversation.")
    elif trajectory["trajectory"] == "declining":
        summary_parts.append("Sentiment declined during conversation - customer became more upset.")
    elif trajectory["trajectory"] == "volatile":
        summary_parts.append("Sentiment was volatile throughout conversation.")

    # Key flags
    critical_flags = [f for f in flags if f["severity"] == "critical"]
    if critical_flags:
        flag_names = [f["flag_type"].replace("_", " ").title() for f in critical_flags]
        summary_parts.append(f"CRITICAL: {', '.join(flag_names)}")

    # Status
    if thread.get("status") == "open":
        summary_parts.append(f"Thread is OPEN - last message from {thread.get('last_message_role', 'unknown')}.")

    return " ".join(summary_parts)


def analyze_all_threads(threads: List[Dict]) -> Dict:
    """
    Analyze all threads and return aggregated results.

    Returns:
        {
            "total_threads": int,
            "threads": list of analyzed threads,
            "flagged_threads": list of threads with flags,
            "open_threads": list of open threads,
            "threat_threads": list of threads with threats,
            "agent_stats": dict of agent performance,
            "issue_stats": dict of issue categories,
            "product_stats": dict of products with issues,
            "repeat_issues": list of repeat issue clusters
        }
    """
    analyzed = []
    flagged = []
    open_threads = []
    threat_threads = []

    agent_data = defaultdict(lambda: {
        "threads_handled": 0,
        "total_response_time": 0,
        "response_count": 0,
        "escalations": 0,
        "resolutions": 0,
        "sentiment_improvements": []
    })

    issue_counts = defaultdict(int)
    product_issues = defaultdict(lambda: defaultdict(int))
    issue_details = defaultdict(list)  # For repeat issue detection

    for thread in threads:
        analysis = analyze_thread(thread)
        analyzed.append({**thread, "analysis": analysis})

        # Categorize
        if analysis["flags"]:
            flagged.append({**thread, "analysis": analysis})

        if thread.get("status") == "open":
            open_threads.append({**thread, "analysis": analysis})

        threat_flags = [f for f in analysis["flags"]
                        if f["flag_type"] in ["CHARGEBACK_THREAT", "LEGAL_THREAT",
                                               "REGULATORY_THREAT", "REPUTATIONAL_THREAT"]]
        if threat_flags:
            threat_threads.append({**thread, "analysis": analysis})

        # Agent stats
        agent = thread.get("assigned_agent")
        if agent:
            agent_id = agent.get("id")
            agent_data[agent_id]["name"] = agent.get("name")
            agent_data[agent_id]["threads_handled"] += 1

            # Response times
            for msg in thread.get("messages", []):
                if msg.get("role") == "agent" and msg.get("response_time_hours"):
                    agent_data[agent_id]["total_response_time"] += msg["response_time_hours"]
                    agent_data[agent_id]["response_count"] += 1

            # Escalations
            if any(f["flag_type"] == "ESCALATING" for f in analysis["flags"]):
                agent_data[agent_id]["escalations"] += 1

            # Resolutions (closed with positive or neutral sentiment)
            trajectory = analysis["sentiment_analysis"]
            if thread.get("status") == "closed" and trajectory["final_sentiment"] >= -0.2:
                agent_data[agent_id]["resolutions"] += 1

            # Sentiment improvement
            if trajectory["sentiment_change"]:
                agent_data[agent_id]["sentiment_improvements"].append(trajectory["sentiment_change"])

        # Issue stats
        category = thread.get("category", "other")
        issue_counts[category] += 1

        # Product stats
        products = thread.get("order", {}).get("products", [])
        for product in products:
            product_issues[product][category] += 1
            product_issues[product]["total"] += 1

        # For repeat issue detection
        issue_details[category].append({
            "thread_id": thread.get("thread_id"),
            "customer_email": thread.get("customer", {}).get("email"),
            "products": products
        })

    # Calculate agent performance metrics
    agent_stats = {}
    for agent_id, data in agent_data.items():
        avg_response = (data["total_response_time"] / data["response_count"]
                        if data["response_count"] > 0 else 0)
        resolution_rate = (data["resolutions"] / data["threads_handled"]
                          if data["threads_handled"] > 0 else 0)
        escalation_rate = (data["escalations"] / data["threads_handled"]
                          if data["threads_handled"] > 0 else 0)
        avg_sentiment = (sum(data["sentiment_improvements"]) / len(data["sentiment_improvements"])
                        if data["sentiment_improvements"] else 0)

        agent_stats[agent_id] = {
            "name": data["name"],
            "threads_handled": data["threads_handled"],
            "avg_response_time_hours": round(avg_response, 1),
            "resolution_rate": round(resolution_rate * 100, 1),
            "escalation_rate": round(escalation_rate * 100, 1),
            "avg_sentiment_improvement": round(avg_sentiment, 2)
        }

    # Detect repeat issues (3+ customers with same issue)
    repeat_issues = []
    for category, details in issue_details.items():
        if len(details) >= 3:
            repeat_issues.append({
                "issue_type": category,
                "count": len(details),
                "threads": [d["thread_id"] for d in details],
                "customers": [d["customer_email"] for d in details]
            })

    return {
        "total_threads": len(threads),
        "threads": analyzed,
        "flagged_threads": flagged,
        "flagged_count": len(flagged),
        "open_threads": open_threads,
        "open_count": len(open_threads),
        "threat_threads": threat_threads,
        "threat_count": len(threat_threads),
        "agent_stats": agent_stats,
        "issue_stats": dict(issue_counts),
        "product_stats": {k: dict(v) for k, v in product_issues.items()},
        "repeat_issues": repeat_issues
    }


def load_and_analyze(filepath: str = "data/email_threads.json") -> Dict:
    """Load threads from file and analyze them."""
    with open(filepath, "r") as f:
        data = json.load(f)

    threads = data.get("threads", [])
    return analyze_all_threads(threads)


if __name__ == "__main__":
    # Test the analyzer
    print("Loading and analyzing threads...")
    results = load_and_analyze()

    print(f"\nTotal threads: {results['total_threads']}")
    print(f"Flagged threads: {results['flagged_count']}")
    print(f"Open threads: {results['open_count']}")
    print(f"Threat threads: {results['threat_count']}")

    print("\nAgent Performance:")
    for agent_id, stats in results["agent_stats"].items():
        print(f"  {stats['name']}: {stats['threads_handled']} threads, "
              f"{stats['avg_response_time_hours']}h avg response, "
              f"{stats['resolution_rate']}% resolution, "
              f"{stats['escalation_rate']}% escalation")

    print("\nIssue Distribution:")
    for issue, count in sorted(results["issue_stats"].items(), key=lambda x: -x[1]):
        print(f"  {issue}: {count}")

    if results["repeat_issues"]:
        print("\nRepeat Issues Detected:")
        for issue in results["repeat_issues"]:
            print(f"  {issue['issue_type']}: {issue['count']} occurrences")
