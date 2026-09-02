import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export const LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "or", label: "Odia", native: "ଓଡ଼ିଆ" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ml", label: "Malayalam", native: "മലയാളം" },
  { code: "pa", label: "Punjabi", native: "ਪੰਜਾਬੀ" },
  { code: "as", label: "Assamese", native: "অসমীয়া" },
  { code: "ur", label: "Urdu", native: "اردو" },
  { code: "sa", label: "Sanskrit", native: "संस्कृतम्" },
  { code: "kok", label: "Konkani", native: "कोंकणी" },
  { code: "ne", label: "Nepali", native: "नेपाली" },
  { code: "doi", label: "Dogri", native: "डोगरी" },
  { code: "mai", label: "Maithili", native: "मैथिली" },
  { code: "ks", label: "Kashmiri", native: "कॉशुर" },
  { code: "mni", label: "Manipuri", native: "মৈতৈলোন্" },
  { code: "sat", label: "Santali", native: "ᱥᱟᱱᱛᱟᱲᱤ" },
  { code: "brx", label: "Bodo", native: "बड़ो" },
] as const;

export type LanguageCode = (typeof LANGUAGES)[number]["code"];

type TranslationMap = Partial<Record<LanguageCode, string>>;

const UI: Record<string, TranslationMap> = {
  "Verify Document": { hi: "दस्तावेज़ सत्यापित करें", or: "ଦଲିଲ ସତ୍ୟାପନ କରନ୍ତୁ", bn: "নথি যাচাই করুন", te: "పత్రాన్ని ధృవీకరించండి", ta: "ஆவணத்தைச் சரிபார்க்கவும்", mr: "दस्तऐवज सत्यापित करा", gu: "દસ્તાવેજ ચકાસો", kn: "ದಾಖಲೆಯನ್ನು ಪರಿಶೀಲಿಸಿ", ml: "രേഖ പരിശോധിക്കുക", pa: "ਦਸਤਾਵੇਜ਼ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ", as: "নথি পৰীক্ষা কৰক", ur: "دستاویز کی تصدیق کریں", sa: "दस्तावेजं सत्यापयतु", kok: "दस्तावेज तपासात", ne: "कागजात प्रमाणित गर्नुहोस्" },
  "About": { hi: "हमारे बारे में", or: "ଆମ ବିଷୟରେ", bn: "আমাদের সম্পর্কে", te: "మా గురించి", ta: "எங்களைப் பற்றி", mr: "आमच्याबद्दल", gu: "અમારા વિશે", kn: "ನಮ್ಮ ಬಗ್ಗೆ", ml: "ഞങ്ങളെക്കുറിച്ച്", pa: "ਸਾਡੇ ਬਾਰੇ", as: "আমাৰ বিষয়ে", ur: "ہمارے بارے میں", sa: "अस्माकं विषये", kok: "आमच्या विशीं", ne: "हाम्रो बारेमा" },
  "FAQ": { hi: "अक्सर पूछे जाने वाले प्रश्न", or: "ସାଧାରଣ ପ୍ରଶ୍ନ", bn: "প্রায়শই জিজ্ঞাসিত প্রশ্ন", te: "తరచుగా అడిగే ప్రశ్నలు", ta: "அடிக்கடி கேட்கப்படும் கேள்விகள்", mr: "वारंवार विचारले जाणारे प्रश्न", gu: "વારંવાર પૂછાતા પ્રશ્નો", kn: "ಪದೇ ಪದೇ ಕೇಳಲಾಗುವ ಪ್ರಶ್ನೆಗಳು", ml: "പതിവായി ചോദിക്കുന്ന ചോദ്യങ്ങൾ", pa: "ਅਕਸਰ ਪੁੱਛੇ ਜਾਂਦੇ ਸਵਾਲ", as: "সঘনাই সোধা প্ৰশ্ন", ur: "اکثر پوچھے گئے سوالات", sa: "सामान्याः प्रश्नाः", kok: "वारंवार विचारले प्रश्न", ne: "बारम्बार सोधिने प्रश्नहरू" },
  "Contact": { hi: "संपर्क", or: "ଯୋଗାଯୋଗ", bn: "যোগাযোগ", te: "సంప్రదించండి", ta: "தொடர்பு", mr: "संपर्क", gu: "સંપર્ક", kn: "ಸಂಪರ್ಕಿಸಿ", ml: "ബന്ധപ്പെടുക", pa: "ਸੰਪਰਕ", as: "যোগাযোগ", ur: "رابطہ", sa: "सम्पर्कः", kok: "संपर्क", ne: "सम्पर्क" },
  "Portal Login": { hi: "पोर्टल लॉगिन", or: "ପୋର୍ଟାଲ ଲଗଇନ", bn: "পোর্টাল লগইন", te: "పోర్టల్ లాగిన్", ta: "போர்டல் உள்நுழைவு", mr: "पोर्टल लॉगिन", gu: "પોર્ટલ લૉગિન", kn: "ಪೋರ್ಟಲ್ ಲಾಗಿನ್", ml: "പോർട്ടൽ ലോഗിൻ", pa: "ਪੋਰਟਲ ਲਾਗਇਨ", as: "পৰ্টেল লগইন", ur: "پورٹل لاگ ان", sa: "पोर्टल प्रवेशः", kok: "पोर्टल लॉगिन", ne: "पोर्टल लगइन" },
  "Institution Login": { hi: "संस्था लॉगिन", or: "ଅନୁଷ୍ଠାନ ଲଗଇନ", bn: "প্রতিষ্ঠান লগইন", te: "సంస్థ లాగిన్", ta: "நிறுவன உள்நுழைவு", mr: "संस्था लॉगिन", gu: "સંસ્થા લૉગિન", kn: "ಸಂಸ್ಥೆ ಲಾಗಿನ್", ml: "സ്ഥാപന ലോഗിൻ", pa: "ਸੰਸਥਾ ਲਾਗਇਨ", as: "প্ৰতিষ্ঠান লগইন", ur: "ادارہ لاگ ان", sa: "संस्था प्रवेशः", kok: "संस्था लॉगिन", ne: "संस्था लगइन" },
  "Administrator Login": { hi: "व्यवस्थापक लॉगिन", or: "ପ୍ରଶାସକ ଲଗଇନ", bn: "অ্যাডমিন লগইন", te: "నిర్వాహక లాగిన్", ta: "நிர்வாகி உள்நுழைவு", mr: "प्रशासक लॉगिन", gu: "એડમિન લૉગિન", kn: "ನಿರ್ವಾಹಕ ಲಾಗಿನ್", ml: "അഡ്മിൻ ലോഗിൻ", pa: "ਪ੍ਰਸ਼ਾਸਕ ਲਾਗਇਨ", as: "প্ৰশাসক লগইন", ur: "ایڈمن لاگ ان", sa: "प्रशासक प्रवेशः", kok: "प्रशासक लॉगिन", ne: "प्रशासक लगइन" },
  "Verify Now": { hi: "अभी सत्यापित करें", or: "ବର୍ତ୍ତମାନ ସତ୍ୟାପନ କରନ୍ତୁ", bn: "এখনই যাচাই করুন", te: "ఇప్పుడే ధృవీకరించండి", ta: "இப்போதே சரிபார்க்கவும்", mr: "आता सत्यापित करा", gu: "હમણાં ચકાસો", kn: "ಈಗ ಪರಿಶೀಲಿಸಿ", ml: "ഇപ്പോൾ പരിശോധിക്കുക", pa: "ਹੁਣੇ ਪੁਸ਼ਟੀ ਕਰੋ", as: "এতিয়া পৰীক্ষা কৰক", ur: "ابھی تصدیق کریں", sa: "इदानीं सत्यापयतु", kok: "आतां तपासात", ne: "अहिले प्रमाणित गर्नुहोस्" },
  "Language": { hi: "भाषा", or: "ଭାଷା", bn: "ভাষা", te: "భాష", ta: "மொழி", mr: "भाषा", gu: "ભાષા", kn: "ಭಾಷೆ", ml: "ഭാഷ", pa: "ਭਾਸ਼ਾ", as: "ভাষা", ur: "زبان", sa: "भाषा", kok: "भास", ne: "भाषा" },
  "Chat Assistant": { hi: "चैट सहायक", or: "ଚାଟ ସହାୟକ", bn: "চ্যাট সহায়ক", te: "చాట్ సహాయకుడు", ta: "அரட்டை உதவியாளர்", mr: "चॅट सहाय्यक", gu: "ચેટ સહાયક", kn: "ಚಾಟ್ ಸಹಾಯಕ", ml: "ചാറ്റ് സഹായി", pa: "ਚੈਟ ਸਹਾਇਕ", as: "চেট সহায়ক", ur: "چیٹ معاون", sa: "संवादसहायकः", kok: "चॅट सहाय्यक", ne: "च्याट सहायक" },
  "Send": { hi: "भेजें", or: "ପଠାନ୍ତୁ", bn: "পাঠান", te: "పంపండి", ta: "அனுப்பவும்", mr: "पाठवा", gu: "મોકલો", kn: "ಕಳುಹಿಸಿ", ml: "അയയ്ക്കുക", pa: "ਭੇਜੋ", as: "পঠিয়াওক", ur: "بھیجیں", sa: "प्रेषयतु", kok: "धाडात", ne: "पठाउनुहोस्" },
};

