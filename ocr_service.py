import os
import base64
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user


def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return OpenAI(api_key=OPENAI_API_KEY)


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    client = get_openai_client()
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "system",
                "content": "당신은 이미지에서 텍스트를 정확하게 추출하는 OCR 전문가입니다. "
                           "이미지에 포함된 모든 텍스트를 정확하게 추출하여 반환해주세요. "
                           "영어와 한글 모두 정확하게 인식합니다. "
                           "텍스트의 원래 형식과 줄바꿈을 최대한 유지해주세요. "
                           "이미지에 텍스트가 없으면 '텍스트가 발견되지 않았습니다.'라고 답해주세요."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 이미지에서 모든 텍스트를 추출해주세요. 텍스트만 반환하고 다른 설명은 하지 마세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=4096
    )
    
    return response.choices[0].message.content
