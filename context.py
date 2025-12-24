def build_context(context):
    return {
        "platform": context["platform"],
        "time_bucket": context["time_bucket"],
        "day_of_week": context["day_of_week"]
    }
