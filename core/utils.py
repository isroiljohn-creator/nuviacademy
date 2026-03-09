import re

def generate_referral_code(user_id):
    """Generates a referral code based on user ID."""
    return f"r{user_id}"

def get_referrer_id_from_code(code):
    """Extracts user ID from referral code."""
    if code.startswith("r") and code[1:].isdigit():
        return int(code[1:])
    return None

def strip_html(text):
    """Removes HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def safe_split_text(text, limit=4000):
    """
    Splits text into chunks of maximum 'limit' characters, 
    respecting newlines to avoid breaking HTML tags or sentences.
    """
    if len(text) <= limit:
        return [text]
        
    chunks = []
    current_chunk = ""
    
    # Split by double newline first (paragraphs)
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= limit:
            current_chunk += para + "\n\n"
        else:
            # If current chunk is not empty, save it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If paragraph itself is too long, split by single newline
            if len(para) > limit:
                lines = para.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= limit:
                        current_chunk += line + "\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                        # If line is still too long, hard split (rare)
                        while len(line) > limit:
                            chunks.append(line[:limit])
                            line = line[limit:]
                        current_chunk = line + "\n"
            else:
                current_chunk = para + "\n\n"
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def parse_callback(data, prefix=None, min_parts=0):
    """
    Safely parses callback data.
    
    Args:
        data (str): The callback data string.
        prefix (str, optional): Expected prefix (e.g., 'redeem_').
        min_parts (int, optional): Minimum number of parts expected after split('_').
        
    Returns:
        list: List of parts if valid, None otherwise.
    """
    if not data or not isinstance(data, str):
        return None
        
    if prefix and not data.startswith(prefix):
        return None
        
    parts = data.split('_')
    
    if len(parts) < min_parts:
        return None
        
    return parts

def safe_handler(bot):
    """
    Decorator to wrap handlers with try-except block to prevent crashes.
    """
    def decorator(func):
        def wrapper(message, *args, **kwargs):
            try:
                return func(message, *args, **kwargs)
            except Exception as e:
                print(f"ERROR in {func.__name__}: {e}")
                try:
                    bot.send_message(message.chat.id, "⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
                except:
                    pass
        return wrapper
    return decorator