export const LANGUAGE_NAMES: Record<LanguageCode, string> = Object.fromEntries(
  LANGUAGES.map((language) => [language.code, language.native])
) as Record<LanguageCode, string>;

function browserLanguage(): LanguageCode {
  const base = navigator.language?.split("-")[0]?.toLowerCase();
  const supported = LANGUAGES.find((language) => language.code === base);
  return supported?.code ?? "en";
}

interface LanguageContextValue {
  language: LanguageCode;
  setLanguage: (language: LanguageCode) => void;
  t: (text: string) => string;
  languageName: string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>(() => {
    const saved = localStorage.getItem("pramaanscan-language") as LanguageCode | null;
    return saved && LANGUAGES.some((item) => item.code === saved) ? saved : browserLanguage();
  });

  const setLanguage = (next: LanguageCode) => {
    setLanguageState(next);
    localStorage.setItem("pramaanscan-language", next);
  };

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ur" ? "rtl" : "ltr";
  }, [language]);

  const value = useMemo<LanguageContextValue>(() => ({
    language,
    setLanguage,
    languageName: LANGUAGE_NAMES[language],
    t: (text: string) => UI[text]?.[language] ?? text,
  }), [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const value = useContext(LanguageContext);
  if (!value) throw new Error("useLanguage must be used inside LanguageProvider");
  return value;
}
