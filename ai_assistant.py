"""AI assistant.

The route layer only validates and returns JSON. This module decides
whether to call a provider or the labelled demo fallback.

Speech methods are a stable interface for a future provider. They do
not pretend that audio was transcribed or spoken.
"""

import httpx

from app.config import Settings
from app.data.demo_content import AI_DISCLAIMER

LANGUAGES = [
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "en", "name": "English", "native_name": "English"},
]

_MEDICAL = (
    "hospital", "doctor", "medicine", "pain", "bleeding", "chest", "ambulance", "emergency",
    "suicide", "kill myself", "হাসপাতাল", "ডাক্তার", "জরুরি", "ব্যথা", "আত্মহত্যা",
    "अस्पताल", "डॉक्टर", "आपात", "दर्द", "खुदकुशी",
)
_TOPICS = {
    "schemes": ("scheme", "yojana", "pmay", "kisan", "nrega", "প্রকল্প", "স্কিম", "योजना"),
    "agriculture": ("farm", "crop", "seed", "agriculture", "কৃষি", "ফসল", "खेती", "फसल"),
    "education": ("school", "education", "student", "স্কুল", "শিক্ষা", "स्कूल", "शिक्षा"),
    "health": ("health", "clinic", "স্বাস্থ্য", "स्वास्थ्य"),
    "services": ("water", "road", "electric", "sanitation", "complaint", "পানি", "রাস্তা", "पानी", "सड़क"),
}

_REPLIES = {
    "en": {
        "emergency": "Demo fallback: this is not medical advice and not a diagnosis. If someone is in danger, call 112 now. For non-urgent health information, contact a nearby government health centre and follow its staff.",
        "schemes": "Demo fallback: open the Government Schemes section to see sample programme names and their official websites. Do not treat this chat as an eligibility decision. Confirm rules, benefits, and documents on the official site.",
        "agriculture": "Demo fallback: for farming support, check the schemes section for agriculture programmes and confirm details on the official website. A local agriculture office can explain what applies to your village.",
        "education": "Demo fallback: use the location search to look for schools, and ask the school or district education office about admissions. This chat cannot confirm a seat or a scholarship.",
        "health": "Demo fallback: this is general information, not care for a patient. Call 112 in an emergency. Otherwise contact a government health centre.",
        "services": "Demo fallback: you can report a local problem in the complaint form. SafeVillage stores it for tracking and does not automatically send it to a government department.",
        "default": "Demo fallback: I can help you explore schemes, schools, farming information, health contacts, and how to record a village complaint in this demo. Ask in Bengali, Hindi, or English.",
    },
    "bn": {
        "emergency": "ডেমো উত্তর: এটি চিকিৎসা পরামর্শ বা রোগ নির্ণয় নয়। বিপদ হলে এখনই 112-তে কল করুন। জরুরি না হলে কাছের সরকারি স্বাস্থ্যকেন্দ্রে যোগাযোগ করুন।",
        "schemes": "ডেমো উত্তর: সরকারি প্রকল্পের নাম ও অফিসিয়াল ওয়েবসাইট স্কিম বিভাগে দেওয়া আছে। যোগ্যতা বা সুবিধা এই চ্যাটে নিশ্চিত করা হয় না। আবেদনের আগে অফিসিয়াল সাইটে যাচাই করুন।",
        "agriculture": "ডেমো উত্তর: কৃষি সহায়তার জন্য স্কিম বিভাগ দেখুন এবং স্থানীয় কৃষি অফিস বা অফিসিয়াল ওয়েবসাইটে নিয়ম যাচাই করুন।",
        "education": "ডেমো উত্তর: স্কুল খুঁজতে লোকেশন সার্চ ব্যবহার করুন। ভর্তি বা বৃত্তির সিদ্ধান্ত স্কুল বা শিক্ষা দপ্তর দেবে। এই চ্যাট আসন নিশ্চিত করে না।",
        "health": "ডেমো উত্তর: এটি সাধারণ তথ্য, কোনো রোগীর চিকিৎসা নয়। জরুরি অবস্থায় 112-তে কল করুন। অন্যথায় সরকারি স্বাস্থ্যকেন্দ্রে যোগাযোগ করুন।",
        "services": "ডেমো উত্তর: রাস্তা, পানি, বিদ্যুৎ বা স্বাস্থ্যের সমস্যা অভিযোগ ফর্মে লিখে রাখতে পারেন। এটি SafeVillage-এ সংরক্ষিত হয়, সরকারি দপ্তরে নিজে থেকে পাঠানো হয় না।",
        "default": "ডেমো উত্তর: আমি প্রকল্প, শিক্ষা, কৃষি, স্বাস্থ্য তথ্য এবং গ্রামের অভিযোগ ট্র্যাকিং নিয়ে সাধারণ দিকনির্দেশ দিতে পারি। এটি কোনো সরকারি সিদ্ধান্ত নয়।",
    },
    "hi": {
        "emergency": "डेमो उत्तर: यह चिकित्सा सलाह या निदान नहीं है। खतरा हो तो अभी 112 पर कॉल करें। गैर-जरूरी जानकारी के लिए नज़दीकी सरकारी स्वास्थ्य केंद्र से संपर्क करें।",
        "schemes": "डेमो उत्तर: योजनाओं के नाम और आधिकारिक वेबसाइट योजना खंड में हैं। पात्रता या लाभ इस चैट से तय नहीं होते। आवेदन से पहले आधिकारिक साइट जाँचें।",
        "agriculture": "डेमो उत्तर: खेती से जुड़ी योजनाओं के लिए योजना खंड देखें और नियम स्थानीय कृषि कार्यालय या आधिकारिक वेबसाइट पर जाँचें।",
        "education": "डेमो उत्तर: स्कूल खोजने के लिए लोकेशन खोज का उपयोग करें। दाखिला या छात्रवृत्ति स्कूल या शिक्षा विभाग तय करता है।",
        "health": "डेमो उत्तर: यह सामान्य जानकारी है, किसी मरीज का इलाज नहीं। आपात स्थिति में 112 पर कॉल करें।",
        "services": "डेमो उत्तर: सड़क, पानी, बिजली या स्वच्छता की समस्या शिकायत फ़ॉर्म में दर्ज कर सकते हैं। यह SafeVillage में सहेजी जाती है और अपने आप सरकारी विभाग को नहीं भेजी जाती।",
        "default": "डेमो उत्तर: मैं योजनाओं, शिक्षा, खेती, स्वास्थ्य जानकारी और गाँव की शिकायत ट्रैकिंग पर सामान्य मदद दे सकता हूँ। यह सरकारी निर्णय नहीं है।",
    },
}


