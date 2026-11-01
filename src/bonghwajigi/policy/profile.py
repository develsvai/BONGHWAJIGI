from bonghwajigi.contracts.policy import ProfileInput


def normalize_profile(profile, revision):
    mobility = {
        "independent": "independent",
        "walking_aid": "needs_time",
        "wheelchair": "needs_time",
        "assistance_required": "requires_help",
        "unknown": "unknown",
    }[profile.mobility]
    if mobility != "requires_help" and (
        profile.stairs in {"difficult", "unable"} or "vision" in profile.sensory_supports
    ):
        mobility = "needs_time"
    return ProfileInput(
        revision=revision,
        mobility=mobility,
        mobility_assistance=mobility in {"needs_time", "requires_help"},
        child_registered="child" in profile.dependents,
        assistive_device=profile.mobility in {"walking_aid", "wheelchair"},
        helper_registered=profile.helper_registered,
        vehicle_access=profile.vehicle_access,
        communication="audio"
        if profile.communication_preference == "voice"
        else profile.communication_preference,
    )
