"""
Sample Data Generator for Customer Email Analyzer
Generates 30 realistic customer service email threads for a DTC supplements brand
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
PRODUCTS = [
    "ZenVita Pro",
    "NightRest Elite",
    "IronCore Strength",
    "PureGlow Collagen",
    "MindSharp Focus",
    "GutHealth Plus",
    "SlimBoost Max",
    "JointFlex Ultra"
]

AGENTS = [
    {"id": "AGT-001", "name": "Sarah M."},
    {"id": "AGT-002", "name": "James R."},
    {"id": "AGT-003", "name": "Lisa K."},
    {"id": "AGT-004", "name": "Mike T."},
    {"id": "AGT-005", "name": "Emma S."}
]

FIRST_NAMES = ["John", "Sarah", "Mike", "Emily", "David", "Jessica", "Chris", "Amanda",
               "Ryan", "Michelle", "Kevin", "Lauren", "Brian", "Nicole", "Jason",
               "Stephanie", "Mark", "Ashley", "Steven", "Megan", "Daniel", "Rachel",
               "Andrew", "Jennifer", "Joshua", "Samantha", "Tyler", "Brittany", "Brandon", "Kayla"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson"]

# Email templates by scenario
CUSTOMER_EMAILS = {
    "missing_items": [
        "Hi, I just received my order #{order_id} but {product} is missing from the package. I ordered 2 bottles but only received 1. Can you please help?",
        "My order arrived today but it's incomplete. I'm missing {product} from order #{order_id}. This is really frustrating as I've been waiting for this.",
        "Hello, package arrived but {product} wasn't in the box. Order #{order_id}. What happened?",
    ],
    "damaged_product": [
        "The {product} I received is completely crushed and leaking. Order #{order_id}. I can't use this at all. Please send a replacement ASAP.",
        "My {product} arrived damaged - the seal was broken and some pills were crushed. This is unacceptable. Order #{order_id}.",
        "Just opened my package and the {product} bottle is cracked. Everything inside is ruined. Order #{order_id}.",
    ],
    "product_not_working": [
        "I've been taking {product} for 2 months now and I haven't noticed ANY difference. This feels like a waste of money.",
        "Honestly, {product} doesn't work at all. I followed all the instructions and nothing. Very disappointed.",
        "I bought {product} based on your claims but it's done absolutely nothing for me. I want my money back.",
    ],
    "subscription_cancel": [
        "I need to cancel my subscription for {product} immediately. I can't find where to do it on your website.",
        "Please cancel my {product} subscription. I've been trying to do this online for days with no luck.",
        "CANCEL MY SUBSCRIPTION NOW. I don't want any more {product} shipped to me. How do I stop this?",
    ],
    "late_delivery": [
        "My order #{order_id} was supposed to arrive 5 days ago. Where is it? I need my {product}!",
        "It's been over a week and I still haven't received order #{order_id}. The tracking hasn't updated in days.",
        "I ordered {product} two weeks ago and it still hasn't arrived. This is ridiculous. Order #{order_id}.",
    ],
    "billing_dispute": [
        "I was charged twice for order #{order_id}! I see two charges of the same amount on my credit card. Fix this immediately.",
        "Why was I charged ${amount} when the website showed ${lower_amount}? Order #{order_id}. This is not what I agreed to.",
        "I cancelled my subscription but you STILL charged me for {product}. I want a refund right now.",
    ],
    "wrong_product": [
        "I ordered {product} but received {wrong_product} instead. Order #{order_id}. Please send the correct item.",
        "Wrong product in my order #{order_id}. I wanted {product} not {wrong_product}. Very disappointing.",
    ],
    "allergic_reaction": [
        "I had a bad reaction after taking {product}. My skin broke out in hives. What's in this?? I need the full ingredient list.",
        "Your {product} made me sick. I had stomach cramps and nausea all day. Is this normal? I'm worried.",
    ],
    "general_inquiry": [
        "Hi, I have a question about {product}. Can I take it with my other vitamins? Just want to make sure it's safe.",
        "When will {product} be back in stock? I've been checking every day.",
        "What's the difference between {product} and {other_product}? Trying to decide which one to buy.",
    ]
}

AGENT_RESPONSES = {
    "helpful_resolution": [
        "Hi {customer_name},\n\nThank you for reaching out, and I sincerely apologize for this issue with your order.\n\nI've already processed a replacement shipment for the {product} - it will ship today with express delivery at no extra charge. You should receive it within 2-3 business days.\n\nTracking number: {tracking}\n\nIs there anything else I can help you with?\n\nBest,\n{agent_name}",
        "Hello {customer_name},\n\nI'm so sorry to hear about this problem. I've looked into your order #{order_id} and can confirm the issue.\n\nI've issued a full refund for the {product} which should appear in your account within 3-5 business days. I've also added a 20% discount code for your next order: SORRY20\n\nPlease let me know if you need anything else.\n\nWarm regards,\n{agent_name}",
    ],
    "canned_unhelpful": [
        "Hi,\n\nThank you for contacting us. We apologize for any inconvenience.\n\nPlease allow 5-7 business days for a response from our team.\n\nBest,\nCustomer Support",
        "Hello,\n\nWe have received your message and will get back to you soon.\n\nThank you for your patience.\n\nSupport Team",
        "Hi,\n\nThank you for reaching out. Your feedback is important to us.\n\nPlease check our FAQ page for common questions: www.zenithsupplements.com/faq\n\nBest,\n{agent_name}",
    ],
    "policy_decline": [
        "Hi {customer_name},\n\nThank you for contacting us about your {product} order.\n\nUnfortunately, our return policy only covers items within 30 days of purchase. Since your order was placed {days_ago} days ago, we're unable to process a refund at this time.\n\nHowever, I'd like to offer you a 25% discount on your next order as a gesture of goodwill.\n\nBest,\n{agent_name}",
        "Hello {customer_name},\n\nI understand your frustration, but I need to explain our policy.\n\nSubscription cancellations must be made at least 48 hours before the next billing date. Since your next shipment has already been processed, we cannot cancel this month's order.\n\nYour subscription has been cancelled for future months.\n\nRegards,\n{agent_name}",
    ],
    "wrong_info": [
        "Hi {customer_name},\n\nYour order should arrive within 24 hours. Our express shipping guarantees next-day delivery.\n\nBest,\n{agent_name}",  # Wrong - standard shipping doesn't guarantee this
        "Hello {customer_name},\n\nYes, you can take {product} with any other medication - there are no interactions to worry about.\n\nBest,\n{agent_name}",  # Wrong - should recommend consulting doctor
    ]
}

CUSTOMER_FOLLOWUPS = {
    "happy": [
        "Wow, that was fast! Thank you so much {agent_name}. I really appreciate the quick response and the express shipping. This is why I keep ordering from you guys!",
        "Perfect, thank you for handling this so quickly. The refund and discount code are very appreciated. Great customer service!",
        "Thanks {agent_name}! I got the replacement today and everything looks good. You've restored my faith in your company.",
    ],
    "accepted_policy": [
        "I understand. That's disappointing but I appreciate you explaining the policy. I'll use the discount code for my next order. Thanks.",
        "Okay, I wish you could make an exception but I understand you have policies to follow. Thanks for the explanation.",
        "Fine. Not happy about it but I get it. At least the subscription is cancelled now.",
    ],
    "frustrated": [
        "Are you serious?? I've been a customer for 2 years and this is how you treat me? This is UNACCEPTABLE.",
        "This doesn't solve my problem at all. I asked for a refund, not a discount code I'll never use. Let me speak to a manager.",
        "I've been waiting {days} days for a response and THIS is what I get? A generic email? You clearly don't care about your customers.",
    ],
    "escalating_threat": [
        "You know what? I'm done. I'm going to dispute this charge with my credit card company. Good luck dealing with that chargeback.",
        "I'm reporting this to the Better Business Bureau. This is fraud. You'll be hearing from my attorney.",
        "Fine. I'll just leave reviews EVERYWHERE about how terrible your company is. Yelp, Facebook, Google - everyone will know.",
        "I'm contacting the State Attorney General's office about your deceptive business practices. This is illegal.",
        "I have 50,000 followers on Instagram. One post about this experience and you'll lose a lot more than my $49.99.",
    ],
    "double_text": [
        "Hello?? Is anyone there? I sent an email 2 days ago!",
        "Still waiting for a response... this is really frustrating.",
        "HELLO??? I need help with my order!!",
    ]
}


def generate_order_id():
    return f"ORD-{random.randint(10000, 99999)}"


def generate_tracking():
    return f"1Z{random.randint(100000000, 999999999)}"


def generate_customer():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@{'gmail.com' if random.random() > 0.3 else 'yahoo.com'}"
    return {
        "name": f"{first} {last}",
        "first_name": first,
        "email": email,
        "customer_since": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
        "total_orders": random.randint(1, 15),
        "lifetime_value": round(random.uniform(49.99, 850.00), 2)
    }


def generate_timestamp(base_time, hours_offset=0, minutes_offset=0):
    return (base_time + timedelta(hours=hours_offset, minutes=minutes_offset)).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_thread(thread_id: int, scenario: str, thread_type: str) -> Dict:
    """Generate a single email thread based on scenario and type"""

    customer = generate_customer()
    product = random.choice(PRODUCTS)
    order_id = generate_order_id()
    agent = random.choice(AGENTS)

    # Base timestamp - random time in the past 30 days
    base_time = datetime.now() - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

    messages = []
    current_time = base_time

    # Determine issue category
    if scenario in ["happy_resolution", "policy_decline_accepted"]:
        issue_type = random.choice(["missing_items", "damaged_product", "late_delivery", "general_inquiry"])
    elif scenario in ["escalating", "chargeback_threat", "reputational_threat"]:
        issue_type = random.choice(["product_not_working", "billing_dispute", "subscription_cancel"])
    elif scenario == "no_response":
        issue_type = random.choice(["missing_items", "subscription_cancel", "billing_dispute"])
    elif scenario == "double_text":
        issue_type = random.choice(["missing_items", "late_delivery", "subscription_cancel"])
    elif scenario == "wrong_answer":
        issue_type = random.choice(["general_inquiry", "late_delivery"])
    else:
        issue_type = random.choice(list(CUSTOMER_EMAILS.keys()))

    # Initial customer email
    template = random.choice(CUSTOMER_EMAILS.get(issue_type, CUSTOMER_EMAILS["general_inquiry"]))
    wrong_product = random.choice([p for p in PRODUCTS if p != product])
    body = template.format(
        order_id=order_id,
        product=product,
        wrong_product=wrong_product,
        other_product=wrong_product,
        amount=random.randint(50, 150),
        lower_amount=random.randint(30, 49)
    )

    messages.append({
        "message_id": f"MSG-{thread_id:03d}-001",
        "role": "customer",
        "timestamp": generate_timestamp(current_time),
        "subject": get_subject_line(issue_type, product),
        "body": body
    })

    # Determine request type and reasonableness
    request_type = map_issue_to_request(issue_type)
    request_reasonable = random.random() > 0.2  # 80% reasonable

    # Double-text scenario
    double_texted = False
    if scenario == "double_text" or (scenario in ["no_response", "escalating"] and random.random() > 0.5):
        double_texted = True
        current_time += timedelta(hours=random.randint(24, 72))
        messages.append({
            "message_id": f"MSG-{thread_id:03d}-002",
            "role": "customer",
            "timestamp": generate_timestamp(current_time),
            "subject": f"Re: {get_subject_line(issue_type, product)}",
            "body": random.choice(CUSTOMER_FOLLOWUPS["double_text"])
        })

    # Agent response (if not no_response scenario)
    our_response_type = "no_response"
    if scenario != "no_response":
        # Calculate response time
        if scenario in ["happy_resolution", "policy_decline_accepted"]:
            response_hours = random.uniform(0.5, 4)  # Fast response
        elif scenario == "double_text":
            response_hours = random.uniform(48, 96)  # Very slow
        else:
            response_hours = random.uniform(1, 48)

        current_time += timedelta(hours=response_hours)

        # Choose agent response type
        if scenario == "happy_resolution":
            response_template = random.choice(AGENT_RESPONSES["helpful_resolution"])
            our_response_type = "granted"
        elif scenario in ["policy_decline_accepted", "policy_decline_frustrated"]:
            response_template = random.choice(AGENT_RESPONSES["policy_decline"])
            our_response_type = "policy_decline"
        elif scenario == "wrong_answer":
            response_template = random.choice(AGENT_RESPONSES["wrong_info"])
            our_response_type = "granted"  # They tried, but gave wrong info
        else:
            # Mix of responses for other scenarios
            if random.random() > 0.6:
                response_template = random.choice(AGENT_RESPONSES["canned_unhelpful"])
                our_response_type = "partial"
            else:
                response_template = random.choice(AGENT_RESPONSES["helpful_resolution"])
                our_response_type = "granted"

        agent_body = response_template.format(
            customer_name=customer["first_name"],
            product=product,
            order_id=order_id,
            tracking=generate_tracking(),
            agent_name=agent["name"],
            days_ago=random.randint(45, 90)
        )

        msg_num = len(messages) + 1
        messages.append({
            "message_id": f"MSG-{thread_id:03d}-{msg_num:03d}",
            "role": "agent",
            "agent_name": agent["name"],
            "agent_id": agent["id"],
            "timestamp": generate_timestamp(current_time),
            "subject": f"Re: {get_subject_line(issue_type, product)}",
            "body": agent_body,
            "response_time_hours": round(response_hours, 1)
        })

        # Customer follow-up based on scenario
        if scenario != "no_response" and thread_type not in ["A"]:
            current_time += timedelta(hours=random.uniform(0.5, 24))

            if scenario == "happy_resolution":
                followup = random.choice(CUSTOMER_FOLLOWUPS["happy"]).format(agent_name=agent["name"])
            elif scenario == "policy_decline_accepted":
                followup = random.choice(CUSTOMER_FOLLOWUPS["accepted_policy"])
            elif scenario in ["escalating", "policy_decline_frustrated"]:
                followup = random.choice(CUSTOMER_FOLLOWUPS["frustrated"]).format(days=random.randint(2, 7))
            elif scenario in ["chargeback_threat", "reputational_threat"]:
                followup = random.choice(CUSTOMER_FOLLOWUPS["escalating_threat"])
            else:
                followup = random.choice(CUSTOMER_FOLLOWUPS["frustrated"]).format(days=random.randint(2, 7))

            msg_num = len(messages) + 1
            messages.append({
                "message_id": f"MSG-{thread_id:03d}-{msg_num:03d}",
                "role": "customer",
                "timestamp": generate_timestamp(current_time),
                "subject": f"Re: {get_subject_line(issue_type, product)}",
                "body": followup
            })

            # Additional exchanges for longer threads
            if thread_type in ["D", "E", "F", "G"]:
                # Another agent response
                current_time += timedelta(hours=random.uniform(1, 24))
                msg_num = len(messages) + 1

                if scenario in ["chargeback_threat", "reputational_threat", "escalating"]:
                    # Escalation response
                    agent_body = f"Hi {customer['first_name']},\n\nI understand your frustration and I've escalated this to my supervisor. Someone from our management team will reach out within 24 hours to resolve this.\n\nWe truly value your business and want to make this right.\n\nSincerely,\n{agent['name']}"
                else:
                    agent_body = f"Hi {customer['first_name']},\n\nThank you for your patience. Is there anything else I can help you with?\n\nBest,\n{agent['name']}"

                messages.append({
                    "message_id": f"MSG-{thread_id:03d}-{msg_num:03d}",
                    "role": "agent",
                    "agent_name": agent["name"],
                    "agent_id": agent["id"],
                    "timestamp": generate_timestamp(current_time),
                    "subject": f"Re: {get_subject_line(issue_type, product)}",
                    "body": agent_body,
                    "response_time_hours": round(random.uniform(1, 12), 1)
                })

                # Final customer response for E, F, G types
                if thread_type in ["E", "F", "G"]:
                    current_time += timedelta(hours=random.uniform(0.5, 12))
                    msg_num = len(messages) + 1

                    if scenario in ["happy_resolution", "policy_decline_accepted"]:
                        final_response = "Okay, thank you for following up. I appreciate your help."
                    else:
                        final_response = random.choice([
                            "We'll see about that. I've already filed my complaint.",
                            "Too little too late. I'm done with this company.",
                            "Fine. But I'm still leaving that review."
                        ])

                    messages.append({
                        "message_id": f"MSG-{thread_id:03d}-{msg_num:03d}",
                        "role": "customer",
                        "timestamp": generate_timestamp(current_time),
                        "subject": f"Re: {get_subject_line(issue_type, product)}",
                        "body": final_response
                    })

    # Determine final status
    last_message = messages[-1]
    status = "closed"
    if scenario == "no_response" or scenario == "double_text":
        status = "open"
    elif last_message["role"] == "customer" and scenario in ["escalating", "chargeback_threat", "reputational_threat"]:
        status = "open"  # Unresolved

    # Calculate hours since last response
    last_timestamp = datetime.strptime(last_message["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    hours_since = (datetime.now() - last_timestamp).total_seconds() / 3600

    return {
        "thread_id": f"TH-2024-{thread_id:03d}",
        "created_at": messages[0]["timestamp"],
        "updated_at": last_message["timestamp"],
        "status": status,
        "last_message_role": last_message["role"],
        "hours_since_last_response": round(hours_since, 1),
        "total_messages": len(messages),
        "customer_double_texted": double_texted,
        "customer": customer,
        "order": {
            "order_id": order_id,
            "products": [product] if random.random() > 0.3 else [product, random.choice([p for p in PRODUCTS if p != product])],
            "total": round(random.uniform(39.99, 189.99), 2)
        },
        "category": issue_type,
        "request_type": request_type,
        "request_reasonable": request_reasonable,
        "our_response_type": our_response_type,
        "assigned_agent": agent if our_response_type != "no_response" else None,
        "messages": messages
    }


def get_subject_line(issue_type: str, product: str) -> str:
    subjects = {
        "missing_items": f"Missing items in my order",
        "damaged_product": f"Damaged {product} received",
        "product_not_working": f"{product} not working as advertised",
        "subscription_cancel": "Cancel my subscription ASAP",
        "late_delivery": "Where is my order??",
        "billing_dispute": "Incorrect charge on my account",
        "wrong_product": "Wrong product received",
        "allergic_reaction": f"Reaction to {product} - URGENT",
        "general_inquiry": f"Question about {product}"
    }
    return subjects.get(issue_type, f"Question about {product}")


def map_issue_to_request(issue_type: str) -> str:
    mapping = {
        "missing_items": "replacement",
        "damaged_product": "replacement",
        "product_not_working": "refund",
        "subscription_cancel": "cancellation",
        "late_delivery": "information",
        "billing_dispute": "refund",
        "wrong_product": "replacement",
        "allergic_reaction": "information",
        "general_inquiry": "information"
    }
    return mapping.get(issue_type, "information")


def generate_all_threads():
    """Generate 30 threads with the specified scenario distribution"""

    scenarios = [
        # Happy resolution - 6 threads
        ("happy_resolution", "A"), ("happy_resolution", "B"), ("happy_resolution", "A"),
        ("happy_resolution", "B"), ("happy_resolution", "B"), ("happy_resolution", "A"),
        # Policy decline accepted - 3 threads
        ("policy_decline_accepted", "B"), ("policy_decline_accepted", "C"), ("policy_decline_accepted", "B"),
        # Policy decline frustrated - 3 threads
        ("policy_decline_frustrated", "C"), ("policy_decline_frustrated", "D"), ("policy_decline_frustrated", "C"),
        # Escalating - 4 threads
        ("escalating", "D"), ("escalating", "E"), ("escalating", "D"), ("escalating", "E"),
        # No response - 4 threads
        ("no_response", "B"), ("no_response", "B"), ("no_response", "C"), ("no_response", "B"),
        # Double text - 3 threads
        ("double_text", "G"), ("double_text", "G"), ("double_text", "G"),
        # Chargeback/legal threat - 3 threads
        ("chargeback_threat", "E"), ("chargeback_threat", "F"), ("chargeback_threat", "D"),
        # Reputational threat - 2 threads
        ("reputational_threat", "D"), ("reputational_threat", "C"),
        # Wrong answer - 2 threads
        ("wrong_answer", "C"), ("wrong_answer", "D"),
    ]

    threads = []
    for i, (scenario, thread_type) in enumerate(scenarios, 1):
        thread = create_thread(i, scenario, thread_type)
        threads.append(thread)

    return {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_threads": len(threads),
            "scenario_distribution": {
                "happy_resolution": 6,
                "policy_decline_accepted": 3,
                "policy_decline_frustrated": 3,
                "escalating": 4,
                "no_response": 4,
                "double_text": 3,
                "chargeback_legal_threat": 3,
                "reputational_threat": 2,
                "wrong_answer": 2
            }
        },
        "threads": threads
    }


if __name__ == "__main__":
    print("Generating 30 sample email threads...")
    data = generate_all_threads()

    output_path = "data/email_threads.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Created {data['metadata']['total_threads']} threads")
    print(f"Saved to: {output_path}")

    # Print summary
    print("\nScenario distribution:")
    for scenario, count in data["metadata"]["scenario_distribution"].items():
        print(f"  {scenario}: {count}")