class SpeechGateway:
    """Future speech providers should implement these two methods."""

    def transcribe(self, language: str) -> dict:
        return {
            "available": False,
            "provider": None,
            "detail": (
                f"Speech-to-text is not configured for '{language}'. "
                "Type your question at POST /api/ai/chat."
            ),
        }

    def synthesize(self, language: str) -> dict:
        return {
            "available": False,
            "provider": None,
            "detail": (
                f"Text-to-speech is not configured for '{language}'. "
                "The chat response can still be read on screen."
            ),
        }


speech_gateway = SpeechGateway()


def assistant_health(settings: Settings) -> dict:
    return {
        "status": "ok",
        "provider_configured": settings.ai_configured,
        "mode": "ai_provider" if settings.ai_configured else "demo_fallback",
        "languages": [item["code"] for item in LANGUAGES],
        "speech_to_text": "not_configured",
        "text_to_speech": "not_configured",
    }


def answer_question(settings: Settings, message: str, language: str) -> dict:
    topic = _topic(message)
    emergency = topic == "emergency"
    if settings.ai_configured:
        generated = _call_provider(settings, message, language, emergency)
        if generated:
            return _payload(language, "ai_provider", None, generated, emergency)
    reply = _REPLIES[language][topic if topic in _REPLIES[language] else "default"]
    label = {
        "en": "Demo fallback — not an official government or medical decision.",
        "bn": "ডেমো উত্তর — এটি কোনো সরকারি বা চিকিৎসা সিদ্ধান্ত নয়।",
        "hi": "डेमो उत्तर — यह कोई सरकारी या चिकित्सा निर्णय नहीं है।",
    }[language]
    return _payload(language, "demo_fallback", label, reply, emergency)


def _topic(message: str) -> str:
    text = message.lower()
    if any(word in text for word in _MEDICAL):
        return "emergency"
    for name, words in _TOPICS.items():
        if any(word in text for word in words):
            return name
    return "default"


def _payload(language: str, mode: str, label: str | None, reply: str, emergency: bool) -> dict:
    if emergency and "112" not in reply:
        reply = f"{reply} Call 112 if this is an emergency."
    return {
        "language": language,
        "mode": mode,
        "demo_label": label,
        "reply": reply,
        "disclaimer": AI_DISCLAIMER,
        "emergency": emergency,
    }


def _call_provider(settings: Settings, message: str, language: str, emergency: bool) -> str | None:
    language_name = {"en": "English", "hi": "Hindi", "bn": "Bengali"}[language]
    system = (
        "You are the SafeVillage information assistant for rural India. "
        f"Reply in {language_name}. "
        "You give general information about public schemes, education, agriculture, "
        "healthcare contacts, and village services. "
        "Never say that you made a government decision, approved a scheme, or filed an official complaint. "
        "Never invent eligibility rules or benefit amounts. Tell the person to verify on the official website. "
        "Never diagnose or prescribe. For any medical or danger question, tell them to call 112. "
        "Keep the reply under 140 words."
    )
    if emergency:
        system += " Start the reply by telling the person to call 112 if someone is in danger."
    try:
        response = httpx.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            json={
                "model": settings.ai_model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": message},
                ],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None
    if not isinstance(content, str) or not content.strip():
        return None
    return content.strip()
