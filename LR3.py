# app.py
import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st

# ----------------------------
# Operator mapping
# ----------------------------
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

# ----------------------------
# Your Scholarship Rules 
# ----------------------------
SCHOLARSHIP_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    }
]

# ----------------------------
# Rule Engine Functions 
# ----------------------------
def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False

def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))

def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return ({"decision": "REVIEW", "reason": "No rule matched – manual review required"}, [])

    # Sort by priority descending, highest wins
    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best_action = fired_sorted[0]["action"]
    return best_action, fired_sorted

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Scholarship Eligibility Checker", page_icon="🎓", layout="wide")
st.title("🎓 Scholarship Eligibility Decision System")
st.caption("Enter student data → instantly see scholarship decision based on your rules.")

# Sidebar - Input Form
with st.sidebar:
    st.header("Student Profile")
    
    cgpa = st.slider("CGPA", min_value=0.0, max_value=4.0, value=3.5, step=0.05)
    co_curricular_score = st.slider("Co-curricular Score (0–100)", min_value=0, max_value=100, value=70)
    family_income = st.number_input("Monthly Family Income (MYR)", min_value=0, step=500, value=10000)
    disciplinary_actions = st.number_input("Number of Disciplinary Actions", min_value=0, step=1, value=0)
    
    st.divider()
    st.header("Rules (Editable JSON)")
    st.caption("You can modify rules live. Invalid JSON → falls back to default rules.")
    
    default_json = json.dumps(SCHOLARSHIP_RULES, indent=2)
    rules_text = st.text_area("Edit rules JSON here", value=default_json, height=400, key="rules_input")

    evaluate = st.button("Evaluate Eligibility", type="primary", use_container_width=True)

# Main area - Show facts
facts = {
    "cgpa": float(cgpa),
    "co_curricular_score": int(co_curricular_score),
    "family_income": int(family_income),
    "disciplinary_actions": int(disciplinary_actions)
}

st.subheader("📋 Student Data")
st.json(facts, expanded=False)

# Parse custom rules (fallback to default if invalid)
try:
    custom_rules = json.loads(rules_text)
    if not isinstance(custom_rules, list):
        raise ValueError("Must be a list")
    rules = custom_rules
    st.success("✅ Using custom rules")
except Exception as e:
    st.error(f"Invalid JSON → Using default scholarship rules ({e})")
    rules = SCHOLARSHIP_RULES

# Show active rules
with st.expander("View Active Rules", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

if evaluate:
    decision, matched_rules = run_rules(facts, rules)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🏆 Final Decision")
        dec = decision.get("decision", "REVIEW")
        reason = decision.get("reason", "No reason provided")

        if dec == "AWARD_FULL":
            st.success(f"**{dec}**  \nFull Scholarship Awarded!")
            st.info(reason)
        elif dec == "AWARD_PARTIAL":
            st.warning(f"**{dec}**  \nPartial Scholarship Awarded")
            st.info(reason)
        elif dec == "REVIEW":
            st.warning(f"**{dec}**  \nRequires Manual Review")
            st.info(reason)
        elif dec == "REJECT":
            st.error(f"**{dec}**  \nNot Eligible")
            st.info(reason)
        else:
            st.info(f"**{dec}**  \n{reason}")

    with col2:
        st.subheader("🔥 Rules That Fired (Highest Priority Wins)")
        if not matched_rules:
            st.info("No rules matched.")
        else:
            for i, rule in enumerate(matched_rules, 1):
                priority = rule.get("priority", 0)
                name = rule.get("name", "(unnamed)")
                action = rule["action"]["decision"]
                if i == 1:
                    st.markdown(f"**→ {i}. {name}** (Priority: {priority}) **← WINNER**")
                else:
                    st.markdown(f"{i}. {name} (Priority: {priority})")
                with st.expander(f"Conditions & Action"):
                    st.write("**Conditions:**")
                    for cond in rule.get("conditions", []):
                        field, op, val = cond
                        actual = facts.get(field, "N/A")
                        satisfied = "✓" if evaluate_condition(facts, cond) else "✗"
                        st.caption(f"{satisfied} `{field} {op} {val}` → actual: `{actual}`")
                    st.write("**Action:**")
                    st.json(rule["action"])

else:
    st.info("👈 Adjust student data in the sidebar and click **Evaluate Eligibility** to see the result.")