import { apiClient } from "./client";

export async function translateTexts(texts: string[], targetLanguage: string): Promise<string[]> {
  if (!texts.length || targetLanguage === "en") return texts;
  const { data } = await apiClient.post<{ translations: string[] }>("/language/translate", {
    texts,
    target_language: targetLanguage,
  });
  return Array.isArray(data?.translations) && data.translations.length === texts.length
    ? data.translations
    : texts;
}
