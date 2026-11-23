from data import CASE_001

def generate_case():

    return {
        "victim": CASE_001["victim"],
        "location": CASE_001["location"],
        "suspects": [
            {
                "name": "آسر منصور",
                "age": 46,
                "job": "روائي جرائم",
                "secret": "كان يبتز الضحية"
            },
            {
                "name": "ليلى الديب",
                "age": 34,
                "job": "عازفة بيانو",
                "secret": "كانت على علاقة سرية بالضحية"
            },
            {
                "name": "يوسف بيومي",
                "age": 51,
                "job": "طبيب نفسي",
                "secret": "يعرف معلومة خطيرة عن القضية"
            },
            {
                "name": "نادين مراد",
                "age": 29,
                "job": "صحفية تحقيقات",
                "secret": "كانت تراقب الضحية منذ أسابيع"
            }
        ],
        "killer": {
            "name": CASE_001["killer"],
            "job": "صحفية تحقيقات",
            "secret": "كانت تراقب الضحية منذ أسابيع"
        }
    }


def investigate(action):

    return CASE_001["evidence"].get(
        action,
        "لا توجد معلومات جديدة."
    )
