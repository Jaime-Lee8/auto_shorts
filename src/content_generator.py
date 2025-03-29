"""
콘텐츠 생성 모듈
- 추출된 자막과 번역된 내용을 바탕으로 쇼츠 콘텐츠에 최적화된 스크립트를 생성합니다.
- OpenAI Chat API를 사용하여 Hook 멘트, 핵심 요약, 배경 설명을 생성합니다.
- 스크립트 템플릿을 관리합니다.
"""
import os
import json
import logging
import openai
from datetime import datetime

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    OPENAI_API_KEY, DATA_DIR, LOGS_DIR, SHORTS_DURATION
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'content_generator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('content_generator')

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

class ContentGenerator:
    """콘텐츠 생성 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        # 스크립트 저장 디렉토리 생성
        os.makedirs(os.path.join(DATA_DIR, 'scripts'), exist_ok=True)
        
        # 스크립트 템플릿 로드
        self.templates = self._load_templates()
        
        logger.info("ContentGenerator 초기화 완료")
    
    def _load_templates(self):
        """
        스크립트 템플릿 로드
        
        Returns:
            dict: 템플릿 사전
        """
        # 기본 템플릿
        default_templates = {
            'hook': {
                'question': "{}?",
                'warning': "주의하세요! {}",
                'shocking': "충격! {}",
                'interesting': "놀라운 사실! {}"
            },
            'transition': [
                "자세히 알아보겠습니다.",
                "지금 바로 알려드립니다.",
                "함께 살펴보겠습니다.",
                "이것이 전체 내용입니다."
            ],
            'ending': [
                "이상 글로벌 뉴스 단신이었습니다.",
                "더 자세한 내용은 링크를 참고하세요.",
                "구독과 좋아요 부탁드립니다.",
                "다음 소식에서 다시 만나요."
            ]
        }
        
        # 템플릿 파일 경로
        template_file = os.path.join(DATA_DIR, 'templates.json')
        
        # 템플릿 파일이 있으면 로드
        if os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                logger.info("템플릿 파일 로드 성공")
                return templates
            except Exception as e:
                logger.error(f"템플릿 파일 로드 실패: {e}")
                return default_templates
        else:
            # 템플릿 파일이 없으면 기본 템플릿 저장
            try:
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(default_templates, f, ensure_ascii=False, indent=2)
                logger.info("기본 템플릿 파일 생성 완료")
                return default_templates
            except Exception as e:
                logger.error(f"기본 템플릿 파일 생성 실패: {e}")
                return default_templates
    
    def save_templates(self, templates):
        """
        스크립트 템플릿 저장
        
        Args:
            templates (dict): 템플릿 사전
        """
        template_file = os.path.join(DATA_DIR, 'templates.json')
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            logger.info("템플릿 파일 저장 완료")
            self.templates = templates
        except Exception as e:
            logger.error(f"템플릿 파일 저장 실패: {e}")
    
    def enhance_hook(self, hook_text, style='question'):
        """
        Hook 멘트 강화
        
        Args:
            hook_text (str): 기본 Hook 멘트
            style (str): Hook 스타일 (question, warning, shocking, interesting)
            
        Returns:
            str: 강화된 Hook 멘트
        """
        try:
            # 템플릿에서 스타일 가져오기
            template = self.templates['hook'].get(style, self.templates['hook']['question'])
            
            # Hook 멘트가 이미 해당 스타일이면 그대로 반환
            if hook_text.endswith('?') and style == 'question':
                return hook_text
            if hook_text.startswith('주의') and style == 'warning':
                return hook_text
            if hook_text.startswith('충격') and style == 'shocking':
                return hook_text
            if hook_text.startswith('놀라운') and style == 'interesting':
                return hook_text
            
            # Hook 멘트 강화
            # 문장 부호 제거
            clean_text = hook_text.rstrip('.!?')
            
            # 템플릿 적용
            enhanced_hook = template.format(clean_text)
            
            return enhanced_hook
        except Exception as e:
            logger.error(f"Hook 멘트 강화 실패: {e}")
            return hook_text
    
    def generate_script(self, video_data, transcript_data):
        """
        스크립트 생성
        
        Args:
            video_data (dict): 영상 정보
            transcript_data (dict): 자막 정보
            
        Returns:
            dict: 생성된 스크립트
        """
        try:
            # 영상 정보 추출
            video_id = video_data['id']
            video_title = video_data['snippet']['title']
            channel_title = video_data['snippet']['channelTitle']
            
            # 자막 정보 추출
            summary = transcript_data['summary']
            hook = summary['hook']
            summary_text = summary['summary']
            background = summary['background']
            
            # Hook 멘트 강화 (랜덤 스타일 또는 피드백 기반 선택)
            import random
            hook_styles = list(self.templates['hook'].keys())
            selected_style = random.choice(hook_styles)
            enhanced_hook = self.enhance_hook(hook, style=selected_style)
            
            # 전환 문구 선택
            transition = random.choice(self.templates['transition'])
            
            # 마무리 문구 선택
            ending = random.choice(self.templates['ending'])
            
            # 스크립트 구성
            script = {
                'video_id': video_id,
                'title': video_title,
                'channel': channel_title,
                'hook': enhanced_hook,
                'transition': transition,
                'summary': summary_text,
                'background': background,
                'ending': ending,
                'created_at': datetime.now().isoformat()
            }
            
            # 스크립트 저장
            script_file = os.path.join(DATA_DIR, 'scripts', f"{video_id}.json")
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            logger.info(f"스크립트 생성 완료: {video_id}")
            return script
        except Exception as e:
            logger.error(f"스크립트 생성 실패: {e}")
            return None
    
    def optimize_script_for_shorts(self, script, target_duration=SHORTS_DURATION):
        """
        쇼츠용 스크립트 최적화
        
        Args:
            script (dict): 스크립트
            target_duration (int): 목표 영상 길이 (초)
            
        Returns:
            dict: 최적화된 스크립트
        """
        try:
            # 평균 말하기 속도 (초당 글자 수)
            chars_per_second = 4
            
            # 현재 스크립트 길이 계산
            hook_length = len(script['hook']) / chars_per_second
            summary_length = len(script['summary']) / chars_per_second
            background_length = len(script['background']) / chars_per_second
            transition_length = len(script['transition']) / chars_per_second
            ending_length = len(script['ending']) / chars_per_second
            
            total_length = hook_length + summary_length + background_length + transition_length + ending_length
            
            # 길이가 적절하면 그대로 반환
            if total_length <= target_duration:
                return script
            
            # 길이가 너무 길면 최적화
            logger.info(f"스크립트 길이 최적화 필요: {total_length}초 -> {target_duration}초")
            
            # OpenAI API를 사용하여 요약 최적화
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert editor for short-form video content."},
                    {"role": "user", "content": f"""
                    다음 쇼츠 영상 스크립트를 {target_duration}초 이내로 최적화해주세요.
                    현재 예상 길이는 약 {total_length:.1f}초입니다.
                    
                    1. Hook 멘트는 최대한 유지하되 간결하게 만들어주세요.
                    2. 핵심 요약은 가장 중요한 내용만 남기고 축약해주세요.
                    3. 배경 설명은 필요시 축약하거나 생략할 수 있습니다.
                    4. 전환 문구와 마무리 문구는 더 짧은 것으로 대체할 수 있습니다.
                    
                    원본 스크립트:
                    - Hook: {script['hook']}
                    - 전환: {script['transition']}
                    - 요약: {script['summary']}
                    - 배경: {script['background']}
                    - 마무리: {script['ending']}
                    
                    JSON 형식으로 다음과 같이 반환해주세요:
                    {{
                        "hook": "최적화된 Hook 멘트",
                        "transition": "최적화된 전환 문구",
                        "summary": "최적화된 요약",
                        "background": "최적화된 배경 설명",
                        "ending": "최적화된 마무리 문구"
                    }}
                    """
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            optimized_content = json.loads(response.choices[0].message.content)
            
            # 최적화된 내용으로 스크립트 업데이트
            script.update(optimized_content)
            
            # 최적화된 스크립트 저장
            script_file = os.path.join(DATA_DIR, 'scripts', f"{script['video_id']}_optimized.json")
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            logger.info(f"스크립트 최적화 완료: {script['video_id']}")
            return script
        except Exception as e:
            logger.error(f"스크립트 최적화 실패: {e}")
            return script
    
    def generate_title_and_tags(self, script):
        """
        제목 및 태그 생성
        
        Args:
            script (dict): 스크립트
            
        Returns:
            dict: 제목 및 태그
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in creating engaging titles and tags for YouTube Shorts."},
                    {"role": "user", "content": f"""
                    다음 쇼츠 영상 스크립트를 바탕으로 매력적인 제목과 해시태그를 생성해주세요.
                    
                    스크립트:
                    - Hook: {script['hook']}
                    - 요약: {script['summary']}
                    - 배경: {script['background']}
                    
                    원본 영상 제목: {script['title']}
                    
                    다음 조건을 만족하는 결과를 JSON 형식으로 반환해주세요:
                    1. 제목은 30자 이내로 짧고 강렬하게 작성
                    2. 해시태그는 5-7개 정도로 관련성 높은 것만 선택
                    3. 제목에는 이모지를 1-2개 포함
                    
                    {{
                        "title": "생성된 제목",
                        "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"]
                    }}
                    """
                    }
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 결과 저장
            script['youtube_title'] = result['title']
            script['youtube_tags'] = result['tags']
            
            # 업데이트된 스크립트 저장
            script_file = os.path.join(DATA_DIR, 'scripts', f"{script['video_id']}_final.json")
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            logger.info(f"제목 및 태그 생성 완료: {script['video_id']}")
            return result
        except Exception as e:
            logger.error(f"제목 및 태그 생성 실패: {e}")
            return {"title": script['title'], "tags": ["글로벌뉴스", "해외소식", "뉴스요약"]}

