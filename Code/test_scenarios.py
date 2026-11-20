from agent_logic import IndusMindAgent

def run_all_tests():
    agent = IndusMindAgent()

    scenarios = [
        ("1. فحص ماكينة سليمة (Normal)", "ما هي حالة الماكينة رقم 1؟"),
        ("2. عطل تآكل الأداة (TWF)", "Evaluate machine with air temp 298.9, process temp 309.1, speed 2861, torque 4.6, tool wear 215"),
        ("3. عطل تبديد الحرارة (HDF)", "افحص ماكينة حرارة الجو فيها 302.5 وحرارة العملية 310.5 والسرعة 1350 والعزم 45 وتآكل الأداة 50"),
        ("4. عطل الطاقة (PWF)", "Check machine UDI 161"),
        ("5. عطل الإجهاد الزائد (OSF)", "افحص ماكينة من نوع L فيها العزم 65 وتآكل الأداة 190 وحرارة الجو 298 وحرارة العملية 308 والسرعة 1400"),
        ("6. استعلام عام عن الصيانة الفورية", "إديني أسماء وأرقام الماكينات اللي محتاجة صيانة فورية"),
        ("7. رقم غير موجود (Error Handling)", "ما حالة الماكينة 999999؟"),
    ]

    for title, prompt in scenarios:
        print(f"\n{'='*60}\nTEST: {title}\nPROMPT: {prompt}\n{'-'*60}")
        response = agent.chat(prompt)
        print(f"RESPONSE:\n{response}")

if __name__ == "__main__":
    run_all_tests()