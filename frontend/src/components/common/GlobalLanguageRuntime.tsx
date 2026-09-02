import { useEffect, useRef } from "react";
import { translateTexts } from "@/api/translation";
import { useLanguage } from "@/context/LanguageContext";

const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "CODE", "PRE", "TEXTAREA", "INPUT"]);
const technical = /^(https?:\/\/|www\.|mailto:|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$|[0-9a-f]{16,}$|[A-Z0-9_-]{10,}$)/i;

export function GlobalLanguageRuntime() {
  const { language } = useLanguage();
  const languageRef = useRef(language);
  const translating = useRef(false);
  const textOriginals = useRef(new WeakMap<Text, string>());
  const attrOriginals = useRef(new WeakMap<Element, Map<string, string>>());
  const cache = useRef(new Map<string, string>());

  useEffect(() => {
    languageRef.current = language;
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ur" ? "rtl" : "ltr";

    if (language === "en") {
      // Restore original English text/attributes when returning to English.
      document.querySelectorAll("[data-ps-no-translate]").forEach(() => {});
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const nodes: Text[] = [];
      while (walker.nextNode()) nodes.push(walker.currentNode as Text);
      nodes.forEach((node) => {
        const original = textOriginals.current.get(node);
        if (original !== undefined) node.nodeValue = original;
      });
      document.querySelectorAll<HTMLElement>("*").forEach((el) => {
        const originals = attrOriginals.current.get(el);
        originals?.forEach((value, attr) => el.setAttribute(attr, value));
      });
      return;
    }

    const translatePage = async () => {
      if (translating.current) return;
      translating.current = true;
      try {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const nodes: Text[] = [];
        const originals: string[] = [];
        while (walker.nextNode()) {
          const node = walker.currentNode as Text;
          const parent = node.parentElement;
          if (!parent || SKIP_TAGS.has(parent.tagName) || parent.closest("[data-ps-no-translate]")) continue;
          const raw = textOriginals.current.get(node) ?? node.nodeValue ?? "";
          if (!textOriginals.current.has(node)) textOriginals.current.set(node, raw);
          const value = raw.trim();
          if (!value || value.length < 2 || technical.test(value)) continue;
          nodes.push(node);
          originals.push(value);
        }

        const unique = [...new Set(originals)];
        const missing = unique.filter((x) => !cache.current.has(`${language}:${x}`));
        for (let i = 0; i < missing.length; i += 50) {
          if (languageRef.current !== language) return;
          const batch = missing.slice(i, i + 50);
          try {
            const translated = await translateTexts(batch, language);
            batch.forEach((original, index) => cache.current.set(`${language}:${original}`, translated[index] ?? original));
          } catch {
            batch.forEach((original) => cache.current.set(`${language}:${original}`, original));
          }
        }
        nodes.forEach((node, index) => {
          if (languageRef.current !== language) return;
          const translated = cache.current.get(`${language}:${originals[index]}`);
          if (translated) node.nodeValue = (node.nodeValue ?? "").replace(originals[index], translated);
        });

        const attrs = ["placeholder", "aria-label", "title"];
        document.querySelectorAll<HTMLElement>("input,textarea,button,[title],[aria-label]").forEach((el) => {
          if (el.closest("[data-ps-no-translate]")) return;
          for (const attr of attrs) {
            const value = el.getAttribute(attr);
            if (!value || value.length < 2 || technical.test(value)) continue;
            let originalsForEl = attrOriginals.current.get(el);
            if (!originalsForEl) {
              originalsForEl = new Map();
              attrOriginals.current.set(el, originalsForEl);
            }
            const original = originalsForEl.get(attr) ?? value;
            originalsForEl.set(attr, original);
            const translated = cache.current.get(`${language}:${original}`);
            if (translated) el.setAttribute(attr, translated);
          }
        });
      } finally {
        translating.current = false;
      }
    };

    const timer = window.setTimeout(translatePage, 80);
    const observer = new MutationObserver(() => {
      if (!translating.current) window.setTimeout(translatePage, 40);
    });
    observer.observe(document.body, { subtree: true, childList: true });

    return () => {
      window.clearTimeout(timer);
      observer.disconnect();
    };
  }, [language]);

  return null;
}