# 테스트 코드
if __name__ == "__main__":
    generator = ContentGenerator()
    
    # 테스트용 데이터
    video_data = {
        "id": "test_video_id",
        "snippet": {
            "title": "Breaking News: Major Economic Announcement",
            "channelTitle": "CNN News"
        }
    }
    
    transcript_data = {
        "summary": {
            "hook": "세계 경제가 큰 위기에 직면했습니다",
            "summary": "미국 연방준비제도이사회가 기준금리를 0.5% 인상했습니다. 이는 지난 20년간 가장 큰 폭의 인상입니다. 전문가들은 인플레이션 억제를 위한 조치라고 분석합니다.",
            "background": "미국의 금리 인상은 전 세계 경제에 큰 영향을 미칠 것으로 예상됩니다."
        }
    }
    
    # 스크립트 생성
    script = generator.generate_script(video_data, transcript_data)
    
    if script:
        # 스크립트 최적화
        optimized_script = generator.optimize_script_for_shorts(script)
        
        # 제목 및 태그 생성
        title_and_tags = generator.generate_title_and_tags(optimized_script)
        
        print("생성된 스크립트:")
        print(f"제목: {title_and_tags['title']}")
        print(f"Hook: {optimized_script['hook']}")
        print(f"요약: {optimized_script['summary']}")
        print(f"배경: {optimized_script['background']}")
        print(f"태그: {', '.join(title_and_tags['tags'])}")
    else:
        print("스크립트 생성 실패")
