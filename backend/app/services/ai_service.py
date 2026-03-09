from google import genai

class AIService:
    def __init__(self):
        import os
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.client = genai.Client(api_key=gemini_key)
            self.model_name = 'gemini-1.5-flash'
        else:
            self.client = None
            print("⚠️ GEMINI_API_KEY not set. AI features disabled.")

    def generate_content(self, prompt: str) -> str | None:
        if not self.client:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"AI Error: {e}")
            return None

    def format_text(self, raw_text: str, title: str) -> str:
        if not raw_text:
            return ""
        
        text = raw_text.replace("**", "").replace("##", "").replace("#", "")
        text = text.replace("<script>", "").replace("</script>", "")
        
        if len(text) > 2000:
            text = text[:2000] + "..."
            
        return f"🍽 <b>{title}</b>\n\n{text.strip()}"

ai_service = AIService()
