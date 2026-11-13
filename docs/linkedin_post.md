# LinkedIn post

Image: `docs/assets/linkedin_poster.png` (1440×1800, 4:5)

---

**100 victims.**

That is how many people an illegal loan app can harm before a complaint-driven regulator even opens a file. It is the same number for a small app and a huge one.

The reason is simple. If a regulator acts after K complaints, and only a share θ of victims ever complain, every illegal app gets a "free-harm allowance" of K/θ victims. With 10 complaints and a 10% reporting rate, that is 100. And the victims who are threatened and shamed into silence report least, so the most abusive lenders get the largest allowance.

I wrote a working paper on how to break that trap: **Regulating Non-Bank Lenders in the Digital Age**.

What's inside:
🌏 12 regulatory regimes (Thailand, India, Indonesia, the Philippines, Malaysia, Singapore, Japan, Kenya, UK, Australia, EU, US) coded on 7 design dimensions
📐 3 formal models: the free-harm allowance, why faster takedown shrinks the illegal market more than proportionally, and why price caps and enforcement must move together
🎲 A Monte Carlo of 200,000 apps: moving from complaints to detection, fast takedown and an app-store listing check cuts victims per app by 91%
🔍 lendwatch-th, an open-source pipeline that finds lending apps, checks them against the licensed-lender list, links clone apps to their operators and estimates how many no source sees (precision 0.997 on 30 synthetic markets)
🗺️ A three-phase reform roadmap for Thailand, ordered by the legal instrument each step needs

Honest caveats: every number is model-based or simulated under hypothetical parameters, the regime coding is provisional, and the pipeline has not yet run on real app stores. The method is ready; the estimates for Thailand are not.

📖 Read online: https://thanatchon36.github.io/non-bank-lending-research/paper/
💻 Code + data: https://github.com/thanatchon36/non-bank-lending-research
🤗 Dataset: https://huggingface.co/datasets/thanatchon36/non-bank-lending-research
DOI: 10.5281/zenodo.24184054

Feedback very welcome, especially from people who work on consumer credit, financial consumer protection or app-store policy in Asia.

Views are my own.

#FinancialRegulation #DigitalLending #ConsumerProtection #SupTech #Thailand #OpenScience

---

# ฉบับภาษาไทย

**100 คน**

คือจำนวนผู้เสียหายที่แอปเงินกู้เถื่อนหนึ่งแอปสร้างได้ ก่อนที่หน่วยงานซึ่งรอเรื่องร้องเรียนจะเริ่มเปิดแฟ้มด้วยซ้ำ และเป็นตัวเลขเดียวกันไม่ว่าแอปจะเล็กหรือใหญ่

ถ้าหน่วยงานลงมือเมื่อมีเรื่องร้องเรียนครบ K เรื่อง และผู้เสียหายร้องเรียนเพียงสัดส่วน θ ทุกแอปจะได้ "โควตาทำร้ายฟรี" K/θ คน เช่น 10 เรื่อง ÷ 10% = 100 คน ยิ่งเจ้าหนี้ข่มขู่ประจานจนผู้เสียหายไม่กล้าร้องเรียน โควตานี้ยิ่งสูง

ผมเขียน working paper **Regulating Non-Bank Lenders in the Digital Age** เพื่อหาทางออกจากกับดักนี้:
🌏 เปรียบเทียบการกำกับ 12 ประเทศ/ภูมิภาค บน 7 มิติ
📐 3 แบบจำลองเชิงทฤษฎี
🎲 Monte Carlo 200,000 แอป: เปลี่ยนจากรอร้องเรียนเป็นตรวจจับเชิงรุก + ปิดเร็ว + ตรวจก่อนขึ้นสโตร์ ลดผู้เสียหายต่อแอปได้ 91%
🔍 lendwatch-th เครื่องมือโอเพนซอร์สตรวจหาแอปเงินกู้ที่ไม่มีใบอนุญาต
🗺️ Roadmap ปฏิรูป 3 ระยะสำหรับไทย

ข้อควรระวัง: ตัวเลขทั้งหมดมาจากแบบจำลองและการจำลองด้วยพารามิเตอร์สมมติ ไม่ใช่ค่าประมาณของตลาดไทย

📖 https://thanatchon36.github.io/non-bank-lending-research/paper/
💻 https://github.com/thanatchon36/non-bank-lending-research

ความเห็นในโพสต์นี้เป็นของผมเอง
