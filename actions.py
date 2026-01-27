# --------------------------------
# TRUST ACTION RESOLVER
# --------------------------------

def resolve_action(band: str, confidence: float | None):
    if band == "high_trust":
        return {
            "action": "ALLOW_FULL",
            "policy": "full_access",
            "message": "High trust — full access granted",
        }

    if band == "normal":
        return {
            "action": "ALLOW_LIMITED",
            "policy": "limited_access",
            "message": "Normal trust — limited access",
        }

    if band == "low_trust":
        return {
            "action": "RESTRICT",
            "policy": "restricted_access",
            "message": "Low trust — access restricted",
        }

    if band == "insufficient_data":
        return {
            "action": "REQUIRE_REVIEW",
            "policy": "manual_review",
            "message": "Insufficient data — manual review required",
        }

    return {
        "action": "REQUIRE_REVIEW",
        "policy": "unknown",
        "message": "Unknown trust state — review required",
    }
