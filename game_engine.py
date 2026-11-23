from data import CASE_001


def generate_case():

    public = CASE_001["public"]

    return {
        "title": public["title"],
        "story": public["story"],
        "victim": public["victim"],
        "location": public["location"],
        "forensic_report": public["forensic_report"],
        "camera_report": public["camera_report"],
        "call_log": public["call_log"],
        "witness_statement": public["witness_statement"],
        "timeline": public["timeline"],

        # الشخصيات
        "suspects": CASE_001["characters"],

        # البيانات السرية (للاستخدام الداخلي فقط)
        "truth": CASE_001["truth"],

        # طبقات المفاجآت
        "twist": CASE_001["twist"]
    }
